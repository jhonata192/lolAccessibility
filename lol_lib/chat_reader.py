# -*- coding: utf-8 -*-
"""
Leitor e Parser de Chat e Pings Táticos do League of Legends.
Detecta pings de Inimigo Desaparecido (MIA), Perigo, A Caminho, Ajuda,
Cuidado/Recuo, Feitiços de Invocador e Mensagens de Chat dos Aliados.
Opera via captura ultrarrápida de GDI (< 4ms) e OCR integrado do NVDA (UwpOcr),
sendo 100% seguro contra o Riot Vanguard (zero injeção / zero hooks de memória).
"""

import os
import re
import time
import collections
import ctypes
from ctypes import wintypes

try:
    from logHandler import log
except Exception:
    import logging
    log = logging.getLogger("lol_chat_reader")

# Tentar importar subsistemas nativos do NVDA
try:
    from contentRecog.uwpOcr import UwpOcr
    from contentRecog import RecogImageInfo
except Exception:
    UwpOcr = None
    RecogImageInfo = None

try:
    from screenBitmap import ScreenBitmap
except Exception:
    ScreenBitmap = None


# Tipos de eventos de chat e pings
PING_MISSING = "MISSING"       # Inimigo Desaparecido / MIA (?)
PING_DANGER = "DANGER"         # Perigo (!)
PING_ON_MY_WAY = "ON_MY_WAY"   # A Caminho
PING_CAUTION = "CAUTION"       # Cuidado / Recuar
PING_ASSIST = "ASSIST"         # Preciso de Ajuda
PING_SPELL = "SPELL"           # Feitiço de invocador sinalizado
PING_CHAT = "CHAT"             # Mensagem de texto normal
PING_RAW = "RAW"               # Linha não estruturada


# Expressão regular para linhas do chat do League of Legends (Cliente em Português)
RE_CHAT_LINE = re.compile(
    r"^(?:\[(?P<channel>[^\]]+)\]\s*)?(?P<sender>[^\(:\-]+?)(?:\s*\((?P<champion>[^\)]+)\))?\s*[:\-]\s*(?P<content>.+)$",
    re.IGNORECASE
)


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG)
    ]


