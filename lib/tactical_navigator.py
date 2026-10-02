# -*- coding: utf-8 -*-
"""
Navegador Tático e Assistente de Movimentação no Minimapa para League of Legends.

Permite que jogadores com deficiência visual se movimentem com autonomia pelas rotas
de Summoner's Rift usando comandos de teclado (Alt+1, Alt+2, Alt+3, Alt+4, Control+Shift+N).
Aproveita o sistema nativo de pathfinding automático do League of Legends através de cliques
programáticos precisos com o botão direito nas coordenadas táticas do minimapa.

Totalmente seguro e compatível com o Riot Vanguard (zero injeção de DLL, zero leitura de memória).
"""

import time
import os
import ctypes
from ctypes import wintypes

try:
    from logHandler import log
except ImportError:
    import logging
    log = logging.getLogger("lolAccessibility")

from lol_lib.riot_api_helper import (
    get_live_allgamedata, get_live_active_player, get_live_player_list, is_live_game_active
)
from lol_lib.minimap_scanner import LoLMinimapScanner
from lol_lib.spatial_audio import get_spatial_audio_player


MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
VK_SPACE = 0x20
KEYEVENTF_KEYUP = 0x0002

# Coordenadas táticas normalizadas (0.0 a 1.0) no Minimapa de Summoner's Rift
# (0, 0) = Canto Superior Esquerdo | (1, 1) = Canto Inferior Direito
WAYPOINTS = {
    # Blue Side (ORDER)
    "ORDER_BASE": {"name": "Base Aliada (Fonte)", "nx": 0.08, "ny": 0.92, "category": "Base"},
    "ORDER_TOP_T1": {"name": "Torre do Topo (T1 Aliada)", "nx": 0.12, "ny": 0.55, "category": "Topo"},
    "ORDER_TOP_CENTER": {"name": "Rota do Topo (Centro)", "nx": 0.18, "ny": 0.22, "category": "Topo"},
    "ORDER_MID_T1": {"name": "Torre do Meio (T1 Aliada)", "nx": 0.36, "ny": 0.64, "category": "Meio"},
    "ORDER_MID_CENTER": {"name": "Rota do Meio (Centro)", "nx": 0.50, "ny": 0.50, "category": "Meio"},
    "ORDER_BOT_T1": {"name": "Torre da Rota Inferior (T1 Aliada)", "nx": 0.55, "ny": 0.88, "category": "Inferior"},
    "ORDER_BOT_CENTER": {"name": "Rota Inferior (Centro)", "nx": 0.82, "ny": 0.82, "category": "Inferior"},

    # Red Side (CHAOS)
    "CHAOS_BASE": {"name": "Base Aliada (Fonte)", "nx": 0.92, "ny": 0.08, "category": "Base"},
    "CHAOS_TOP_T1": {"name": "Torre do Topo (T1 Aliada)", "nx": 0.45, "ny": 0.12, "category": "Topo"},
    "CHAOS_TOP_CENTER": {"name": "Rota do Topo (Centro)", "nx": 0.18, "ny": 0.22, "category": "Topo"},
    "CHAOS_MID_T1": {"name": "Torre do Meio (T1 Aliada)", "nx": 0.64, "ny": 0.36, "category": "Meio"},
    "CHAOS_MID_CENTER": {"name": "Rota do Meio (Centro)", "nx": 0.50, "ny": 0.50, "category": "Meio"},
    "CHAOS_BOT_T1": {"name": "Torre da Rota Inferior (T1 Aliada)", "nx": 0.88, "ny": 0.45, "category": "Inferior"},
    "CHAOS_BOT_CENTER": {"name": "Rota Inferior (Centro)", "nx": 0.82, "ny": 0.82, "category": "Inferior"},

    # Neutros
    "DRAGON_PIT": {"name": "Covil do Dragão", "nx": 0.68, "ny": 0.68, "category": "Objetivos"},
    "BARON_PIT": {"name": "Covil do Barão", "nx": 0.32, "ny": 0.32, "category": "Objetivos"},
}


