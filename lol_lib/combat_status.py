# -*- coding: utf-8 -*-
"""
Monitor de Estado de Combate, Vida Crítica, Habilidades e Canalização de Recall.
Fornece alertas sonoros vitais durante a partida de League of Legends:
1. Batimento cardíaco para vida crítica (< 30%).
2. Alarme e interrupção sonora de Recall (retorno à base / tecla B) se sofrer dano.
3. Notificação sonora imediata de Ultimate pronto.
4. Resumo detalhado de recarga e níveis das habilidades.
"""

import time

try:
    from logHandler import log
except Exception:
    import logging
    log = logging.getLogger("lol_combat_status")

try:
    from lol_lib.spatial_audio import get_spatial_audio_player, generate_pcm_stereo_tone
except Exception:
    try:
        from spatial_audio import get_spatial_audio_player, generate_pcm_stereo_tone
    except Exception:
        get_spatial_audio_player = lambda: None
        generate_pcm_stereo_tone = lambda *a, **kw: b""


class LoLCombatStatus:
    """
    Rastreia a saúde do jogador, prontidão de habilidades e canalizações em andamento.
    """

    def __init__(self):
        self.last_hp_pct = 1.0
        self.last_heartbeat_time = 0.0
        self.last_ultimate_ready = True
        self.last_ability_levels = {}
        
        # Estado do Retorno à Base (Recall / tecla B)
        self.is_recalling = False
        self.recall_start_time = 0.0
        self.recall_duration = 8.0
        self.health_at_recall_start = 0.0
        self.last_recall_pulse_sec = -1

    def update_player_health(self, cur_hp, max_hp):
        """
        Monitora a vida do jogador. Se estiver abaixo de 30%, emite
        pulso sonoro grave de batimento cardíaco (tum-tum).
        """
        if max_hp <= 0:
            return None

        hp_pct = cur_hp / float(max_hp)
        self.last_hp_pct = hp_pct
        now = time.time()

        # Alerta de batimento cardíaco para vida crítica (< 30%)
        if hp_pct < 0.30 and cur_hp > 0:
            interval = 0.85 if hp_pct < 0.15 else 1.35
            if now - self.last_heartbeat_time >= interval:
                self.last_heartbeat_time = now
                player = get_spatial_audio_player()
                if player:
                    # Som grave de batimento cardíaco duplo
                    player.play_spatial_tone(180, 50, 0.0, volume=0.85)
                    player.play_spatial_tone(140, 70, 0.0, volume=0.75)
                return "CRITICAL_HP"

        return None

    def start_recall(self, current_health, duration=8.0):
        """Inicia o acompanhamento da canalização de retorno à base (tecla B)."""
        self.is_recalling = True
        self.recall_start_time = time.time()
        self.recall_duration = duration
        self.health_at_recall_start = current_health
        self.last_recall_pulse_sec = 0

        player = get_spatial_audio_player()
        if player:
            # Som inicial de canalização (sweep ascendente suave)
            player.play_spatial_tone(520, 100, 0.0, volume=0.5)

        return "Iniciando retorno à base (8 segundos)..."

    def cancel_recall(self):
        """Cancela manualmente a canalização de retorno."""
        self.is_recalling = False
        self.last_recall_pulse_sec = -1

    def update_recall(self, current_health):
        """
        Verifica se a canalização de retorno continua ativa, se foi interrompida
        por dano inimigo ou se foi completada com sucesso.
        """
        if not self.is_recalling:
            return None, ""

        now = time.time()
        elapsed = now - self.recall_start_time

        # 1. Detecção de Dano / Interrupção (vida caiu mais de 3 HP)
        if current_health < (self.health_at_recall_start - 3.0):
            self.is_recalling = False
            self.last_recall_pulse_sec = -1
            player = get_spatial_audio_player()
            if player:
                # Alarme estridente de quebra de canalização
                player.play_proximity_alarm(0.0, distance_ratio=0.05, count=3)
            return "INTERRUPTED", "Retorno interrompido! Você sofreu dano!"

        # 2. Conclusão do retorno (8 segundos)
        if elapsed >= self.recall_duration:
            self.is_recalling = False
            self.last_recall_pulse_sec = -1
            player = get_spatial_audio_player()
            if player:
                # Acorde harmônico de chegada na base
                player.play_clean_radar()
            return "SUCCESS", "Chegou na base!"

        # 3. Pulso sonoro de contagem de canalização a cada segundo
        sec = int(elapsed)
        if sec > self.last_recall_pulse_sec and sec < int(self.recall_duration):
            self.last_recall_pulse_sec = sec
            player = get_spatial_audio_player()
            if player:
                freq = 440 + (sec * 50)
                player.play_spatial_tone(freq, 40, 0.0, volume=0.35)
            return "PROGRESS", f"{int(self.recall_duration - sec)}"

        return None, ""

    def update_abilities_cooldowns(self, abilities_dict):
        """
        Rastreia as habilidades e detecta quando o Ultimate (R) sai de recarga.
        Retorna (event_type, announcement_text).
        """
        if not abilities_dict or not isinstance(abilities_dict, dict):
            return None, ""

        r_data = abilities_dict.get("R", {})
        r_level = r_data.get("abilityLevel", 0)
        r_cd = float(r_data.get("cooldown", 0.0) or 0.0)

        r_ready = (r_level > 0 and r_cd <= 0.05)
        event = None
        msg = ""

        # Transição: Ultimate estava em recarga e agora ficou pronto!
        if not self.last_ultimate_ready and r_ready:
            player = get_spatial_audio_player()
            if player:
                # Efeito sonoro triunfante de Ultimate pronto
                player.play_spatial_tone(659, 80, -0.2, volume=0.6)
                player.play_spatial_tone(880, 80, 0.0, volume=0.7)
                player.play_spatial_tone(1175, 140, 0.2, volume=0.8)
            event = "ULTIMATE_READY"
            r_name = r_data.get("displayName") or "Ultimate"
            msg = f"Ultimate pronto ({r_name})!"

        self.last_ultimate_ready = r_ready
        return event, msg

    def get_abilities_summary(self, abilities_dict):
        """Formata resumo falado completo dos tempos de recarga e níveis das habilidades."""
        if not abilities_dict or not isinstance(abilities_dict, dict):
            return "Informações de habilidades indisponíveis no momento."

        order = ["Passive", "Q", "W", "E", "R"]
        parts = []

        for key in ["Q", "W", "E", "R"]:
            data = abilities_dict.get(key, {})
            name = data.get("displayName", key)
            level = data.get("abilityLevel", 0)
            cd = float(data.get("cooldown", 0.0) or 0.0)

            if level == 0:
                parts.append(f"{key}: Não aprendida")
            elif cd <= 0.1:
                parts.append(f"{key}: Pronto (Nível {level})")
            else:
                cd_int = int(round(cd))
                parts.append(f"{key}: {cd_int}s de recarga (Nível {level})")

        return "Habilidades: " + "; ".join(parts) + "."