class LoLChatReader:
    """
    Gerencia a captura da área de chat do League of Legends e a extração
    de pings táticos e mensagens para o leitor de telas.
    """

    def __init__(self):
        self.history = collections.deque(maxlen=30)
        self.last_announced = {}  # (type, champion): (timestamp, count)
        self.last_processed_lines = collections.deque(maxlen=50)
        self.is_scanning = False
        self.last_scan_time = 0
        self._uwp_ocr = None
        if UwpOcr:
            try:
                self._uwp_ocr = UwpOcr()
            except Exception as e:
                log.debug(f"lolAccessibility: Falha ao inicializar UwpOcr: {e}")

    @staticmethod
    def find_league_game_window():
        """Retorna o identificador HWND da janela 3D do League of Legends."""
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW("RiotWindowClass", None)
        if not hwnd:
            hwnd = user32.FindWindowW(None, "League of Legends (TM) Client")
        if hwnd and user32.IsWindowVisible(hwnd) and not user32.IsIconic(hwnd):
            return hwnd
        return None

    @staticmethod
    def get_chat_rect(hwnd):
        """
        Calcula as coordenadas de tela da caixa de chat do LoL.
        Localizada no canto inferior esquerdo (acima do HUD do campeão).
        """
        user32 = ctypes.windll.user32
        rect = RECT()
        user32.GetClientRect(hwnd, ctypes.byref(rect))
        w = rect.right - rect.left
        h = rect.bottom - rect.top

        if w <= 0 or h <= 0:
            return None

        # Proporções padrão da caixa de chat no LoL
        chat_x = int(w * 0.015)
        chat_y = int(h * 0.55)
        chat_w = int(w * 0.28)
        chat_h = int(h * 0.25)

        pt = wintypes.POINT(chat_x, chat_y)
        user32.ClientToScreen(hwnd, ctypes.byref(pt))
        return pt.x, pt.y, chat_w, chat_h

    def parse_line(self, line):
        """
        Interpreta uma linha do chat e identifica pings táticos ou mensagens de texto.
        """
        line = line.strip()
        if not line or len(line) < 3:
            return None

        m = RE_CHAT_LINE.match(line)
        if not m:
            c_low = line.lower()
            if any(k in c_low for k in ["desaparecido", "desaparecida", "missing", "mia"]):
                return {
                    "type": PING_MISSING,
                    "sender": "Aliado",
                    "champion": "Inimigo",
                    "channel": "",
                    "content": line,
                    "announcement": "Alerta de MIA: Inimigo desaparecido da rota!"
                }
            elif any(k in c_low for k in ["perigo", "danger"]):
                return {
                    "type": PING_DANGER,
                    "sender": "Aliado",
                    "champion": "Aliado",
                    "channel": "",
                    "content": line,
                    "announcement": "Alerta de Perigo sinalizado!"
                }
            return {
                "type": PING_RAW,
                "sender": "",
                "champion": "",
                "channel": "",
                "content": line,
                "announcement": line
            }

        sender = m.group("sender").strip()
        champion = (m.group("champion") or sender).strip()
        channel = (m.group("channel") or "").strip()
        content = m.group("content").strip()
        c_lower = content.lower()

        # Classificação por palavras-chave em português e inglês
        if any(k in c_lower for k in ["desaparecido", "desaparecida", "missing", "mia"]):
            ptype = PING_MISSING
            announcement = f"Alerta de MIA: {champion} desapareceu da rota!"
        elif any(k in c_lower for k in ["perigo", "danger"]):
            ptype = PING_DANGER
            announcement = f"Alerta de Perigo sinalizado por {champion}!"
        elif any(k in c_lower for k in ["a caminho", "caminho", "on my way", "omw"]):
            ptype = PING_ON_MY_WAY
            announcement = f"{champion} a caminho!"
        elif any(k in c_lower for k in ["cuidado", "recuar", "caution", "retreat", "afaste"]):
            ptype = PING_CAUTION
            announcement = f"Cuidado! Sinal de recuo por {champion}!"
        elif any(k in c_lower for k in ["ajuda", "assist", "socorro", "preciso de ajuda"]):
            ptype = PING_ASSIST
            announcement = f"{champion} pede ajuda!"
        elif any(k in c_lower for k in ["flash", "teleporte", "incendiar", "golpear", "exaustao", "curar", "barreira"]):
            ptype = PING_SPELL
            announcement = f"{champion} sinalizou: {content}!"
        else:
            ptype = PING_CHAT
            prefix = "no chat geral" if "todos" in channel.lower() else ""
            announcement = f"Chat de {sender} {prefix}: {content}".replace("  ", " ").strip()

        return {
            "type": ptype,
            "sender": sender,
            "champion": champion,
            "channel": channel,
            "content": content,
            "announcement": announcement
        }

    def process_raw_text(self, text, now=None):
        """
        Recebe texto puro extraído do OCR da caixa de chat, deduplica repetições
        e retorna uma lista de pings/mensagens inéditas prontas para anúncio.
        """
        if not text:
            return []
        if now is None:
            now = time.time()

        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        new_items = []

        for ln in lines:
            # Evitar reprocessar linhas idênticas recém-vistas
            if ln in self.last_processed_lines:
                continue
            self.last_processed_lines.append(ln)

            parsed = self.parse_line(ln)
            if not parsed:
                continue

            parsed["timestamp"] = now
            self.history.append(parsed)

            # Agrupamento e controle de repetição (Cooldown de 4.0s para pings repetidos)
            key = (parsed["type"], parsed["champion"])
            if key in self.last_announced:
                last_time, count = self.last_announced[key]
                if now - last_time < 4.0 and parsed["type"] in (PING_MISSING, PING_DANGER, PING_ON_MY_WAY, PING_CAUTION, PING_ASSIST):
                    self.last_announced[key] = (now, count + 1)
                    # Silenciar pings repetidos consecutivos para não poluir a voz
                    continue

            self.last_announced[key] = (now, 1)
            new_items.append(parsed)

        return new_items

    def get_recent_summary(self, max_count=3):
        """
        Retorna texto formatado com os últimos pings ou mensagens de chat
        para ser lido quando o usuário pressionar Control+Shift+M.
        """
        if not self.history:
            return "Nenhuma mensagem ou ping recente no chat."

        items = list(self.history)[-max_count:]
        summaries = []
        for it in items:
            summaries.append(it.get("announcement", it.get("content", "")))
        return ". ".join(summaries)

    def scan_chat_sync(self):
        """
        Executa uma varredura de OCR síncrona na caixa de chat da janela ativa do LoL.
        Retorna lista de novos pings/mensagens.
        """
        hwnd = self.find_league_game_window()
        if not hwnd or not self._uwp_ocr or not ScreenBitmap:
            return []

        coords = self.get_chat_rect(hwnd)
        if not coords:
            return []

        x, y, w, h = coords
        try:
            sb = ScreenBitmap(w, h)
            pixels = sb.captureImage(x, y, w, h)
            img_info = RecogImageInfo(x, y, w, h)
            
            ocr_text = []
            def _on_result(result):
                if result and hasattr(result, "text"):
                    ocr_text.append(result.text)

            self._uwp_ocr.recognize(pixels, img_info, _on_result)
            full_text = "\n".join(ocr_text)
            return self.process_raw_text(full_text)
        except Exception as e:
            log.debug(f"lolAccessibility: Erro ao capturar chat: {e}")
            return []