def force_restore_and_focus(hwnd):
    """Restaura a janela do DirectX/League mesmo se estiver minimizada para 1x1 e força o foco."""
    if not hwnd:
        return False
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    try:
        hDesk = user32.OpenInputDesktop(0, False, 0x01FF)
        if hDesk:
            user32.SetThreadDesktop(hDesk)
        fore_hwnd = user32.GetForegroundWindow()
        fore_tid = user32.GetWindowThreadProcessId(fore_hwnd, None)
        cur_tid = kernel32.GetCurrentThreadId()
        if fore_tid != cur_tid:
            user32.AttachThreadInput(cur_tid, fore_tid, True)
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.ShowWindow(hwnd, 5)  # SW_SHOW
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
        if fore_tid != cur_tid:
            user32.AttachThreadInput(cur_tid, fore_tid, False)
        return True
    except Exception:
        try:
            user32.ShowWindow(hwnd, 9)
            user32.SetForegroundWindow(hwnd)
        except Exception:
            pass
        return False


class TacticalNavigator:
    """Gerencia waypoints e executa cliques inteligentes de navegação no minimapa."""

    def __init__(self):
        self.scanner = LoLMinimapScanner()
        self.cached_team = None
        self.last_team_check_time = 0

    def get_player_team(self, live_data=None):
        """
        Retorna o time do jogador ('ORDER' ou 'CHAOS') consultando a Live API.
        Usa cache de 10 segundos.
        """
        now = time.time()
        if self.cached_team and (now - self.last_team_check_time) < 10.0:
            return self.cached_team

        if not live_data:
            live_data = get_live_allgamedata()

        if live_data and isinstance(live_data, dict):
            active = live_data.get("activePlayer", {})
            my_name = active.get("summonerName", "")
            players = live_data.get("allPlayers", [])

            for p in players:
                if p.get("summonerName") == my_name:
                    team = p.get("team", "ORDER")
                    self.cached_team = team
                    self.last_team_check_time = now
                    return team

            if players:
                team = players[0].get("team", "ORDER")
                self.cached_team = team
                self.last_team_check_time = now
                return team

        return self.cached_team or "ORDER"

    def resolve_waypoint(self, target_alias, team=None):
        """
        Resolve um apelido (ex: 'TOP', 'MID', 'BOT', 'BASE', 'DRAGON', 'BARON')
        para as coordenadas normalizadas e o nome do destino com base no time do jogador.
        """
        if not team:
            team = self.get_player_team()

        team_prefix = "CHAOS" if team == "CHAOS" else "ORDER"
        alias = target_alias.upper().strip()

        # Mapeamentos diretos
        mapping = {
            "TOP": f"{team_prefix}_TOP_CENTER",
            "TOP_T1": f"{team_prefix}_TOP_T1",
            "TOP_CENTER": f"{team_prefix}_TOP_CENTER",
            "MID": f"{team_prefix}_MID_CENTER",
            "MID_T1": f"{team_prefix}_MID_T1",
            "MID_CENTER": f"{team_prefix}_MID_CENTER",
            "BOT": f"{team_prefix}_BOT_CENTER",
            "BOT_T1": f"{team_prefix}_BOT_T1",
            "BOT_CENTER": f"{team_prefix}_BOT_CENTER",
            "BASE": f"{team_prefix}_BASE",
            "DRAGON": "DRAGON_PIT",
            "DRAGON_PIT": "DRAGON_PIT",
            "BARON": "BARON_PIT",
            "BARON_PIT": "BARON_PIT",
        }

        key = mapping.get(alias, alias)
        if key in WAYPOINTS:
            wp = dict(WAYPOINTS[key])
            wp["key"] = key
            return wp

        return None

    def calculate_screen_coordinates(self, nx, ny, minimap_rect):
        """
        Converte coordenadas normalizadas do minimapa (0.0 a 1.0) para coordenadas
        de pixels absolutos na tela do Windows.
        """
        if not minimap_rect:
            return None
        px = minimap_rect["x"] + int(nx * minimap_rect["width"])
        py = minimap_rect["y"] + int(ny * minimap_rect["height"])
        return px, py

    def navigate_to(self, target_alias, team=None):
        """
        Executa a navegação completa para o destino desejado:
        1. Resolve o waypoint com base no time.
        2. Obtém as dimensões e posição do minimapa na tela do LoL.
        3. Calcula as coordenadas absolutas de tela.
        4. Move o cursor e clica com botão direito.
        5. Emite feedback sonoro espacial e retorna mensagem descritiva.
        """
        wp = self.resolve_waypoint(target_alias, team=team)
        if not wp:
            return False, f"Destino de navegação '{target_alias}' desconhecido."

        hwnd = self.scanner.find_league_game_window()
        if not hwnd:
            return False, "Janela da partida do League of Legends não encontrada ou minimizada."

        force_restore_and_focus(hwnd)
        user32 = ctypes.windll.user32

        rect = self.scanner.get_minimap_rect(hwnd)
        if not rect:
            return False, "Minimapa não localizado na tela da partida."

        screen_coords = self.calculate_screen_coordinates(wp["nx"], wp["ny"], rect)
        if not screen_coords:
            return False, "Falha ao calcular coordenadas de tela para o minimapa."

        target_x, target_y = screen_coords

        # 1. Salvar posição atual do cursor
        old_pt = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(old_pt))

        try:
            # 2. Mover cursor para o destino no minimapa
            user32.SetCursorPos(target_x, target_y)
            time.sleep(0.015)

            # 3. Emitir clique com botão direito
            user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            time.sleep(0.035)
            user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
            time.sleep(0.015)

        finally:
            # 4. Restaurar posição do cursor
            user32.SetCursorPos(old_pt.x, old_pt.y)

        # 5. Emitir confirmação sonora estéreo direcional
        pan = (wp["nx"] - 0.5) * 2.0
        pan = max(-1.0, min(1.0, pan))
        player = get_spatial_audio_player()
        if player:
            # Dois tons ascendentes suaves indicando início de movimento naquela direção
            freq1 = 480 if wp["ny"] > 0.5 else 620
            freq2 = freq1 + 160
            player.play_spatial_tone(freq1, 50, pan, volume=0.5)
            player.play_spatial_tone(freq2, 70, pan, volume=0.6)

        return True, f"Movendo para {wp['name']}."

    def center_camera_and_cursor(self):
        """
        Centraliza a câmera na posição do campeão (Espaço) e posiciona
        o cursor exatamente no centro da janela do jogo.
        """
        hwnd = self.scanner.find_league_game_window()
        if not hwnd:
            return False, "Janela da partida do League of Legends não encontrada."

        user32 = ctypes.windll.user32
        force_restore_and_focus(hwnd)

        rect = wintypes.RECT()
        if not user32.GetClientRect(hwnd, ctypes.byref(rect)):
            return False, "Não foi possível obter dimensões da janela do jogo."

        pt = wintypes.POINT(rect.left, rect.top)
        user32.ClientToScreen(hwnd, ctypes.byref(pt))

        width = rect.right - rect.left
        height = rect.bottom - rect.top
        center_x = pt.x + (width // 2)
        center_y = pt.y + (height // 2)

        # Pressionar e soltar Espaço para recentralizar câmera
        user32.keybd_event(VK_SPACE, 0, 0, 0)
        time.sleep(0.02)
        user32.keybd_event(VK_SPACE, 0, KEYEVENTF_KEYUP, 0)

        # Posicionar cursor no centro exato da tela
        user32.SetCursorPos(center_x, center_y)

        player = get_spatial_audio_player()
        if player:
            player.play_spatial_tone(587, 80, 0.0, volume=0.55)

        return True, "Câmera e cursor centralizados no campeão."


_global_navigator = None

def get_tactical_navigator():
    global _global_navigator
    if _global_navigator is None:
        _global_navigator = TacticalNavigator()
    return _global_navigator
