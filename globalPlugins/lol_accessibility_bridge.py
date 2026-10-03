# -*- coding: utf-8 -*-
"""
Global Plugin - lolAccessibility Bridge
Responsável por:
1. Registrar os mapeamentos de executáveis da Riot para os AppModules correspondentes.
2. Monitorar em segundo plano eventos do League Client (LCU) (Ready Check / Champ Select).
3. Monitorar em tempo real a Live Client Data API (127.0.0.1:2999) durante a partida:
   - Alerta sonoro de vida baixa (Low HP warning beeps).
   - Anúncio de abates, dragões, barão, torres destruídas e ace.
   - Anúncio de subida de nível (Level Up).
4. Gerenciar atalhos universais (F6 para aceitar partida, Ctrl+Shift+F6 para auto-aceitar, etc.).
"""

import os
import sys
import threading
import time
import re
import globalPluginHandler
import appModuleHandler
import tones
import ui
import api
import controlTypes
from scriptHandler import script, getLastScriptRepeatCount
from logHandler import log

try:
    from speech import filter_speechSequence
except Exception:
    try:
        from speech.extensions import filter_speechSequence
    except Exception:
        filter_speechSequence = None

_addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_lol_lib_dir = os.path.join(_addon_dir, "lol_lib")
if _addon_dir not in sys.path:
    sys.path.insert(0, _addon_dir)
if _lol_lib_dir not in sys.path:
    sys.path.insert(0, _lol_lib_dir)

try:
    from lol_lib.riot_api_helper import (
        get_league_client_lockfile,
        get_riot_client_lockfile,
        get_lcu_gameflow_phase,
        get_lcu_ready_check,
        accept_lcu_match,
        get_lcu_champ_select_detailed,
        pick_or_ban_champion,
        get_lcu_aram_bench,
        swap_lcu_aram_bench,
        reroll_lcu_aram,
        import_recommended_runes_and_spells,
        set_lcu_lobby_positions,
        find_champion_by_name,
        get_lcu_all_champions,
        get_lcu_available_champions,
        get_riot_user_info,
        get_lcu_summoner_info,
        get_lcu_ranked_stats,
        get_lcu_lobby_info,
        get_lcu_search_state,
        start_lcu_matchmaking,
        cancel_lcu_matchmaking,
        get_lcu_queue_penalty,
        dismiss_lcu_notifications,
        create_lcu_lobby,
        is_live_game_active,
        get_live_active_player,
        get_live_active_player_abilities,
        get_live_player_list,
        get_live_event_data,
        get_live_game_stats,
        get_riot_install_status,
        get_live_enemy_lane_assignments,
        format_live_game_event,
        parse_turret_name,
        parse_inhib_name,
        format_scoreboard_summary,
        format_champion_stats_summary,
        format_objectives_summary,
        format_enemies_summary
    )
except Exception:
    try:
        from riot_api_helper import (
            get_league_client_lockfile,
            get_riot_client_lockfile,
            get_lcu_gameflow_phase,
            get_lcu_ready_check,
            accept_lcu_match,
            get_lcu_champ_select_detailed,
            pick_or_ban_champion,
            get_lcu_aram_bench,
            swap_lcu_aram_bench,
            reroll_lcu_aram,
            import_recommended_runes_and_spells,
            set_lcu_lobby_positions,
            find_champion_by_name,
            get_lcu_all_champions,
            get_lcu_available_champions,
            get_riot_user_info,
            get_lcu_summoner_info,
            get_lcu_ranked_stats,
            get_lcu_lobby_info,
            get_lcu_search_state,
            start_lcu_matchmaking,
            cancel_lcu_matchmaking,
            get_lcu_queue_penalty,
            dismiss_lcu_notifications,
            create_lcu_lobby,
            is_live_game_active,
            get_live_active_player,
            get_live_active_player_abilities,
            get_live_player_list,
            get_live_event_data,
            get_live_game_stats,
            get_riot_install_status,
            get_live_enemy_lane_assignments,
            format_live_game_event,
            parse_turret_name,
            parse_inhib_name,
            format_scoreboard_summary,
            format_champion_stats_summary,
            format_objectives_summary,
            format_enemies_summary
        )
    except Exception:
        try:
            from lib.riot_api_helper import (
                get_league_client_lockfile,
                get_riot_client_lockfile,
                get_lcu_gameflow_phase,
                get_lcu_ready_check,
                accept_lcu_match,
                get_lcu_champ_select_detailed,
                pick_or_ban_champion,
                get_lcu_aram_bench,
                swap_lcu_aram_bench,
                reroll_lcu_aram,
                import_recommended_runes_and_spells,
                set_lcu_lobby_positions,
                find_champion_by_name,
                get_lcu_all_champions,
                get_lcu_available_champions,
                get_riot_user_info,
                get_lcu_summoner_info,
                get_lcu_ranked_stats,
                get_lcu_lobby_info,
                get_lcu_search_state,
                start_lcu_matchmaking,
                cancel_lcu_matchmaking,
                get_lcu_queue_penalty,
                dismiss_lcu_notifications,
                create_lcu_lobby,
                is_live_game_active,
                get_live_active_player,
                get_live_active_player_abilities,
                get_live_player_list,
                get_live_event_data,
                get_live_game_stats,
                get_riot_install_status,
                get_live_enemy_lane_assignments,
                format_live_game_event,
                parse_turret_name,
                parse_inhib_name,
                format_scoreboard_summary,
                format_champion_stats_summary,
                format_objectives_summary,
                format_enemies_summary
            )
        except Exception as e:
            log.error(f"lolAccessibility: Falha ao importar riot_api_helper: {e}")
            get_league_client_lockfile = lambda: None
            get_riot_client_lockfile = lambda: None
            get_lcu_gameflow_phase = lambda: None
            get_lcu_ready_check = lambda: None
            accept_lcu_match = lambda: False
            get_lcu_champ_select_detailed = lambda: None
            pick_or_ban_champion = lambda c, b=False, l=True: (False, "Módulo indisponível", "")
            get_lcu_aram_bench = lambda: []
            swap_lcu_aram_bench = lambda c: (False, "Módulo indisponível")
            reroll_lcu_aram = lambda: (False, "Módulo indisponível", 0)
            import_recommended_runes_and_spells = lambda c=None, p=None: (False, "Módulo indisponível")
            set_lcu_lobby_positions = lambda p1, p2="UNSELECTED": (False, "Módulo indisponível")
            find_champion_by_name = lambda q: None
            get_lcu_all_champions = lambda: []
            get_lcu_available_champions = lambda is_ban=False: []
            get_riot_user_info = lambda: None
            get_lcu_summoner_info = lambda: None
            get_lcu_ranked_stats = lambda: "Sem classificação"
            get_lcu_lobby_info = lambda: None
            get_lcu_search_state = lambda: None
            start_lcu_matchmaking = lambda: False
            cancel_lcu_matchmaking = lambda: False
            get_lcu_queue_penalty = lambda: None
            dismiss_lcu_notifications = lambda: 0
            create_lcu_lobby = lambda q: False
            is_live_game_active = lambda: False
            get_live_active_player = lambda: None
            get_live_active_player_abilities = lambda: None
            get_live_player_list = lambda: None
            get_live_event_data = lambda: None
            get_live_game_stats = lambda: None
            get_riot_install_status = lambda: None
            get_live_enemy_lane_assignments = lambda: None
            format_live_game_event = lambda e, t=None: (None, "")
            parse_turret_name = lambda r: "Torre"
            parse_inhib_name = lambda r: "Inibidor"
            format_scoreboard_summary = lambda l=None: "Placar indisponível"
            format_champion_stats_summary = lambda l=None: "Stats indisponíveis"
            format_objectives_summary = lambda l=None: "Objetivos indisponíveis"
            format_enemies_summary = lambda l=None: "Inimigos indisponíveis"

