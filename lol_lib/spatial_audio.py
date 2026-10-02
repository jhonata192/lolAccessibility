# -*- coding: utf-8 -*-
"""
Motor de Áudio Espacial 3D (Binaural Stereo Panning e Proximidade Sonora)
para League of Legends e NVDA.

Permite que jogadores com deficiência visual percebam a direção e distância
de inimigos, aliados e objetivos no mapa através de áudio estéreo em tempo real.
Utiliza síntese PCM de 16 bits nativa do Windows (winsound / wave / math)
com lei de panning de potência constante (constant-power panning law),
garantindo zero dependências externas e 100% de compatibilidade e segurança.
"""

import math
import struct
import io
import wave
import winsound
import threading
import queue
import time

try:
    from logHandler import log
except Exception:
    import logging
    log = logging.getLogger("lol_spatial_audio")

SAMPLE_RATE = 22050


def generate_pcm_stereo_tone(frequency, duration_ms, pan=0.0, volume=0.55, waveform="sine"):
    """
    Gera bytes de um arquivo WAV estéreo de 16 bits com panning direcional
    usando a lei de potência constante:
      theta = (pan + 1.0) * pi / 4.0
      left_gain = cos(theta) * volume
      right_gain = sin(theta) * volume
    
    pan: float entre -1.0 (100% ouvido esquerdo) e +1.0 (100% ouvido direito).
    """
    pan = max(-1.0, min(1.0, float(pan)))
    volume = max(0.0, min(1.0, float(volume)))
    frequency = max(100.0, min(4000.0, float(frequency)))
    duration_ms = max(20, min(2000, int(duration_ms)))

    theta = (pan + 1.0) * (math.pi / 4.0)
    left_gain = math.cos(theta) * volume
    right_gain = math.sin(theta) * volume

    n_samples = int(SAMPLE_RATE * (duration_ms / 1000.0))
    ramp = min(120, max(10, n_samples // 6))

    frames = bytearray(n_samples * 4)

    for i in range(n_samples):
        # Envelopamento linear para evitar estalos de corte DC
        env = 1.0
        if i < ramp:
            env = i / float(ramp)
        elif i > (n_samples - ramp):
            env = (n_samples - i) / float(ramp)

        t = i / float(SAMPLE_RATE)

        if waveform == "sawtooth":
            # Som mais brilhante e cortante para perigo e alertas
            phase = (t * frequency) % 1.0
            sample_val = (2.0 * phase - 1.0) * 0.85
        elif waveform == "pulse":
            # Pulso sonoro quadrado suave
            phase = (t * frequency) % 1.0
            sample_val = 0.7 if phase < 0.5 else -0.7
        else:
            # Onda senoidal clássica suave
            sample_val = math.sin(2.0 * math.pi * frequency * t)

        final_sample = sample_val * 32767.0 * env
        left_val = int(max(-32767, min(32767, final_sample * left_gain)))
        right_val = int(max(-32767, min(32767, final_sample * right_gain)))

        struct.pack_into("<hh", frames, i * 4, left_val, right_val)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(frames)

    return buf.getvalue()


def generate_sweep_tone(start_freq, end_freq, duration_ms, pan=0.0, volume=0.45):
    """Gera um sweep de frequência (chirp) estéreo suave para abertura de radar."""
    pan = max(-1.0, min(1.0, float(pan)))
    theta = (pan + 1.0) * (math.pi / 4.0)
    left_gain = math.cos(theta) * volume
    right_gain = math.sin(theta) * volume

    n_samples = int(SAMPLE_RATE * (duration_ms / 1000.0))
    ramp = min(100, n_samples // 6)
    frames = bytearray(n_samples * 4)

    cur_phase = 0.0
    for i in range(n_samples):
        progress = i / float(n_samples)
        freq = start_freq + (end_freq - start_freq) * progress
        cur_phase += (2.0 * math.pi * freq) / SAMPLE_RATE

        env = 1.0
        if i < ramp:
            env = i / float(ramp)
        elif i > (n_samples - ramp):
            env = (n_samples - i) / float(ramp)

        sample_val = math.sin(cur_phase) * 32767.0 * env
        left_val = int(max(-32767, min(32767, sample_val * left_gain)))
        right_val = int(max(-32767, min(32767, sample_val * right_gain)))

        struct.pack_into("<hh", frames, i * 4, left_val, right_val)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(frames)

    return buf.getvalue()


def generate_clean_radar_chord(duration_ms=250, volume=0.4):
    """Gera um acorde calmo e harmônico (Dó Maior / 523Hz + 659Hz) indicando mapa limpo."""
    n_samples = int(SAMPLE_RATE * (duration_ms / 1000.0))
    ramp = min(150, n_samples // 5)
    frames = bytearray(n_samples * 4)

    for i in range(n_samples):
        t = i / float(SAMPLE_RATE)
        env = 1.0
        if i < ramp:
            env = i / float(ramp)
        elif i > (n_samples - ramp):
            env = (n_samples - i) / float(ramp)

        s1 = math.sin(2.0 * math.pi * 523.25 * t)
        s2 = math.sin(2.0 * math.pi * 659.25 * t)
        sample_val = ((s1 + s2) / 2.0) * 32767.0 * volume * env

        val = int(max(-32767, min(32767, sample_val)))
        struct.pack_into("<hh", frames, i * 4, val, val)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(frames)

    return buf.getvalue()


class SpatialAudioPlayer:
    """
    Controlador de reprodução assíncrona não bloqueante de áudio espacial.
    Executa em uma thread em segundo plano com fila prioritária.
    """

    def __init__(self):
        self._queue = queue.Queue(maxsize=32)
        self._running = True
        self._thread = threading.Thread(target=self._worker, name="LoLSpatialAudioWorker", daemon=True)
        self._thread.start()

    def _worker(self):
        while self._running:
            try:
                item = self._queue.get(timeout=0.3)
            except queue.Empty:
                continue

            if not self._running:
                break

            action, args = item
            try:
                if action == "play_wav":
                    wav_bytes = args
                    winsound.PlaySound(wav_bytes, winsound.SND_MEMORY)
                elif action == "play_sequence":
                    seq = args
                    for wav_bytes, delay_after in seq:
                        if not self._running:
                            break
                        winsound.PlaySound(wav_bytes, winsound.SND_MEMORY)
                        if delay_after > 0:
                            time.sleep(delay_after)
            except Exception as e:
                log.debug(f"lolAccessibility: Erro na reprodução de áudio espacial: {e}")
            finally:
                self._queue.task_done()

    def play_spatial_tone(self, freq, duration_ms, pan, vol=0.55, waveform="sine", volume=None):
        """Enfileira um bip estéreo espacial para reprodução instantânea."""
        if not self._running:
            return
        if volume is not None:
            vol = volume
        try:
            wav_bytes = generate_pcm_stereo_tone(freq, duration_ms, pan, vol, waveform)
            self._queue.put_nowait(("play_wav", wav_bytes))
        except queue.Full:
            pass
        except Exception as e:
            log.debug(f"lolAccessibility: Falha ao enfileirar tom espacial: {e}")

    def play_sweep_intro(self):
        """Toca o efeito sonoro de inicialização da varredura de radar."""
        if not self._running:
            return
        try:
            wav_bytes = generate_sweep_tone(450, 950, 100, 0.0, 0.45)
            self._queue.put_nowait(("play_wav", wav_bytes))
        except Exception:
            pass

    def play_clean_radar(self):
        """Toca acorde suave indicando nenhum perigo ou inimigo próximo."""
        if not self._running:
            return
        try:
            wav_bytes = generate_clean_radar_chord(220, 0.4)
            self._queue.put_nowait(("play_wav", wav_bytes))
        except Exception:
            pass

    def play_proximity_alarm(self, pan, distance_ratio=0.1, count=2):
        """
        Emite um alarme direcional rápido de emboscada / perigo (bip-bip)
        no canal estéreo da aproximação do inimigo.
        """
        if not self._running:
            return
        # Quanto mais próximo (menor distance_ratio), maior a frequência
        freq = 1350.0 if distance_ratio < 0.10 else (1150.0 if distance_ratio < 0.20 else 900.0)
        dur = 65
        gap = 0.045
        seq = []
        for _ in range(count):
            wb = generate_pcm_stereo_tone(freq, dur, pan, volume=0.75, waveform="sawtooth")
            seq.append((wb, gap))
        try:
            self._queue.put_nowait(("play_sequence", seq))
        except Exception:
            pass

    def play_radar_sweep(self, targets):
        """
        Executa uma varredura acústica sequencial completa dos alvos detectados.
        Ordena os alvos da esquerda para a direita (pan -1.0 a +1.0) e emite
        pulsos com variação de frequência de acordo com a distância.
        """
        if not self._running:
            return
        if not targets:
            self.play_clean_radar()
            return

        # Ordenar por pan (da esquerda para a direita)
        sorted_targets = sorted(targets, key=lambda t: t.get("pan", 0.0))
        seq = []

        # Som de abertura
        intro_wav = generate_sweep_tone(400, 900, 80, 0.0, 0.4)
        seq.append((intro_wav, 0.08))

        for tgt in sorted_targets:
            pan = tgt.get("pan", 0.0)
            freq = tgt.get("freq", 800)
            team = tgt.get("team", "enemy")
            waveform = "sawtooth" if team == "enemy" else "sine"
            vol = 0.70 if team == "enemy" else 0.50
            dur = 75 if team == "enemy" else 65

            wb = generate_pcm_stereo_tone(freq, dur, pan, volume=vol, waveform=waveform)
            seq.append((wb, 0.09))

        try:
            self._queue.put_nowait(("play_sequence", seq))
        except Exception:
            pass

    def stop(self):
        """Para a thread de áudio e limpa a fila."""
        self._running = False
        try:
            self._queue.put_nowait(("stop", None))
        except Exception:
            pass


_global_spatial_player = None

def get_spatial_audio_player():
    """Retorna a instância singleton do SpatialAudioPlayer."""
    global _global_spatial_player
    if _global_spatial_player is None:
        _global_spatial_player = SpatialAudioPlayer()
    return _global_spatial_player