try:
    from lol_lib.chat_reader import (
        LoLChatReader, PING_MISSING, PING_DANGER, PING_ON_MY_WAY,
        PING_CAUTION, PING_ASSIST, PING_SPELL, PING_CHAT
    )
except Exception:
    try:
        from chat_reader import (
            LoLChatReader, PING_MISSING, PING_DANGER, PING_ON_MY_WAY,
            PING_CAUTION, PING_ASSIST, PING_SPELL, PING_CHAT
        )
    except Exception:
        try:
            from lib.chat_reader import (
                LoLChatReader, PING_MISSING, PING_DANGER, PING_ON_MY_WAY,
                PING_CAUTION, PING_ASSIST, PING_SPELL, PING_CHAT
            )
        except Exception as e:
            log.error(f"lolAccessibility: Falha ao importar chat_reader: {e}")
            LoLChatReader = None
            PING_MISSING = "MISSING"
            PING_DANGER = "DANGER"
            PING_ON_MY_WAY = "ON_MY_WAY"
            PING_CAUTION = "CAUTION"
            PING_ASSIST = "ASSIST"
            PING_SPELL = "SPELL"
            PING_CHAT = "CHAT"


try:
    from lol_lib.minimap_scanner import LoLMinimapScanner
except Exception:
    try:
        from minimap_scanner import LoLMinimapScanner
    except Exception:
        try:
            from lib.minimap_scanner import LoLMinimapScanner
        except Exception as e:
            log.error(f"lolAccessibility: Falha ao importar minimap_scanner: {e}")
            LoLMinimapScanner = None

try:
    from lol_lib.spatial_audio import get_spatial_audio_player, generate_pcm_stereo_tone
except Exception:
    try:
        from spatial_audio import get_spatial_audio_player, generate_pcm_stereo_tone
    except Exception:
        try:
            from lib.spatial_audio import get_spatial_audio_player, generate_pcm_stereo_tone
        except Exception as e:
            log.error(f"lolAccessibility: Falha ao importar spatial_audio: {e}")
            get_spatial_audio_player = lambda: None
            generate_pcm_stereo_tone = lambda *a, **kw: b""

try:
    from lol_lib.shop_assistant import LoLShopAssistant
except Exception:
    try:
        from shop_assistant import LoLShopAssistant
    except Exception:
        try:
            from lib.shop_assistant import LoLShopAssistant
        except Exception as e:
            log.error(f"lolAccessibility: Falha ao importar shop_assistant: {e}")
            LoLShopAssistant = None

try:
    from lol_lib.combat_status import LoLCombatStatus
except Exception:
    try:
        from combat_status import LoLCombatStatus
    except Exception:
        try:
            from lib.combat_status import LoLCombatStatus
        except Exception as e:
            log.error(f"lolAccessibility: Falha ao importar combat_status: {e}")
            LoLCombatStatus = None

try:
    from lol_lib.tactical_navigator import get_tactical_navigator, TacticalNavigator
except Exception:
    try:
        from tactical_navigator import get_tactical_navigator, TacticalNavigator
    except Exception:
        try:
            from lib.tactical_navigator import get_tactical_navigator, TacticalNavigator
        except Exception as e:
            log.error(f"lolAccessibility: Falha ao importar tactical_navigator: {e}")
            get_tactical_navigator = lambda: None
            TacticalNavigator = None



try:
    from lol_lib.text_cleaner import shared_cleaner
except Exception:
    try:
        from text_cleaner import shared_cleaner
    except Exception:
        try:
            from lib.text_cleaner import shared_cleaner
        except Exception:
            shared_cleaner = None

try:
    from lol_lib.tos_helper import LoLToSHelper, scroll_and_accept_async
except Exception:
    try:
        from tos_helper import LoLToSHelper, scroll_and_accept_async
    except Exception:
        try:
            from lib.tos_helper import LoLToSHelper, scroll_and_accept_async
        except Exception:
            LoLToSHelper = None
            scroll_and_accept_async = lambda *a, **kw: None


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    """Plugin global de acessibilidade para League of Legends e Riot Client."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        log.info("=" * 60)
        log.info("lolAccessibility: Carregando Global Plugin com Live Game Engine...")
        
        self.auto_accept = False
        self._running = True
        self._last_ready_check_state = None
        self._last_phase = None
        self._last_event_id = -1
        self._last_player_level = 0
        self._last_low_hp_beep = 0
        self._in_live_game = False
        self._announced_early_lanes = False
        self.auto_pings_enabled = True
        self.chat_reader = LoLChatReader() if LoLChatReader else None
        self._last_chat_scan = 0.0
        self.auto_gank_alerts_enabled = True
        self.minimap_scanner = LoLMinimapScanner() if LoLMinimapScanner else None
        self.spatial_player = get_spatial_audio_player() if get_spatial_audio_player else None
        self.spatial_radar_enabled = True
        self._last_spatial_alarm_time = 0.0
        self.shop_assistant = LoLShopAssistant() if LoLShopAssistant else None
        self.combat_status = LoLCombatStatus() if LoLCombatStatus else None
        self.tactical_navigator = get_tactical_navigator() if get_tactical_navigator else None
        self._last_minimap_scan = 0.0
        self._last_champ_select_sec = -1
        self._last_notified_action_id = -1
        self._last_aram_announced_champ = -1
        
        # Mapeamento explícito de executáveis para AppModules
        self._registered_executables = []
        self._register_mappings()
        
        # Inicializar estado contextual do leitor de telas para Riot/LoL
        self._last_spoken = ""
        if filter_speechSequence:
            try:
                filter_speechSequence.register(self.filter_speech)
                log.info("lolAccessibility: Filtro inteligente de fala registrado com sucesso.")
            except Exception as e:
                log.debug(f"lolAccessibility: Falha ao registrar filter_speechSequence: {e}")

        # Iniciar thread de monitoramento em segundo plano (LCU e Live API)
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True, name="LoLClientMonitor")
        self._monitor_thread.start()
        
        log.info("lolAccessibility: Global Plugin com Live Game carregado!")
        log.info("=" * 60)

    def _register_mappings(self):
        """Mapeia executáveis do Riot Client e LoL para os módulos."""
        riot_exes = [
            "riot client", "riot client.exe",
            "riotclientux", "riotclientux.exe",
            "riotclientservices", "riotclientservices.exe"
        ]
        launcher_exes = [
            "leagueclientuxrender", "leagueclientuxrender.exe",
            "leagueclientux", "leagueclientux.exe",
            "leagueclient", "leagueclient.exe"
        ]
        game_exes = [
            "league of legends", "league of legends.exe",
            "League of Legends", "League of Legends.exe",
            "leagueoflegends", "leagueoflegends.exe",
            "league_of_legends", "league_of_legends.exe"
        ]
        
        for exe in riot_exes:
            try:
                appModuleHandler.registerExecutableWithAppModule(exe, "riotclient")
                self._registered_executables.append(exe)
                log.info(f"lolAccessibility: Mapeado '{exe}' -> 'riotclient'")
            except Exception as e:
                log.debug(f"lolAccessibility: Erro ao mapear {exe}: {e}")
                
        for exe in launcher_exes:
            try:
                appModuleHandler.registerExecutableWithAppModule(exe, "leagueclient")
                self._registered_executables.append(exe)
                log.info(f"lolAccessibility: Mapeado '{exe}' -> 'leagueclient'")
            except Exception as e:
                log.debug(f"lolAccessibility: Erro ao mapear {exe}: {e}")

        for exe in game_exes:
            try:
                appModuleHandler.registerExecutableWithAppModule(exe, "leagueoflegends")
                self._registered_executables.append(exe)
                log.info(f"lolAccessibility: Mapeado '{exe}' -> 'leagueoflegends'")
            except Exception as e:
                log.debug(f"lolAccessibility: Erro ao mapear {exe}: {e}")

        # Limpar cache de processos ativos para forçar a vinculação do novo módulo
        try:
            for pid in list(appModuleHandler.runningTable.keys()):
                app_name = appModuleHandler.getAppNameFromProcessID(pid, includeExt=False) or ""
                if any(k in app_name.lower() for k in ["riot", "league"]):
                    del appModuleHandler.runningTable[pid]
                    log.info(f"lolAccessibility: Recarregando appModule para PID {pid} ({app_name})")
        except Exception:
            pass

    def terminate(self, *args, **kwargs):
        """Finalização limpa do plugin."""
        log.info("lolAccessibility: Finalizando Global Plugin...")
        self._running = False
        
        if filter_speechSequence:
            try:
                filter_speechSequence.unregister(self.filter_speech)
            except Exception:
                pass

        for exe in self._registered_executables:
            try:
                appModuleHandler.unregisterExecutable(exe)
            except Exception:
                pass
                
        super().terminate(*args, **kwargs)

    # ========================================================================
    # FILTRO INTELIGENTE DE FALA (RIOT CLIENT E LEAGUE OF LEGENDS)
    # ========================================================================

    def _is_riot_or_league_focused(self):
        """Verifica se o foco do usuário está em uma aplicação da Riot ou League of Legends."""
        now = time.time()
        try:
            focus = api.getFocusObject()
            if focus:
                pid = getattr(focus, "processID", 0)
                if pid:
                    app_name = (appModuleHandler.getAppNameFromProcessID(pid, includeExt=False) or "").lower()
                    if any(k in app_name for k in ["riot", "league"]):
                        self._last_riot_focus_time = now
                        return True
                app_mod = getattr(focus, "appModule", None)
                if app_mod:
                    mod_name = (getattr(app_mod, "appModuleName", "") or getattr(app_mod, "__module__", "")).lower()
                    if any(k in mod_name for k in ["riot", "league"]):
                        self._last_riot_focus_time = now
                        return True

            fg = api.getForegroundObject()
            if fg:
                pid = getattr(fg, "processID", 0)
                if pid:
                    app_name = (appModuleHandler.getAppNameFromProcessID(pid, includeExt=False) or "").lower()
                    if any(k in app_name for k in ["riot", "league"]):
                        self._last_riot_focus_time = now
                        return True
                app_mod = getattr(fg, "appModule", None)
                if app_mod:
                    mod_name = (getattr(app_mod, "appModuleName", "") or getattr(app_mod, "__module__", "")).lower()
                    if any(k in mod_name for k in ["riot", "league"]):
                        self._last_riot_focus_time = now
                        return True

            try:
                import winUser
                hwnd = winUser.getForegroundWindow()
                if hwnd:
                    _, fg_pid = winUser.getWindowThreadProcessID(hwnd)
                    if fg_pid:
                        app_name = (appModuleHandler.getAppNameFromProcessID(fg_pid, includeExt=False) or "").lower()
                        if any(k in app_name for k in ["riot", "league"]):
                            self._last_riot_focus_time = now
                            return True
            except Exception:
                pass

            pass
        except Exception:
            pass
        return False

    def _is_league_game_window_focused(self):
        """Verifica se a janela 3D da partida do LoL (RiotWindowClass / League of Legends.exe) está em primeiro plano."""
        try:
            import winUser
            hwnd = winUser.getForegroundWindow()
            if not hwnd:
                import ctypes
                hwnd = ctypes.windll.user32.GetForegroundWindow()
            if hwnd:
                cls_name = winUser.getClassName(hwnd)
                if cls_name == "RiotWindowClass":
                    return True
                _, pid = winUser.getWindowThreadProcessID(hwnd)
                if pid:
                    app_name = (appModuleHandler.getAppNameFromProcessID(pid, includeExt=False) or "").lower()
                    if "league of legends" in app_name:
                        return True
                    if app_name and not any(k in app_name for k in ["riot", "league", "nvda", "system"]):
                        return False

            fg_obj = api.getForegroundObject()
            if fg_obj:
                pid = getattr(fg_obj, "processID", 0)
                if pid:
                    app_name = (appModuleHandler.getAppNameFromProcessID(pid, includeExt=False) or "").lower()
                    if "league of legends" in app_name:
                        return True
                    if app_name and not any(k in app_name for k in ["riot", "league", "nvda", "system"]):
                        return False
        except Exception:
            pass
        return False

    def _is_riot_or_league_active_window(self):
        """Verifica estritamente se a janela ativa pertence ao League of Legends ou Riot Client."""
        try:
            import winUser
            hwnd = winUser.getForegroundWindow()
            if not hwnd:
                import ctypes
                hwnd = ctypes.windll.user32.GetForegroundWindow()
            if hwnd:
                cls_name = winUser.getClassName(hwnd)
                if cls_name in ("RiotWindowClass", "Chrome_RenderWidgetHostHWND"):
                    _, pid = winUser.getWindowThreadProcessID(hwnd)
                    if pid:
                        app_name = (appModuleHandler.getAppNameFromProcessID(pid, includeExt=False) or "").lower()
                        if any(k in app_name for k in ["riot", "league"]):
                            return True
                _, pid = winUser.getWindowThreadProcessID(hwnd)
                if pid:
                    app_name = (appModuleHandler.getAppNameFromProcessID(pid, includeExt=False) or "").lower()
                    if any(k in app_name for k in ["riot", "league"]):
                        return True
                    if app_name and not any(k in app_name for k in ["nvda", "system"]):
                        return False

            fg_obj = api.getForegroundObject()
            if fg_obj:
                pid = getattr(fg_obj, "processID", 0)
                if pid:
                    app_name = (appModuleHandler.getAppNameFromProcessID(pid, includeExt=False) or "").lower()
                    if any(k in app_name for k in ["riot", "league"]):
                        return True
                    if app_name and not any(k in app_name for k in ["nvda", "system"]):
                        return False
        except Exception:
            pass
        return False

    def _should_handle_launcher_gesture(self, gesture):
        """
        Determina se atalhos do inicializador/LCU devem ser processados ou repassados:
        - Se a janela ativa for o Riot Client ou League Client, processa sempre.
        - Se o usuário estiver em outro aplicativo (Chrome, VS Code, Bloco de Notas, etc.),
          só processa se o atalho utilizar expressamente o modificador do NVDA (ex: NVDA+Shift+L, NVDA+Shift+P).
          Qualquer atalho comum como Control+Shift+P, Control+Shift+S, etc. é repassado ao sistema.
        """
        if self._is_riot_or_league_active_window():
            return True

        gesture_id = getattr(gesture, "id", "") or ""
        mod_names = getattr(gesture, "modifierNames", None) or set()
        if "nvda" in gesture_id.lower() or "nvda" in [str(m).lower() for m in mod_names]:
            if is_live_game_active() or get_league_client_lockfile() or get_riot_client_lockfile():
                return True

        return False

    def _should_handle_game_gesture(self, gesture):
        """
        Determina se o gesto deve ser processado pelo LoL ou repassado ao sistema:
        - O gesto SÓ É PROCESSADO se a partida ao vivo 3D estiver ativa E a janela do jogo 3D (RiotWindowClass) estiver em primeiro plano!
        - Se o usuário estiver em qualquer outro programa (Chrome, Bloco de Notas, TeamTalk, etc.),
          retorna SEMPRE False para que o gesto seja repassado via gesture.send() sem roubar atalhos do sistema.
        - EXCEÇÃO: Atalhos iniciados por NVDA+shift+ (ex: NVDA+Shift+T, NVDA+Shift+K) são comandos dedicados de acessibilidade
          que nunca colidem com navegadores ou outros aplicativos normais.
        """
        if not is_live_game_active():
            return False

        if self._is_league_game_window_focused():
            return True

        gesture_id = getattr(gesture, "id", "") or ""
        mod_names = getattr(gesture, "modifierNames", None) or set()
        if "nvda" in gesture_id.lower() or "nvda" in [str(m).lower() for m in mod_names]:
            return True

        return False

    def filter_speech(self, speechSequence):
        """
        Normaliza e limpa as sequências de fala sintetizadas pelo NVDA quando o usuário
        está interagindo com o Riot Client ou com o League of Legends.
        Elimina ruídos do Chromium (ex: 'animation', 'descrições ausentes'), rotula abas
        e botões no buffer virtual e formata métricas de download e vídeos promocionais.
        """
        is_focused = self._is_riot_or_league_focused()
        if not is_focused:
            has_riot_signature = False
            for item in speechSequence:
                if isinstance(item, str):
                    s = item.lower()
                    if any(k in s for k in [
                        "gb@", "mb/s", "video off", "video on", "descrições ausentes",
                        "grupo começa aqui", "sem amigos no momento", "multifator",
                        "torne-se uma lenda", "salvation", "disponibilidade de plataformas",
                        "requisitos do sistema", "configuração mínima", "configuração recomendada",
                        "sistema operacional", "arquitetura do sistema operacional"
                    ]):
                        has_riot_signature = True
                        break
            if not has_riot_signature:
                return speechSequence

        new_sequence = []
        for item in speechSequence:
            if not isinstance(item, str):
                new_sequence.append(item)
                continue

            cleaned = shared_cleaner.clean_single_line(item) if shared_cleaner else item
            if cleaned:
                new_sequence.append(cleaned)

        return new_sequence

    # ========================================================================
    # MONITOR DE EVENTOS EM SEGUNDO PLANO (LCU + LIVE GAME 127.0.0.1:2999)
    # ========================================================================

    def _monitor_loop(self):
        """Loop contínuo de monitoramento executado a cada 0.8s."""
        while self._running:
            try:
                # 1. Verificar se há partida 3D ao vivo rodando (Live Client Data API)
                if is_live_game_active():
                    if not self._in_live_game:
                        self._in_live_game = True
                        self._last_event_id = -1
                        self._last_player_level = 0
                        self._announced_early_lanes = False
                        try:
                            tones.beep(523, 100)
                            tones.beep(659, 100)
                            tones.beep(784, 150)
                        except Exception:
                            pass
                        ui.message("Partida ao vivo iniciada! Live Game Audio Engine ativo.")
                    self._check_live_game_events()
                    if getattr(self, "auto_pings_enabled", True) and getattr(self, "chat_reader", None):
                        now = time.time()
                        if now - getattr(self, "_last_chat_scan", 0.0) >= 1.6:
                            self._last_chat_scan = now
                            self._check_chat_pings()
                    if getattr(self, "auto_gank_alerts_enabled", True) and getattr(self, "minimap_scanner", None):
                        now = time.time()
                        if now - getattr(self, "_last_minimap_scan", 0.0) >= 1.8:
                            self._last_minimap_scan = now
                            self._check_minimap_alerts()
                else:
                    if self._in_live_game:
                        self._in_live_game = False
                        self._announced_early_lanes = False
                        ui.message("Partida ao vivo encerrada.")

                # 2. Verificar eventos pré/pós jogo do League Client (LCU)
                lcu_lock = get_league_client_lockfile()
                if lcu_lock and not self._in_live_game:
                    self._check_lcu_events()

            except Exception as e:
                log.debug(f"lolAccessibility: Erro no loop de monitoramento: {e}")
                
            time.sleep(0.8)

    def _check_live_game_events(self):
        """Processa eventos em tempo real da Live Client Data API (2999)."""
        active = get_live_active_player()
        if active and isinstance(active, dict):
            stats = active.get("championStats", {})
            cur_hp = stats.get("currentHealth", 0)
            max_hp = stats.get("maxHealth", 1)
            level = active.get("level", 0)

            # Alerta de Level Up
            if self._last_player_level > 0 and level > self._last_player_level:
                try:
                    tones.beep(587, 80)
                    tones.beep(880, 120)
                except Exception:
                    pass
                ui.message(f"Subiu para o nível {level}!")
            self._last_player_level = level

            # Alerta sonoro de Vida Baixa / Batimento Cardíaco (< 30% de vida)
            if getattr(self, "combat_status", None):
                self.combat_status.update_player_health(cur_hp, max_hp)
                if self.combat_status.is_recalling:
                    r_ev, r_msg = self.combat_status.update_recall(cur_hp)
                    if r_msg and r_ev != "PROGRESS":
                        ui.message(r_msg)

                # Monitor de Ultimate e Habilidades
                abilities = get_live_active_player_abilities()
                ab_ev, ab_msg = self.combat_status.update_abilities_cooldowns(abilities)
                if ab_ev == "ULTIMATE_READY" and ab_msg:
                    ui.message(ab_msg)
            elif max_hp > 0 and (cur_hp / max_hp) < 0.25 and cur_hp > 0:
                now = time.time()
                if now - self._last_low_hp_beep > 2.5:
                    self._last_low_hp_beep = now
                    try:
                        tones.beep(440, 80)
                        tones.beep(330, 80)
                    except Exception:
                        pass

        # Anúncio automático de rotas aos ~60s de partida (quando as tropas marcham)
        if not getattr(self, "_announced_early_lanes", False):
            gamestats = get_live_game_stats()
            if gamestats:
                gtime = gamestats.get("gameTime") or gamestats.get("game_time") or 0.0
                if 60.0 <= gtime <= 85.0:
                    lane_info = get_live_enemy_lane_assignments()
                    if lane_info and lane_info.get("text"):
                        self._announced_early_lanes = True
                        try:
                            tones.beep(523, 100)
                            tones.beep(659, 100)
                        except Exception:
                            pass
                        ui.message(f"Alerta de rotas: {lane_info['text']}")

        event_data = get_live_event_data()
        if event_data and isinstance(event_data, dict):
            events = event_data.get("Events", [])
            for ev in events:
                eid = ev.get("EventID", 0)
                if eid <= self._last_event_id:
                    continue
                self._last_event_id = eid

                stype, msg = format_live_game_event(ev)
                if msg:
                    if stype == "KILL":
                        ui.message(msg)
                    elif stype == "MULTIKILL":
                        try:
                            tones.beep(880, 100)
                            tones.beep(1046, 150)
                        except Exception:
                            pass
                        ui.message(msg)
                    elif stype in ("DRAGON", "BARON", "HERALD"):
                        try:
                            tones.beep(523, 100)
                            tones.beep(659, 100)
                            tones.beep(784, 120)
                        except Exception:
                            pass
                        ui.message(msg)
                    elif stype in ("TURRET", "INHIB"):
                        try:
                            tones.beep(440, 120)
                            tones.beep(330, 120)
                        except Exception:
                            pass
                        ui.message(msg)
                    elif stype == "ACE":
                        try:
                            tones.beep(1046, 200)
                        except Exception:
                            pass
                        ui.message(msg)
                    elif stype in ("FIRST_BLOOD", "FIRST_BRICK"):
                        try:
                            tones.beep(698, 120)
                            tones.beep(880, 150)
                        except Exception:
                            pass
                        ui.message(msg)
                    else:
                        ui.message(msg)

    def _check_chat_pings(self):
        """Varre a caixa de chat do LoL em busca de novos pings ou mensagens."""
        if not getattr(self, "chat_reader", None):
            return
        try:
            new_items = self.chat_reader.scan_chat_sync()
            if not new_items:
                return
            for item in new_items:
                ptype = item.get("type")
                ann = item.get("announcement")
                if not ann:
                    continue

                try:
                    if ptype == PING_MISSING:
                        # Som oco descendente de alerta de MIA (?)
                        tones.beep(400, 80)
                        tones.beep(300, 120)
                    elif ptype == PING_DANGER:
                        # Som agudo de perigo (!)
                        tones.beep(880, 80)
                        tones.beep(1175, 100)
                    elif ptype == PING_ON_MY_WAY:
                        # Acorde ascendente alegre (a caminho)
                        tones.beep(523, 70)
                        tones.beep(659, 70)
                        tones.beep(784, 90)
                    elif ptype == PING_CAUTION:
                        tones.beep(440, 100)
                        tones.beep(330, 100)
                    elif ptype == PING_ASSIST:
                        tones.beep(698, 80)
                        tones.beep(698, 80)
                    elif ptype == PING_SPELL:
                        tones.beep(784, 100)
                except Exception:
                    pass

                ui.message(ann)
        except Exception as e:
            log.debug(f"lolAccessibility: Erro na varredura de chat: {e}")

    def _check_minimap_alerts(self):
        """Monitora o minimapa em busca de emboscadas e presença de múltiplos inimigos (Alerta de Gank)."""
        if not getattr(self, "minimap_scanner", None):
            return
        try:
            active = get_live_active_player() or {}
            players = get_live_player_list() or []
            my_team = "ORDER"
            summoner = active.get("summonerName", "")
            for p in players:
                if p.get("summonerName") == summoner:
                    my_team = p.get("team", "ORDER")
                    break

            lane_info = get_live_enemy_lane_assignments()
            my_lane = "BOTTOM"
            if lane_info and lane_info.get("my_assigned_lane"):
                my_lane = lane_info.get("my_assigned_lane")

            scan = None
            if getattr(self, "spatial_radar_enabled", True) and getattr(self, "spatial_player", None):
                now = time.time()
                if now - getattr(self, "_last_spatial_alarm_time", 0.0) >= 5.0:
                    scan = self.minimap_scanner.scan_radar(player_lane=my_lane, my_team=my_team)
                    if scan and scan.get("enemies"):
                        closest_enemy = min(scan["enemies"], key=lambda e: e["dist"])
                        if closest_enemy["dist"] < 0.20:
                            self._last_spatial_alarm_time = now
                            self.spatial_player.play_proximity_alarm(closest_enemy["pan"], closest_enemy["dist"])

            alert_msg = self.minimap_scanner.check_gank_threat(player_lane=my_lane, my_team=my_team)
            if alert_msg:
                pan = 0.0
                if scan and scan.get("enemies"):
                    closest = min(scan["enemies"], key=lambda e: e["dist"])
                    pan = closest.get("pan", 0.0)
                if getattr(self, "spatial_player", None):
                    self.spatial_player.play_proximity_alarm(pan, 0.08, count=3)
                else:
                    try:
                        tones.beep(880, 100)
                        tones.beep(1175, 150)
                        tones.beep(880, 100)
                    except Exception:
                        pass
                ui.message(alert_msg)
        except Exception as e:
            log.debug(f"lolAccessibility: Erro no monitor de minimapa: {e}")


    def _check_lcu_events(self):
        """Monitora Ready Check e transições de fase no LoL."""
        rc = get_lcu_ready_check()
        if rc and isinstance(rc, dict):
            state = rc.get("state")
            player_resp = rc.get("playerResponse")
            
            if state == "InProgress" and player_resp == "None":
                if self._last_ready_check_state != "InProgress":
                    self._last_ready_check_state = "InProgress"
                    try:
                        tones.beep(880, 200)
                        tones.beep(1175, 250)
                    except Exception:
                        pass
                        
                    if self.auto_accept:
                        accept_lcu_match()
                        ui.message("Partida encontrada! Aceita automaticamente.")
                    else:
                        ui.message("Partida encontrada! Pressione F6 para aceitar!")
            else:
                self._last_ready_check_state = state

        phase = get_lcu_gameflow_phase()
        if phase and phase != self._last_phase:
            if phase == "ChampSelect":
                try:
                    tones.beep(659, 150)
                except Exception:
                    pass
                ui.message("Seleção de Campeões iniciada! Pressione Control+Shift+C para detalhes.")
            elif phase == "InProgress":
                ui.message("Carregando partida...")
            elif phase == "Lobby" and self._last_phase == "Matchmaking":
                ui.message("Busca de partida cancelada.")
                
            self._last_phase = phase

        if phase == "ChampSelect":
            detailed = get_lcu_champ_select_detailed()
            if detailed:
                # 1. Alerta de Campeão no ARAM
                if detailed.get("bench_enabled"):
                    my_info = detailed.get("my_info", {})
                    cid = my_info.get("champion_id", 0)
                    cname = my_info.get("champion_name", "")
                    if cid > 0 and cid != self._last_aram_announced_champ:
                        self._last_aram_announced_champ = cid
                        ui.message(f"ARAM: Seu campeão é {cname}. Control+Shift+B para o banco, Control+Shift+D para rolar dado.")

                # 2. Alerta de Turno de Ação (Pick / Ban)
                local_action = detailed.get("local_action")
                if local_action and not local_action.get("completed"):
                    aid = local_action.get("id")
                    if aid != self._last_notified_action_id and (local_action.get("isActorActive") or local_action.get("isInProgress")):
                        self._last_notified_action_id = aid
                        atype = local_action.get("type", "pick")
                        try:
                            tones.beep(1046, 120)
                            tones.beep(1318, 180)
                        except Exception:
                            pass
                        if atype == "ban":
                            ui.message("Sua vez de banir! Pressione Control+Shift+B para banir um campeão.")
                        else:
                            ui.message("Sua vez de escolher campeão! Pressione Control+Shift+P para escolher e travar.")

                # 3. Contagem regressiva de tempo (30s, 15s, 5s a 1s)
                sec = detailed.get("time_left_sec", 0)
                if sec in (30, 15, 5, 4, 3, 2, 1) and sec != self._last_champ_select_sec:
                    self._last_champ_select_sec = sec
                    if sec == 30:
                        ui.message("30 segundos restantes na seleção.")
                    elif sec == 15:
                        try:
                            tones.beep(659, 100)
                        except Exception:
                            pass
                        ui.message("15 segundos restantes!")
                    elif sec <= 5:
                        try:
                            tones.beep(880 + (5 - sec) * 120, 80)
                        except Exception:
                            pass
                        ui.message(f"{sec}")
        else:
            self._last_champ_select_sec = -1
            self._last_notified_action_id = -1
            self._last_aram_announced_champ = -1

    # ========================================================================
    # ATALHOS GLOBAIS
    # ========================================================================

    @script(
        description="Aceita a partida encontrada no League of Legends de qualquer janela.",
        gestures=["kb:NVDA+f6"]
    )
    def script_globalAcceptMatch(self, gesture):
        """Aceita o Ready Check imediatamente."""
        # Se ReadyCheck não estiver em andamento e a janela não pertencer ao League/Riot, repassa F6 ao sistema
        if getattr(self, "_last_ready_check_state", "") != "InProgress" and not self._is_riot_or_league_active_window():
            gesture_id = getattr(gesture, "id", "") or ""
            if "nvda" not in gesture_id.lower():
                gesture.send()
                return

        ok = accept_lcu_match()
        if ok:
            try:
                tones.beep(1320, 150)
            except Exception:
                pass
            ui.message("Partida aceita com sucesso!")
        else:
            gesture.send()

    @script(
        description="Ativa ou desativa a aceitação automática de partidas.",
        gestures=["kb:control+shift+f6"]
    )
    def script_toggleAutoAccept(self, gesture):
        """Alterna auto-aceitação."""
        if not self._should_handle_launcher_gesture(gesture):
            gesture.send()
            return
        self.auto_accept = not self.auto_accept
        if self.auto_accept:
            try:
                tones.beep(880, 100)
                tones.beep(1100, 100)
            except Exception:
                pass
            ui.message("Aceitação automática de partida ATIVADA.")
        else:
            try:
                tones.beep(1100, 100)
                tones.beep(880, 100)
            except Exception:
                pass
            ui.message("Aceitação automática de partida DESATIVADA.")

    @script(
        description="Anuncia o status global do Riot Client e League of Legends.",
        gestures=["kb:NVDA+shift+l"]
    )
    def script_announceGlobalStatus(self, gesture):
        """Verifica o status atual de todos os componentes da Riot."""
        if not self._should_handle_launcher_gesture(gesture):
            gesture.send()
            return
        if is_live_game_active():
            stats = get_live_game_stats()
            gtime = int(stats.get("gameTime", 0)) if stats else 0
            mins, secs = divmod(gtime, 60)
            ui.message(f"Partida ao vivo em andamento! Tempo: {mins} minutos e {secs} segundos.")
            return

        riot_lock = get_riot_client_lockfile()
        lcu_lock = get_league_client_lockfile()
        
        parts = []
        if riot_lock:
            user = get_riot_user_info()
            user_str = f" ({user['full_tag']})" if user else ""
            parts.append(f"Riot Client ativo{user_str}")
            
        if lcu_lock:
            phase = get_lcu_gameflow_phase()
            sum_info = get_lcu_summoner_info()
            sum_str = f" ({sum_info['full_tag']}, Nível {sum_info['level']})" if sum_info else ""
            if phase == "ReadyCheck":
                parts.append(f"League Client: Partida encontrada! Pressione F6 para aceitar{sum_str}")
            elif phase == "ChampSelect":
                parts.append(f"League Client: Na Seleção de Campeões{sum_str}")
            elif phase == "Matchmaking":
                search = get_lcu_search_state()
                if search and search.get("is_searching"):
                    tiq = search.get("time_in_queue", 0)
                    m, s = divmod(tiq, 60)
                    parts.append(f"League Client: Buscando partida ({m}m {s}s na fila){sum_str}")
                else:
                    parts.append(f"League Client: Buscando partida{sum_str}")
            elif phase == "Lobby":
                lobby = get_lcu_lobby_info()
                mode = lobby.get("game_mode", "LoL") if lobby else "LoL"
                penalty = get_lcu_queue_penalty()
                pen_str = f" [Penalidade ativa: resta {penalty['time_str']}]" if penalty and penalty.get("has_penalty") else ""
                parts.append(f"League Client: No Saguão de {mode}{pen_str}{sum_str}")
            elif phase == "InProgress":
                parts.append(f"League Client: Partida em andamento{sum_str}")
            else:
                parts.append(f"League Client aberto no Início{sum_str}")
            
        if not parts:
            ui.message("Nenhum cliente da Riot ou League of Legends detectado.")
        else:
            auto_str = " (Auto-Aceitar Ativo)" if self.auto_accept else ""
            ui.message(" | ".join(parts) + auto_str)

    @script(
        description="Anuncia globalmente o perfil autenticado da Riot Games.",
        gestures=["kb:NVDA+shift+s"]
    )
    def script_announceGlobalUserInfo(self, gesture):
        """Consulta as informações do perfil autenticado na Riot ou League of Legends."""
        if not self._should_handle_launcher_gesture(gesture):
            gesture.send()
            return
        riot_lock = get_riot_client_lockfile()
        lcu_lock = get_league_client_lockfile()
        if not riot_lock and not lcu_lock and not is_live_game_active():
            gesture.send()
            return

        if lcu_lock:
            sum_info = get_lcu_summoner_info()
            ranked = get_lcu_ranked_stats()
            if sum_info:
                name = sum_info["full_tag"]
                lvl = sum_info["level"]
                xp_pct = sum_info["xp_percent"]
                xp_cur = sum_info["xp_current"]
                xp_need = sum_info["xp_needed"]
                ui.message(f"Invocador: {name}, Nível {lvl} ({xp_cur}/{xp_need} XP, {xp_pct}%). Ranqueada: {ranked}.")
                return

        info = get_riot_user_info()
        if info:
            regiao = f" (Região {info['region'].upper()})" if info.get("region") else ""
            ui.message(f"Conectado como: {info['full_tag']}, Status: Online{regiao}")
        else:
            ui.message("Usuário conectado no Riot Client. Status: Online.")

    @script(
        description="Anuncia o progresso atual do download ou atualização do League of Legends.",
        gestures=["kb:NVDA+shift+d"]
    )
    def script_announceGlobalDownload(self, gesture):
        """Varre a tela do cliente e consulta a API para anunciar o download/instalação."""
        if not self._should_handle_launcher_gesture(gesture):
            gesture.send()
            return
        found_text = []
        is_ready = False
        try:
            fg = api.getForegroundObject()
            if fg:
                def walk(o, depth=0):
                    nonlocal is_ready
                    if depth > 12:
                        return
                    name = (o.name or "").strip()
                    val = (getattr(o, "value", "") or "").strip()
                    for t in (name, val):
                        if not t:
                            continue
                        t_upper = t.upper()
                        if t_upper in ("JOGAR", "PLAY", "INICIAR JOGO"):
                            is_ready = True
                        if any(k in t_upper for k in ["GB@", "MB/S", "KB/S", "GB DE", "INSTALANDO", "ATUALIZANDO", "PAUSADO", "VANGUARD"]):
                            if t not in found_text:
                                found_text.append(t)
                        elif "/" in t and any(unit in t_upper for unit in ["GB", "MB"]):
                            if t not in found_text:
                                found_text.append(t)
                    for child in o.children:
                        walk(child, depth + 1)
                walk(fg)
        except Exception:
            pass

        if is_ready and not found_text:
            ui.message("League of Legends está 100% instalado e pronto para jogar! Pressione Enter em 'Jogar'.")
            return

        if found_text:
            ui.message("Progresso de Download: " + ". ".join(found_text))
            return

        user = get_riot_user_info()
        user_name = user["full_tag"] if user else "Invocador"
        ui.message(f"Status do League of Legends: Pronto para jogar ({user_name}).")
        return

    @script(
        description="Move o foco ou ativa o botão principal (Jogar, Instalar, Atualizar, Ações e Modais do LoL).",
        gestures=["kb:NVDA+shift+j"]
    )
    def script_focusActionButton(self, gesture):
        if not self._should_handle_launcher_gesture(gesture):
            gesture.send()
            return
        lcu_lock = get_league_client_lockfile()

        # 0. Verificar se há diálogo de Termos de Serviço ou botão 'Role para aceitar'
        try:
            fg = api.getForegroundObject()
            if fg:
                has_tos = False
                def check_tos_node(o, depth=0):
                    nonlocal has_tos
                    if has_tos or depth > 8:
                        return
                    t = f"{o.name or ''} {getattr(o, 'value', '') or ''}".lower()
                    if any(k in t for k in ["role para aceitar", "termos de serviço", "termos de servico", "contrato do usuário", "acordo de licença"]):
                        has_tos = True
                        return
                    for c in getattr(o, "children", []):
                        check_tos_node(c, depth + 1)
                check_tos_node(fg)
                if has_tos:
                    ui.message("Diálogo de Termos de Serviço detectado! Rolando e aceitando...")
                    if scroll_and_accept_async:
                        def _cb(ok, msg):
                            ui.message(msg)
                        scroll_and_accept_async(callback=_cb)
                        return
        except Exception as e:
            log.debug(f"lolAccessibility: Erro ao verificar termos na tela: {e}")

        # 1. Tentar primeiro localizar e clicar em botões modais ou de confirmação na tela (TÔ DENTRO, ENTENDI, etc.)
        try:
            candidates = []
            fg = api.getForegroundObject()
            focus = api.getFocusObject()
            if fg:
                candidates.append(fg)
                ti = getattr(fg, "treeInterceptor", None)
                if ti and hasattr(ti, "rootNVDAObject"):
                    candidates.append(ti.rootNVDAObject)
            if focus and focus != fg:
                candidates.append(focus)
                ti = getattr(focus, "treeInterceptor", None)
                if ti and hasattr(ti, "rootNVDAObject"):
                    candidates.append(ti.rootNVDAObject)

            target = None
            modal_targets = [
                "tô dentro", "to dentro", "entendi", "continuar", "confirmar",
                "concluído", "concluido", "aceitar", "dispensar", "fechar", "ok",
                "começar", "comecar", "iniciar", "vamos nessa", "resgatar",
                "reivindicar", "reivindique", "próximo", "proximo"
            ]
            action_targets = [
                "jogar", "play", "encontrar partida", "buscar partida",
                "iniciar jogo", "instalar", "atualizar", "install", "update",
                "começar", "comecar", "iniciar", "vamos nessa"
            ]
            all_search = modal_targets + action_targets

            def find_btn(o, depth=0):
                nonlocal target
                if target or depth > 15:
                    return
                name = (o.name or "").lower().strip()
                role = getattr(o, "role", None)
                is_btn = (role == controlTypes.Role.BUTTON) or ("button" in getattr(o, "className", "").lower())
                
                # Priorizar botões modais mesmo que o role não seja estritamente BUTTON
                for st in all_search:
                    if st in name:
                        target = o
                        return
                for c in getattr(o, "children", []):
                    find_btn(c, depth + 1)

            for cand in candidates:
                if target:
                    break
                find_btn(cand)

            if target:
                target.setFocus()
                try:
                    target.doDefaultAction()
                except Exception:
                    pass
                try:
                    tones.beep(1046, 100)
                    tones.beep(1318, 150)
                except Exception:
                    pass
                ui.message(f"Ação executada: {target.name}")
                # Se for botão modal (ex: TÔ DENTRO ou COMEÇAR), conclui aqui
                if any(mt in (target.name or "").lower() for mt in modal_targets):
                    return
        except Exception as e:
            log.debug(f"lolAccessibility: Erro ao buscar botão na UI: {e}")

        # 2. Descartar notificações e alertas via LCU
        if lcu_lock:
            dismissed = dismiss_lcu_notifications()
            if dismissed > 0:
                tones.beep(880, 100)
                ui.message(f"Avisos e termos ({dismissed}) confirmados com sucesso!")

            phase = get_lcu_gameflow_phase()
            if phase == "Matchmaking":
                ok = cancel_lcu_matchmaking()
                if ok:
                    tones.beep(440, 100)
                    ui.message("Busca de partida cancelada.")
                    return

            if phase == "Lobby":
                lobby = get_lcu_lobby_info()
                if lobby and lobby.get("is_leader"):
                    penalty = get_lcu_queue_penalty()
                    if penalty and penalty.get("has_penalty"):
                        tones.beep(330, 200)
                        ui.message(penalty["text"])
                        return

                    ok = start_lcu_matchmaking()
                    if ok:
                        tones.beep(1100, 120)
                        tones.beep(1320, 150)
                        ui.message("Iniciando busca de partida!")
                        return
                    else:
                        penalty = get_lcu_queue_penalty()
                        if penalty and penalty.get("has_penalty"):
                            tones.beep(330, 200)
                            ui.message(penalty["text"])
                        else:
                            ui.message("Não foi possível iniciar a busca. Verifique se há restrições ou termos pendentes.")
                        return

            if phase == "ReadyCheck":
                ok = accept_lcu_match()
                if ok:
                    tones.beep(1320, 150)
                    ui.message("Partida aceita com sucesso!")
                    return

        if lcu_lock and get_lcu_gameflow_phase() is None:
            # Tenta fila de iniciante (880), ARAM (450) ou tutoriais (2000, 2010, 2020)
            for q_id in [880, 450, 2000, 2010, 2020]:
                ok = create_lcu_lobby(q_id)
                if ok:
                    tones.beep(880, 120)
                    ui.message("Saguão aberto com sucesso!")
                    return

        ui.message("Nenhum botão de ação principal localizado na tela atual.")

    @script(
        description="Rola o container de Termos de Serviço (ToS) e clica em Aceitar no Riot Client ou League of Legends.",
        gestures=["kb:NVDA+shift+t"]
    )
    def script_globalAcceptTerms(self, gesture):
        if not self._should_handle_launcher_gesture(gesture):
            gesture.send()
            return
        ui.message("Iniciando rolagem e aceitação dos Termos de Serviço...")
        if scroll_and_accept_async:
            def _cb(ok, msg):
                ui.message(msg)
            scroll_and_accept_async(callback=_cb)
        else:
            ui.message("Assistente de termos não disponível.")

    @script(
        description="Abre o assistente para escolher e travar campeão com runas e feitiços automáticos.",
        gestures=["kb:NVDA+shift+p"]
    )
    def script_globalPickChampion(self, gesture):
        if not self._should_handle_launcher_gesture(gesture):
            gesture.send()
            return
        lcu_lock = get_league_client_lockfile()
        if not lcu_lock:
            ui.message("League Client não detectado.")
            return

        phase = get_lcu_gameflow_phase()
        if phase != "ChampSelect":
            ui.message("A seleção de campeões não está ativa no momento.")
            return

        detailed = get_lcu_champ_select_detailed()

        def _do_pick(champ_name):
            ok, msg, cname = pick_or_ban_champion(champ_name, is_ban=False, lock_in=True)
            if ok:
                try:
                    tones.beep(1046, 100)
                    tones.beep(1318, 150)
                except Exception:
                    pass
            else:
                try:
                    tones.beep(440, 150)
                except Exception:
                    pass
            ui.message(msg)

        try:
            import appModules.leagueclient as lc
            if hasattr(lc, "prompt_champion_dialog"):
                opened = lc.prompt_champion_dialog(_do_pick, is_ban=False)
                if opened:
                    return
        except Exception as e:
            log.debug(f"lolAccessibility: Erro ao abrir diálogo de campeões: {e}")

        ui.message("Interface gráfica de diálogo não disponível.")

    @script(
        description="Gerencia o banco de reservas no ARAM ou abre o assistente para banir campeão.",
        gestures=["kb:NVDA+shift+b"]
    )
    def script_globalBanOrBench(self, gesture):
        if not self._should_handle_launcher_gesture(gesture):
            gesture.send()
            return
        lcu_lock = get_league_client_lockfile()
        detailed = get_lcu_champ_select_detailed() if lcu_lock else None
        if not detailed:
            gesture.send()
            return

        try:
            import appModules.leagueclient as lc
            if detailed.get("bench_enabled"):
                bench = detailed.get("bench", [])
                if not bench:
                    ui.message("O banco de reservas do ARAM está vazio no momento.")
                    return
                def _do_swap(cid):
                    ok, msg = swap_lcu_aram_bench(cid)
                    if ok:
                        try:
                            tones.beep(1175, 120)
                        except Exception:
                            pass
                    ui.message(msg)
                opened = lc.prompt_aram_bench_dialog(bench, _do_swap)
                if opened:
                    return
            else:
                def _do_ban(champ_name):
                    ok, msg, cname = pick_or_ban_champion(champ_name, is_ban=True, lock_in=True)
                    if ok:
                        try:
                            tones.beep(880, 120)
                        except Exception:
                            pass
                    ui.message(msg)
                opened = lc.prompt_champion_dialog(_do_ban, is_ban=True)
                if opened:
                    return
        except Exception:
            pass
        gesture.send()

    @script(
        description="Importa a melhor página de runas recomendadas e configura os feitiços de invocador.",
        gestures=["kb:NVDA+shift+r"]
    )
    def script_globalImportRunes(self, gesture):
        if not self._should_handle_launcher_gesture(gesture):
            gesture.send()
            return
        lcu_lock = get_league_client_lockfile()
        detailed = get_lcu_champ_select_detailed() if lcu_lock else None
        if not detailed:
            gesture.send()
            return
        ok, msg = import_recommended_runes_and_spells()
        if ok:
            try:
                tones.beep(1175, 120)
            except Exception:
                pass
        ui.message(msg)

    @script(
        description="Configura acessivelmente suas preferências de rotas no saguão (Top, Jungle, Mid, Bot, Sup).",
        gestures=["kb:NVDA+shift+o"]
    )
    def script_globalSetLobbyPositions(self, gesture):
        if not self._should_handle_launcher_gesture(gesture):
            gesture.send()
            return
        if is_live_game_active():
            self.script_liveEnemies(gesture)
            return

        lcu_lock = get_league_client_lockfile()
        phase = get_lcu_gameflow_phase() if lcu_lock else None
        if phase != "Lobby":
            gesture.send()
            return

        try:
            import appModules.leagueclient as lc
            def _do_set_roles(p1, p2):
                ok, msg = set_lcu_lobby_positions(p1, p2)
                if ok:
                    try:
                        tones.beep(1046, 120)
                    except Exception:
                        pass
                ui.message(msg)
            opened = lc.prompt_lobby_roles_dialog(_do_set_roles)
            if opened:
                return
        except Exception:
            pass
        gesture.send()

    @script(
        description="Anuncia informações detalhadas da Seleção de Campeões.",
        gestures=["kb:NVDA+shift+c"]
    )
    def script_globalChampSelectInfo(self, gesture):
        if not self._should_handle_launcher_gesture(gesture):
            gesture.send()
            return
        lcu_lock = get_league_client_lockfile()
        detailed = get_lcu_champ_select_detailed() if lcu_lock else None
        if not detailed:
            gesture.send()
            return

        parts = [f"{detailed['time_left_sec']} segundos restantes ({detailed['phase']})"]
        my_info = detailed.get("my_info", {})
        if my_info:
            cname = my_info.get("champion_name", "Não selecionado")
            pos = my_info.get("position_pt", "")
            spells = ", ".join(my_info.get("spells", []))
            pos_str = f", rota {pos}" if pos and pos != "Não selecionado" else ""
            if cname and cname != "Não selecionado":
                parts.append(f"Seu campeão: {cname}{pos_str} (Feitiços: {spells})")
            else:
                parts.append(f"Seu campeão: Ainda não escolhido{pos_str}")

        teammates = []
        for m in detailed.get("my_team", []):
            if not m.get("is_me"):
                pos = m.get("position_pt", "")
                pos_str = f" ({pos})" if pos and pos != "Não selecionado" else ""
                teammates.append(f"{m.get('champion_name')}{pos_str}")
        if teammates:
            parts.append("Aliados: " + ", ".join(teammates))

        if detailed.get("bench_enabled"):
            bench = detailed.get("bench", [])
            dice = detailed.get("rerolls_remaining", 0)
            if bench:
                bnames = [b["name"] for b in bench]
                parts.append(f"Banco ARAM ({len(bench)}): {', '.join(bnames)}. Dados restantes: {dice}")
            else:
                parts.append(f"Banco ARAM vazio. Dados restantes: {dice}")

        ui.message(". ".join(parts) + ".")

    @script(
        description="Exibe os atalhos de acessibilidade do Riot Client e League of Legends.",
        gestures=["kb:NVDA+shift+h"]
    )
    def script_help(self, gesture):
        help_text = (
            "Atalhos lolAccessibility: "
            "F6: Aceitar partida encontrada no LoL. "
            "Control+Shift+F6: Alternar aceitação automática de partida. "
            "Control+Shift+T ou NVDA+Shift+T: Rolar e aceitar Termos de Serviço (ToS) automaticamente. "
            "Control+Shift+J ou NVDA+Shift+J: Pressionar botão principal (Jogar, Modais, Termos, Saguão). "
            "Control+Shift+P ou NVDA+Shift+P: Escolher e travar campeão (com runas automáticas). "
            "Control+Shift+B ou NVDA+Shift+B: Banco do ARAM ou banir campeão. "
            "Control+Shift+D ou NVDA+Shift+D: Rolar dado no ARAM ou progresso de download. "
            "Control+Shift+R ou NVDA+Shift+R: Importar runas e feitiços recomendados. "
            "Control+Shift+O ou NVDA+Shift+O: Selecionar rotas no saguão (Top, Jungle, Mid, Bot, Sup). "
            "Control+Shift+C ou NVDA+Shift+C: Detalhes da seleção de campeões. "
            "Control+Shift+L ou NVDA+Shift+L: Status global do cliente e conexão. "
            "Control+Shift+E ou NVDA+Shift+E: Rotas dos inimigos deduzidas (2 toques: feitiços). "
            "Control+Shift+M ou NVDA+Shift+M: Histórico de chat e pings (2 toques: varredura imediata). "
            "Control+Shift+F7: Alternar leitura automática de pings. "
            "Control+Shift+N ou NVDA+Shift+N: Análise do Minimapa (2 toques: detalhado). "
            "Control+Shift+F8: Alternar alerta automático de gank. "
            "Durante a partida 3D: H (Vida/Recursos), K (KDA e CS), I (Itens e Ouro), U (Habilidades), O (Inimigos Vivos/Mortos), T (Tempo de Jogo), N (Minimapa), M (Chat e Pings)."
        )
        ui.message(help_text)

    @script(
        description="Foca e restaura em tela cheia a janela da partida do League of Legends.",
        gestures=["kb:NVDA+shift+w"]
    )
    def script_focusGameWindow(self, gesture):
        nav = getattr(self, "tactical_navigator", None)
        scanner = getattr(self, "minimap_scanner", None) or (nav.scanner if nav else None)
        hwnd = scanner.find_league_game_window() if scanner else None
        if not hwnd:
            try:
                import ctypes
                from ctypes import wintypes
                user32 = ctypes.windll.user32
                WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
                def enum_cb(h, lp):
                    nonlocal hwnd
                    cls = ctypes.create_unicode_buffer(256)
                    user32.GetClassNameW(h, cls, 256)
                    if cls.value == "RiotWindowClass":
                        hwnd = h
                        return False
                    return True
                user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
            except Exception:
                pass

        if hwnd:
            try:
                from lol_lib.tactical_navigator import force_restore_and_focus
            except Exception:
                try:
                    from lib.tactical_navigator import force_restore_and_focus
                except Exception:
                    force_restore_and_focus = None
            if force_restore_and_focus:
                force_restore_and_focus(hwnd)
            else:
                ctypes.windll.user32.ShowWindow(hwnd, 9)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
            try:
                tones.beep(880, 80)
                tones.beep(1175, 120)
            except Exception:
                pass
            ui.message("Janela da partida do League of Legends focada e restaurada em tela cheia!")
        else:
            ui.message("Janela da partida do League of Legends não encontrada.")


