# -*- coding: utf-8 -*-
"""
Módulo de Aplicativo NVDA para o League of Legends (LeagueClientUx.exe e League of Legends.exe).
Opera tanto no cliente pré-jogo (LCU) quanto durante a partida 3D ao vivo (Live Client Data API 127.0.0.1:2999):
- F6 para aceitar partida encontrada instantaneamente.
- Leitura estruturada da seleção de campeões (fase, campeões do time, cronômetro).
- Leitura de mensagens do chat do time e do saguão.
- Consultas durante a partida ao vivo: Vida e Recursos (H), Placar/KDA (K), Itens (I), Habilidades (U), Inimigos Vivos/Mortos (O) e Tempo de Jogo (T).
"""

import os
import sys
import appModuleHandler
import controlTypes
import ui
import tones
import NVDAObjects
from NVDAObjects import NVDAObject
from scriptHandler import script, getLastScriptRepeatCount
from logHandler import log

_addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_lol_lib_dir = os.path.join(_addon_dir, "lol_lib")
if _addon_dir not in sys.path:
    sys.path.insert(0, _addon_dir)
if _lol_lib_dir not in sys.path:
    sys.path.insert(0, _lol_lib_dir)

try:
    import wx
    import gui
except Exception:
    wx = None
    gui = None

try:
    from lol_lib.riot_api_helper import (
        get_league_client_lockfile,
        get_lcu_gameflow_phase,
        get_lcu_ready_check,
        accept_lcu_match,
        get_lcu_champ_select,
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
        format_champion_display_name,
        get_lcu_chat_messages,
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
        get_live_game_stats,
        get_live_enemy_lane_assignments,
        format_scoreboard_summary,
        format_champion_stats_summary,
        format_objectives_summary,
        format_enemies_summary
    )
except Exception:
    try:
        from riot_api_helper import (
            get_league_client_lockfile,
            get_lcu_gameflow_phase,
            get_lcu_ready_check,
            accept_lcu_match,
            get_lcu_champ_select,
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
            format_champion_display_name,
            get_lcu_chat_messages,
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
            get_live_game_stats,
            get_live_enemy_lane_assignments,
            format_scoreboard_summary,
            format_champion_stats_summary,
            format_objectives_summary,
            format_enemies_summary
        )
    except Exception:
        try:
            from lib.riot_api_helper import (
                get_league_client_lockfile,
                get_lcu_gameflow_phase,
                get_lcu_ready_check,
                accept_lcu_match,
                get_lcu_champ_select,
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
                format_champion_display_name,
                get_lcu_chat_messages,
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
                get_live_game_stats,
                get_live_enemy_lane_assignments,
                format_scoreboard_summary,
                format_champion_stats_summary,
                format_objectives_summary,
                format_enemies_summary
            )
        except Exception as e:
            log.error(f"lolAccessibility: Falha ao importar riot_api_helper em leagueclient: {e}")
            get_league_client_lockfile = lambda: None
            get_lcu_gameflow_phase = lambda: None
            get_lcu_ready_check = lambda: None
            accept_lcu_match = lambda: False
            get_lcu_champ_select = lambda: None
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
            format_champion_display_name = lambda c: c.get("name", "") if isinstance(c, dict) else str(c)
            get_lcu_chat_messages = lambda: []
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
            get_live_game_stats = lambda: None
            get_live_enemy_lane_assignments = lambda: None
            format_scoreboard_summary = lambda l=None: "Placar indisponível"
            format_champion_stats_summary = lambda l=None: "Stats indisponíveis"
            format_objectives_summary = lambda l=None: "Objetivos indisponíveis"
            format_enemies_summary = lambda l=None: "Inimigos indisponíveis"

try:
    from lol_lib.chat_reader import LoLChatReader
except Exception:
    try:
        from chat_reader import LoLChatReader
    except Exception:
        try:
            from lib.chat_reader import LoLChatReader
        except Exception:
            LoLChatReader = None

try:
    from lol_lib.minimap_scanner import LoLMinimapScanner
except Exception:
    try:
        from minimap_scanner import LoLMinimapScanner
    except Exception:
        try:
            from lib.minimap_scanner import LoLMinimapScanner
        except Exception:
            LoLMinimapScanner = None

try:
    from lol_lib.spatial_audio import get_spatial_audio_player, generate_pcm_stereo_tone
except Exception:
    try:
        from spatial_audio import get_spatial_audio_player, generate_pcm_stereo_tone
    except Exception:
        try:
            from lib.spatial_audio import get_spatial_audio_player, generate_pcm_stereo_tone
        except Exception:
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
        except Exception:
            LoLShopAssistant = None

try:
    from lol_lib.combat_status import LoLCombatStatus
except Exception:
    try:
        from combat_status import LoLCombatStatus
    except Exception:
        try:
            from lib.combat_status import LoLCombatStatus
        except Exception:
            LoLCombatStatus = None

try:
    from lol_lib.tactical_navigator import get_tactical_navigator
except Exception:
    try:
        from tactical_navigator import get_tactical_navigator
    except Exception:
        try:
            from lib.tactical_navigator import get_tactical_navigator
        except Exception:
            get_tactical_navigator = lambda: None




def prompt_champion_dialog(callback, is_ban=False):
    """Abre lista acessível (caixa de seleção) com os campeões disponíveis para escolha ou banimento."""
    if not wx:
        return False
    def _run():
        title = "Banir Campeão" if is_ban else "Escolher e Travar Campeão"
        champs = get_lcu_available_champions(is_ban=is_ban)
        if not champs:
            # Fallback para digitação caso o cliente não retorne a lista
            prompt = (
                "Digite o nome do campeão para banir (ex: Yasuo, Zed, Blitz):"
                if is_ban else
                "Digite o nome do campeão para escolher e travar (ex: Malphite, Sett, Caitlyn):"
            )
            style = wx.OK | wx.CANCEL | wx.CENTRE | wx.STAY_ON_TOP
            dlg = wx.TextEntryDialog(None, prompt, title, "", style=style)
            try:
                dlg.Raise()
                dlg.SetFocus()
            except Exception:
                pass
            if dlg.ShowModal() == wx.ID_OK:
                val = dlg.GetValue().strip()
                dlg.Destroy()
                if val:
                    callback(val)
            else:
                dlg.Destroy()
            return

        # Ordenar alfabeticamente pelo nome
        champs_sorted = sorted(champs, key=lambda c: c.get("name", "").lower())
        choices = []
        champ_names = []

        for c in champs_sorted:
            display_label = format_champion_display_name(c)
            choices.append(display_label)
            champ_names.append(c.get("name", ""))

        choices.append("Digitar outro campeão manualmente...")
        champ_names.append("__CUSTOM__")

        prompt_msg = (
            "Selecione com as setas o campeão para banir e tecle Enter:"
            if is_ban else
            f"Selecione com as setas o campeão para travar ({len(champs)} disponíveis nesta conta):"
        )

        style = wx.OK | wx.CANCEL | wx.CENTRE | wx.STAY_ON_TOP
        dlg = wx.SingleChoiceDialog(None, prompt_msg, title, choices, style=style)
        try:
            dlg.Raise()
            dlg.SetFocus()
        except Exception:
            pass

        try:
            tones.beep(1046, 100)
            tones.beep(1318, 120)
        except Exception:
            pass

        if dlg.ShowModal() == wx.ID_OK:
            sel_idx = dlg.GetSelection()
            dlg.Destroy()
            if 0 <= sel_idx < len(champ_names):
                target = champ_names[sel_idx]
                if target == "__CUSTOM__":
                    custom_prompt = (
                        "Digite o nome do campeão para banir (ex: Yasuo, Zed, Blitz):"
                        if is_ban else
                        "Digite o nome do campeão para escolher e travar:"
                    )
                    cdlg = wx.TextEntryDialog(None, custom_prompt, title, "", style=style)
                    try:
                        cdlg.Raise()
                        cdlg.SetFocus()
                    except Exception:
                        pass
                    if cdlg.ShowModal() == wx.ID_OK:
                        c_val = cdlg.GetValue().strip()
                        cdlg.Destroy()
                        if c_val:
                            callback(c_val)
                    else:
                        cdlg.Destroy()
                else:
                    callback(target)
        else:
            dlg.Destroy()

    wx.CallAfter(_run)
    return True


def prompt_shop_dialog(callback, current_gold, can_buy_now, in_progress):
    """Abre diálogo acessível para compra rápida de itens na Loja do LoL."""
    if not wx:
        return False
    def _run():
        choices = []
        item_names = []

        if can_buy_now:
            for b in can_buy_now:
                choices.append(f"[COMPRAR AGORA] {b['name']} - Custo: {b['cost_to_finish']} ouro (Total: {b['total_price']})")
                item_names.append(b['name'])

        if in_progress:
            for p in in_progress[:6]:
                choices.append(f"[FALTAM {p['gold_needed']} OURO] {p['name']} - Preço restante: {p['cost_to_finish']}")
                item_names.append(p['name'])

        choices.append("Digitar outro item manualmente...")
        item_names.append("__CUSTOM__")

        style = wx.OK | wx.CANCEL | wx.CENTRE | wx.STAY_ON_TOP
        dlg = wx.SingleChoiceDialog(
            None,
            f"Você tem {int(current_gold)} de ouro. Selecione o item para comprar:",
            "Loja Acessível do League of Legends",
            choices,
            style=style
        )
        try:
            dlg.Raise()
            dlg.SetFocus()
        except Exception:
            pass

        try:
            tones.beep(880, 80)
            tones.beep(1175, 120)
        except Exception:
            pass

        if dlg.ShowModal() == wx.ID_OK:
            sel_idx = dlg.GetSelection()
            dlg.Destroy()
            if 0 <= sel_idx < len(item_names):
                target = item_names[sel_idx]
                if target == "__CUSTOM__":
                    cdlg = wx.TextEntryDialog(
                        None,
                        "Digite o nome do item que deseja comprar (ex: Botas, Gume, Trindade):",
                        "Comprar Item na Loja",
                        "",
                        style=style
                    )
                    try:
                        cdlg.Raise()
                        cdlg.SetFocus()
                    except Exception:
                        pass
                    if cdlg.ShowModal() == wx.ID_OK:
                        c_val = cdlg.GetValue().strip()
                        cdlg.Destroy()
                        if c_val:
                            callback(c_val)
                    else:
                        cdlg.Destroy()
                else:
                    callback(target)
        else:
            dlg.Destroy()

    wx.CallAfter(_run)
    return True


def prompt_aram_bench_dialog(bench_items, callback):
    """Abre diálogo acessível para troca com campeão do banco de reservas no ARAM."""
    if not wx:
        return False
    def _run():
        choices = [f"{i+1}: {b['name']}" for i, b in enumerate(bench_items)]
        style = wx.OK | wx.CANCEL | wx.CENTRE | wx.STAY_ON_TOP
        dlg = wx.SingleChoiceDialog(
            None,
            "Selecione o campeão do banco de reservas para trocar:",
            "Banco de Reservas do ARAM",
            choices,
            style=style
        )
        try:
            dlg.Raise()
            dlg.SetFocus()
        except Exception:
            pass
        try:
            tones.beep(1046, 100)
        except Exception:
            pass
        if dlg.ShowModal() == wx.ID_OK:
            sel = dlg.GetSelection()
            dlg.Destroy()
            if 0 <= sel < len(bench_items):
                callback(bench_items[sel]["id"])
        else:
            dlg.Destroy()
    wx.CallAfter(_run)
    return True


def prompt_lobby_roles_dialog(callback):
    """Abre diálogo acessível para escolha de rotas (primária e secundária) no saguão."""
    if not wx:
        return False
    def _run():
        roles = [
            ("TOP", "Topo (Top)"),
            ("JUNGLE", "Selva (Jungle)"),
            ("MIDDLE", "Meio (Mid)"),
            ("BOTTOM", "Atirador (Adc/Bot)"),
            ("UTILITY", "Suporte (Support)"),
            ("FILL", "Preencher (Qualquer rota)"),
        ]
        choices = [r[1] for r in roles]
        style = wx.OK | wx.CANCEL | wx.CENTRE | wx.STAY_ON_TOP
        dlg1 = wx.SingleChoiceDialog(
            None,
            "Escolha sua rota primária para a fila:",
            "Preferência de Rota Primária",
            choices,
            style=style
        )
        try:
            dlg1.Raise()
            dlg1.SetFocus()
        except Exception:
            pass
        try:
            tones.beep(1046, 100)
        except Exception:
            pass
        if dlg1.ShowModal() == wx.ID_OK:
            idx1 = dlg1.GetSelection()
            dlg1.Destroy()
            p1 = roles[idx1][0]

            sec_roles = [r for r in roles if r[0] != p1]
            sec_choices = [r[1] for r in sec_roles]
            dlg2 = wx.SingleChoiceDialog(
                None,
                "Escolha sua rota secundária para a fila:",
                "Preferência de Rota Secundária",
                sec_choices,
                style=style
            )
            try:
                dlg2.Raise()
                dlg2.SetFocus()
            except Exception:
                pass
            p2 = "UNSELECTED"
            if dlg2.ShowModal() == wx.ID_OK:
                idx2 = dlg2.GetSelection()
                if 0 <= idx2 < len(sec_roles):
                    p2 = sec_roles[idx2][0]
            dlg2.Destroy()
            callback(p1, p2)
        else:
            dlg1.Destroy()
    wx.CallAfter(_run)
    return True


def prompt_navigation_dialog(callback, team="ORDER"):
    """Abre diálogo acessível para seleção e movimentação para waypoints do mapa."""
    if not wx:
        return False
    def _run():
        options = [
            ("MID", "Rota do Meio (Centro da Rota)"),
            ("MID_T1", "Rota do Meio (Torre Aliada T1)"),
            ("TOP", "Rota Superior (Centro da Rota)"),
            ("TOP_T1", "Rota Superior (Torre Aliada T1)"),
            ("BOT", "Rota Inferior (Centro da Rota)"),
            ("BOT_T1", "Rota Inferior (Torre Aliada T1)"),
            ("BASE", "Base Aliada (Fonte Segura)"),
            ("DRAGON", "Covil do Dragão"),
            ("BARON", "Covil do Barão"),
        ]
        choices = [label for key, label in options]
        keys = [key for key, label in options]

        style = wx.OK | wx.CANCEL | wx.CENTRE | wx.STAY_ON_TOP
        side_name = "Azul" if team == "ORDER" else "Vermelho"
        dlg = wx.SingleChoiceDialog(
            None,
            f"Seu time é {side_name}. Selecione para onde deseja andar:",
            "Navegador de Rotas e Waypoints - League of Legends",
            choices,
            style=style
        )
        try:
            dlg.Raise()
            dlg.SetFocus()
        except Exception:
            pass

        try:
            tones.beep(587, 80)
            tones.beep(880, 100)
        except Exception:
            pass

        if dlg.ShowModal() == wx.ID_OK:
            sel_idx = dlg.GetSelection()
            dlg.Destroy()
            if 0 <= sel_idx < len(keys):
                callback(keys[sel_idx])
        else:
            dlg.Destroy()

    wx.CallAfter(_run)
    return True



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
    from NVDAObjects.IAccessible.chromium import ChromeVBuf, ChromeVBufTextInfo, Document as ChromiumDocument
except Exception:
    try:
        from virtualBuffers.gecko_ia2 import GeckoVBuf as ChromeVBuf, GeckoVBufTextInfo as ChromeVBufTextInfo
    except Exception:
        ChromeVBuf = object
        ChromeVBufTextInfo = object
    ChromiumDocument = NVDAObjects.NVDAObject


# ============================================================================
# CONSTANTES DE CONTROLE
# ============================================================================

_Role = getattr(controlTypes, "Role", None)
ROLE_TAB = getattr(_Role, "TAB", getattr(controlTypes, "ROLE_TAB", 37))
ROLE_BUTTON = getattr(_Role, "BUTTON", getattr(controlTypes, "ROLE_BUTTON", 9))
ROLE_ANIMATION = getattr(_Role, "ANIMATION", getattr(controlTypes, "ROLE_ANIMATION", 54))
ROLE_DOCUMENT = getattr(_Role, "DOCUMENT", getattr(controlTypes, "ROLE_DOCUMENT", 53))
ROLE_PANE = getattr(_Role, "PANE", getattr(controlTypes, "ROLE_PANE", 16))


def get_element_identifiers(obj):
    """Retorna (id, class_name, tag) combinando UIA e IA2Attributes."""
    auto_id = getattr(obj, "UIAAutomationId", "") or ""
    class_name = getattr(obj, "UIAClassName", "") or getattr(obj, "className", "") or ""
    tag = ""

    ia2 = getattr(obj, "IA2Attributes", None)
    if ia2:
        if isinstance(ia2, dict):
            auto_id = auto_id or ia2.get("id", "") or ia2.get("data-testid", "")
            class_name = class_name or ia2.get("class", "")
            tag = ia2.get("tag", "")
        elif isinstance(ia2, str):
            for part in ia2.split(";"):
                if ":" in part:
                    k, v = part.split(":", 1)
                    k = k.strip().lower()
                    v = v.strip()
                    if k in ("id", "data-testid") and not auto_id:
                        auto_id = v
                    elif k == "class" and not class_name:
                        class_name = v
                    elif k == "tag" and not tag:
                        tag = v

    return (auto_id or "").lower(), (class_name or "").lower(), (tag or "").lower()


# ============================================================================
# MAPAS E OVERLAYS DO LEAGUE CLIENT (LCU)
# ============================================================================

KNOWN_LEAGUE_TABS = {
    "play": "Jogar",
    "home": "Início",
    "tft": "Teamfight Tactics",
    "clash": "Torneios Clash",
    "collection": "Coleção de Campeões e Skins",
    "loot": "Espólio e Criação Hextec",
    "store": "Loja do LoL",
    "profile": "Meu Perfil e Histórico",
    "ranked": "Ranqueada e Classificação",
    "overview": "Visão Geral",
}


class LeagueChromeVBufTextInfo(ChromeVBufTextInfo):
    """Substitui a extração de texto do buffer virtual no cliente do League of Legends."""
    def getTextWithFields(self, formatConfig=None):
        fields = super().getTextWithFields(formatConfig=formatConfig)
        if not shared_cleaner:
            return fields
        cleaned = []
        for item in fields:
            if isinstance(item, str):
                c = shared_cleaner.clean_text_block(item)
                if c:
                    cleaned.append(c)
            else:
                cleaned.append(item)
        return cleaned

    def _getTextRange(self, startOffset, endOffset):
        raw = super()._getTextRange(startOffset, endOffset)
        if shared_cleaner and raw:
            return shared_cleaner.clean_text_block(raw)
        return raw

    def _get_clipboardText(self):
        raw = super()._get_clipboardText()
        if shared_cleaner and raw:
            return shared_cleaner.clean_text_block(raw)
        return raw


class LeagueChromeVBuf(ChromeVBuf):
    """Buffer virtual customizado para a interface Chromium do League of Legends."""
    TextInfo = LeagueChromeVBufTextInfo


class LeagueDocument(NVDAObjects.NVDAObject):
    """Documento do League Client."""
    def _get_treeInterceptorClass(self):
        return LeagueChromeVBuf


class LeagueDecorativeAnimation(NVDAObjects.NVDAObject):
    """Silencia animações e SVGs decorativos no cliente do LoL."""
    def _get_presentationType(self):
        return getattr(self, "presType_layout", "layout")

    def _get_name(self):
        return ""

    def _get_role(self):
        return getattr(controlTypes.Role, "UNKNOWN", 0)

    def _get_roleText(self):
        return ""

    def _get_shouldAllowIAccessibleFocusEvent(self):
        return False


class LeagueCustomComponent(NVDAObjects.NVDAObject):
    """Normaliza componentes personalizados lol-uikit para o leitor de telas."""
    def _get_name(self):
        raw_name = super().name or ""
        if raw_name.startswith("lol-uikit-"):
            return "Elemento de interface"
        return raw_name


class LeagueSmartTab(NVDAObjects.NVDAObject):
    """Nomeia guias e abas do cliente do League of Legends."""
    def _get_name(self):
        raw_name = (super().name or "").strip()
        if raw_name and raw_name.lower() not in ("animation", "lottie", "tab", "guia", "button", "botão") and not raw_name.isdigit():
            return raw_name
        auto_id, class_name, tag = get_element_identifiers(self)
        for k, v in KNOWN_LEAGUE_TABS.items():
            if k in auto_id or k in class_name:
                return v
        try:
            for child in super().children:
                c_name = (child.name or "").strip()
                if c_name and c_name.lower() not in ("animation", "lottie", "graphic", "imagem"):
                    return c_name
        except Exception:
            pass
        return raw_name or "Guia do LoL"

    def _get_firstChild(self):
        return None

    def _get_children(self):
        return []

    def _get_childCount(self):
        return 0


class LeagueSmartButton(NVDAObjects.NVDAObject):
    """Nomeia botões sem rótulo do cliente do League of Legends."""
    def _get_name(self):
        raw_name = (super().name or "").strip()
        if raw_name and raw_name.lower() not in ("animation", "lottie", "button", "botão", "graphic", "imagem"):
            return raw_name
        auto_id, class_name, tag = get_element_identifiers(self)
        target = f"{auto_id} {class_name}"
        if "play" in target:
            return "Jogar"
        elif "close" in target:
            return "Fechar janela"
        elif "min" in target:
            return "Minimizar janela"
        elif "settings" in target or "gear" in target:
            return "Configurações do LoL"
        elif "notifications" in target or "bell" in target:
            return "Notificações"
        elif "friends" in target or "chat" in target:
            return "Amigos e Bate-papo"
        try:
            for child in super().children:
                c_name = (child.name or "").strip()
                if c_name and c_name.lower() not in ("animation", "lottie", "graphic", "imagem"):
                    return c_name
        except Exception:
            pass
        return raw_name or "Botão"

    def _get_firstChild(self):
        raw = self.name
        if raw and raw.lower() not in ("botão", "button"):
            return None
        return super().firstChild

    def _get_children(self):
        raw = self.name
        if raw and raw.lower() not in ("botão", "button"):
            return []
        return super().children


class AppModule(appModuleHandler.AppModule):
    """Módulo de acessibilidade para League Client e Game Client (LoL)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._chat_reader = LoLChatReader() if LoLChatReader else None
        self._minimap_scanner = LoLMinimapScanner() if LoLMinimapScanner else None
        self._spatial_player = get_spatial_audio_player() if get_spatial_audio_player else None
        self._spatial_radar_enabled = True
        self._shop_assistant = LoLShopAssistant() if LoLShopAssistant else None
        self._combat_status = LoLCombatStatus() if LoLCombatStatus else None
        self._tactical_navigator = get_tactical_navigator() if get_tactical_navigator else None
        log.info("lolAccessibility: AppModule para LeagueClient/GameClient inicializado.")


    def chooseNVDAObjectOverlayClasses(self, obj, clsList):
        try:
            role = getattr(obj, "role", None)
            auto_id, class_name, tag = get_element_identifiers(obj)
            window_class = (getattr(obj, "windowClassName", "") or "").lower()

            if role in (ROLE_DOCUMENT, ROLE_PANE) and (tag in ("#document", "document") or "chrome_renderwidgethosthwnd" in window_class):
                clsList.insert(0, LeagueDocument)
            elif role == ROLE_TAB or "tab" in class_name or "tab" in auto_id:
                clsList.insert(0, LeagueSmartTab)
            elif role == ROLE_BUTTON or "button" in class_name:
                clsList.insert(0, LeagueSmartButton)
            elif role == ROLE_ANIMATION or "animation" in class_name:
                clsList.insert(0, LeagueDecorativeAnimation)
            elif (obj.name or "").lower().startswith("lol-uikit-") or "lol-uikit" in class_name:
                clsList.insert(0, LeagueCustomComponent)
        except Exception as e:
            log.debug(f"lolAccessibility: League chooseNVDAObjectOverlayClasses erro: {e}")

        super().chooseNVDAObjectOverlayClasses(obj, clsList)

    # ========================================================================
    # ATALHOS NO LEAGUE CLIENT (PRÉ-JOGO / LOBBY / SELEÇÃO DE CAMPEÕES)
    # ========================================================================

    @script(
        description="Aceita a partida encontrada (Ready Check) no League of Legends.",
        gestures=["kb:f6", "kb:NVDA+f6"]
    )
    def script_acceptMatch(self, gesture):
        """Aceita a partida encontrada imediatamente via API LCU."""
        ok = accept_lcu_match()
        if ok:
            tones.beep(1320, 150)
            ui.message("Partida aceita com sucesso!")
        else:
            ui.message("Nenhum aviso de partida para aceitar no momento.")

    @script(
        description="Alterna o modo de aceitação automática de partidas.",
        gestures=["kb:NVDA+shift+f6", "kb:control+shift+f6"]
    )
    def script_toggleAutoAccept(self, gesture):
        globalPlugin = None
        try:
            import globalPluginHandler
            for plugin in globalPluginHandler.runningPlugins:
                if "lol_accessibility_bridge" in plugin.__module__:
                    globalPlugin = plugin
                    break
        except Exception:
            pass

        if globalPlugin:
            globalPlugin.script_toggleAutoAccept(gesture)
        else:
            ui.message("Serviço de aceitação automática indisponível.")

    @script(
        description="Anuncia informações detalhadas da Seleção de Campeões (tempo restante, campeão, rota, aliados e banco ARAM).",
        gestures=["kb:NVDA+shift+c", "kb:control+shift+c"]
    )
    def script_champSelectInfo(self, gesture):
        detailed = get_lcu_champ_select_detailed()
        if not detailed:
            ui.message("Seleção de campeões não está ativa no momento.")
            return

        parts = []
        parts.append(f"{detailed['time_left_sec']} segundos restantes ({detailed['phase']})")

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

    def _open_in_game_shop(self):
        assistant = getattr(self, "_shop_assistant", None)
        if not assistant:
            ui.message("Assistente de loja indisponível.")
            return

        active = get_live_active_player() or {}
        cur_gold = active.get("currentGold", 0.0)
        players = get_live_player_list() or []
        summoner = active.get("summonerName", "")
        inv = []
        for p in players:
            if p.get("summonerName") == summoner:
                inv = p.get("items", [])
                break

        analysis = assistant.analyze_inventory_and_gold(cur_gold, inv)
        speech_sum = assistant.format_shop_speech(analysis)

        def _on_buy_item(item_name):
            ui.message(f"Comprando {item_name} na loja...")
            ok = assistant.buy_item_via_keys(item_name)
            if ok:
                try:
                    tones.beep(1046, 100)
                    tones.beep(1318, 120)
                except Exception:
                    pass
                ui.message(f"Comando de compra de {item_name} enviado!")
            else:
                ui.message(f"Falha ao enviar comando de compra de {item_name}.")

        opened = prompt_shop_dialog(_on_buy_item, cur_gold, analysis["can_buy_now"], analysis["in_progress"])
        if not opened:
            ui.message(speech_sum)

    @script(
        description="Abre o assistente acessível de loja na partida ou escolha de campeão na seleção.",
        gestures=["kb:NVDA+shift+p", "kb:control+shift+p"]
    )
    def script_pickChampion(self, gesture):
        if is_live_game_active():
            self._open_in_game_shop()
            return

        detailed = get_lcu_champ_select_detailed()
        if not detailed:
            ui.message("A seleção de campeões não está ativa no momento.")
            return

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

        opened = prompt_champion_dialog(_do_pick, is_ban=False)
        if not opened:
            ui.message("Interface gráfica de diálogo não disponível.")

    @script(
        description="Gerencia o banco de reservas no ARAM ou abre o assistente para banir campeão.",
        gestures=["kb:NVDA+shift+b", "kb:control+shift+b"]
    )
    def script_banOrBenchChampion(self, gesture):
        detailed = get_lcu_champ_select_detailed()
        if not detailed:
            ui.message("Seleção de campeões ou banco ARAM não estão ativos no momento.")
            return

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

            opened = prompt_aram_bench_dialog(bench, _do_swap)
            if not opened:
                bench_names = [f"{i+1}: {b['name']}" for i, b in enumerate(bench)]
                ui.message("Banco ARAM: " + ", ".join(bench_names))
        else:
            def _do_ban(champ_name):
                ok, msg, cname = pick_or_ban_champion(champ_name, is_ban=True, lock_in=True)
                if ok:
                    try:
                        tones.beep(880, 120)
                    except Exception:
                        pass
                ui.message(msg)

            opened = prompt_champion_dialog(_do_ban, is_ban=True)
            if not opened:
                ui.message("Interface gráfica de diálogo não disponível.")

    @script(
        description="Rola o dado no ARAM para sortear outro campeão ou lê o download no Riot Client.",
        gestures=["kb:NVDA+shift+d", "kb:control+shift+d"]
    )
    def script_aramReroll(self, gesture):
        phase = get_lcu_gameflow_phase()
        if phase == "ChampSelect":
            detailed = get_lcu_champ_select_detailed()
            if detailed and detailed.get("bench_enabled"):
                ok, msg, dice = reroll_lcu_aram()
                if ok:
                    try:
                        tones.beep(987, 80)
                        tones.beep(1318, 120)
                    except Exception:
                        pass
                ui.message(msg)
                return

        self.script_announceStatus(gesture)

    @script(
        description="Importa a melhor página de runas recomendadas e configura os feitiços de invocador.",
        gestures=["kb:NVDA+shift+r", "kb:control+shift+r"]
    )
    def script_importRunes(self, gesture):
        ok, msg = import_recommended_runes_and_spells()
        if ok:
            try:
                tones.beep(1175, 120)
            except Exception:
                pass
        ui.message(msg)

    @script(
        description="Configura acessivelmente suas preferências de rotas no saguão (Top, Jungle, Mid, Bot, Sup).",
        gestures=["kb:NVDA+shift+o", "kb:control+shift+o"]
    )
    def script_setLobbyPositions(self, gesture):
        phase = get_lcu_gameflow_phase()
        if phase != "Lobby":
            if is_live_game_active():
                self.script_queryEnemies(gesture)
                return
            ui.message("Você precisa estar em um saguão (Lobby) para configurar preferências de rota.")
            return

        def _do_set_roles(p1, p2):
            ok, msg = set_lcu_lobby_positions(p1, p2)
            if ok:
                try:
                    tones.beep(1046, 120)
                except Exception:
                    pass
            ui.message(msg)

        opened = prompt_lobby_roles_dialog(_do_set_roles)
        if not opened:
            ui.message("Interface gráfica de diálogo não disponível.")

    @script(
        description="Anuncia o status detalhado atual do League of Legends e do saguão.",
        gestures=["kb:NVDA+shift+l", "kb:control+shift+l"]
    )
    def script_announceStatus(self, gesture):
        if is_live_game_active():
            stats = get_live_game_stats()
            gtime = int(stats.get("gameTime", 0)) if stats else 0
            mins, secs = divmod(gtime, 60)
            ui.message(f"Partida 3D em andamento. Tempo de jogo: {mins} minutos e {secs} segundos.")
            return

        lock = get_league_client_lockfile()
        if not lock:
            ui.message("League of Legends não detectado.")
            return

        phase = get_lcu_gameflow_phase()
        sum_info = get_lcu_summoner_info()
        sum_str = f" ({sum_info['full_tag']}, Nível {sum_info['level']})" if sum_info else ""

        if phase == "ReadyCheck":
            ui.message(f"Partida encontrada! Pressione F6 para aceitar!{sum_str}")
        elif phase == "ChampSelect":
            ui.message(f"Na Seleção de Campeões! Pressione Control+Shift+C para detalhes.{sum_str}")
        elif phase == "Matchmaking":
            search = get_lcu_search_state()
            if search and search.get("is_searching"):
                tiq = search.get("time_in_queue", 0)
                m, s = divmod(tiq, 60)
                est = search.get("estimated_time", 0)
                em, es = divmod(est, 60)
                est_str = f", estimado: {em}m {es}s" if est > 0 else ""
                ui.message(f"Buscando partida... Tempo na fila: {m} minutos e {s} segundos{est_str}.{sum_str}")
            else:
                ui.message(f"Buscando partida...{sum_str}")
        elif phase == "Lobby":
            lobby = get_lcu_lobby_info()
            penalty = get_lcu_queue_penalty()
            pen_str = f" [Penalidade ativa: resta {penalty['time_str']}]" if penalty and penalty.get("has_penalty") else ""
            if lobby:
                mode = lobby.get("game_mode", "LoL")
                count = lobby.get("members_count", 1)
                leader = " (Você é o líder)" if lobby.get("is_leader") else ""
                ui.message(f"No Saguão de {mode}. {count} jogador(es) no grupo{leader}.{pen_str} Pressione Control+Shift+J para iniciar busca.{sum_str}")
            else:
                ui.message(f"No Saguão do jogo.{pen_str}{sum_str}")
        elif phase == "InProgress":
            ui.message(f"Partida carregando ou em andamento.{sum_str}")
        else:
            ui.message(f"League of Legends conectado no Início / Hub principal.{sum_str}")

    @script(
        description="Anuncia o perfil do invocador (nome, nível, progresso de XP e classificação ranqueada).",
        gestures=["kb:NVDA+shift+s", "kb:control+shift+s"]
    )
    def script_announceSummonerProfile(self, gesture):
        sum_info = get_lcu_summoner_info()
        if not sum_info:
            ui.message("Dados do invocador indisponíveis no momento.")
            return

        ranked = get_lcu_ranked_stats()
        name = sum_info["full_tag"]
        lvl = sum_info["level"]
        xp_pct = sum_info["xp_percent"]
        xp_cur = sum_info["xp_current"]
        xp_need = sum_info["xp_needed"]
        
        msg = f"Invocador: {name}, Nível {lvl} ({xp_cur} de {xp_need} XP, {xp_pct}%). Ranqueada: {ranked}."
        ui.message(msg)

    @script(
        description="Executa a ação principal no cliente (dispensa modais, aceita termos, inicia busca ou foca botão de jogar).",
        gestures=["kb:NVDA+shift+j", "kb:control+shift+j"]
    )
    def script_focusActionButton(self, gesture):
        # 1. Se houver notificações modais pendentes (ex: Pacto da Comunidade, temporadas), descarta via API
        dismissed = dismiss_lcu_notifications()
        if dismissed > 0:
            tones.beep(880, 100)
            ui.message(f"Termos e avisos modais ({dismissed}) confirmados com sucesso!")
            return

        # 2. Se estiver em Matchmaking, cancela a busca
        phase = get_lcu_gameflow_phase()
        if phase == "Matchmaking":
            ok = cancel_lcu_matchmaking()
            if ok:
                tones.beep(440, 100)
                ui.message("Busca de partida cancelada.")
                return

        # 3. Se estiver em Saguão (Lobby), inicia a busca de partida se for o líder
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
                    ui.message("Iniciando busca de partida!")
                    return
                else:
                    penalty = get_lcu_queue_penalty()
                    if penalty and penalty.get("has_penalty"):
                        tones.beep(330, 200)
                        ui.message(penalty["text"])
                        return
                    else:
                        ui.message("Não foi possível iniciar a busca. Verifique se há restrições ou termos pendentes.")
                        return

        # 4. Vasculha a árvore de acessibilidade da tela atual por botões chave
        target = None
        try:
            fg = api.getForegroundObject()
            if fg:
                search_targets = [
                    "tô dentro", "to dentro", "vamos nessa", "jogar", "play", "encontrar partida",
                    "buscar partida", "confirmar", "aceitar", "continuar", "entendi", "fechar",
                    "começar", "comecar", "iniciar", "resgatar", "reivindicar", "reivindique", "próximo", "proximo"
                ]
                def find_btn(o, depth=0):
                    nonlocal target
                    if target or depth > 12:
                        return
                    name = (o.name or "").lower()
                    role = getattr(o, "role", None)
                    if role == ROLE_BUTTON or "button" in getattr(o, "className", "").lower():
                        for st in search_targets:
                            if st in name:
                                target = o
                                return
                    for c in getattr(o, "children", []):
                        find_btn(c, depth + 1)
                find_btn(fg)

                if target:
                    target.setFocus()
                    try:
                        target.doDefaultAction()
                    except Exception:
                        pass
                    tones.beep(1046, 80)
                    ui.message(f"Ação executada: {target.name}")
                    return
        except Exception as e:
            log.debug(f"lolAccessibility: Erro em focusActionButton: {e}")

        # 5. Se estiver no Hub (phase None) e nenhum botão foi focado, abre saguão padrão (Swiftplay Iniciante / ARAM / Tutoriais)
        if phase is None:
            for q_id in [880, 450, 2000, 2010, 2020]:
                ok = create_lcu_lobby(q_id)
                if ok:
                    tones.beep(880, 120)
                    ui.message("Saguão aberto com sucesso!")
                    return

        ui.message("Nenhuma ação principal pendente no momento.")

    @script(
        description="Dispensa e aceita todos os avisos, termos e caixas de diálogo do League of Legends.",
        gestures=["kb:NVDA+shift+escape", "kb:control+shift+escape"]
    )
    def script_dismissModals(self, gesture):
        count = dismiss_lcu_notifications()
        if count > 0:
            tones.beep(880, 120)
            ui.message(f"{count} diálogo(s) ou aviso(s) dispensados.")
        else:
            ui.message("Nenhum aviso ou diálogo pendente.")

    @script(
        description="Abre ou consulta o saguão de partida rápida (Iniciante / ARAM / Tutorial).",
        gestures=["kb:NVDA+shift+m", "kb:control+shift+m"]
    )
    def script_quickLobby(self, gesture):
        phase = get_lcu_gameflow_phase()
        if phase == "Lobby":
            lobby = get_lcu_lobby_info()
            mode = lobby.get("game_mode", "LoL") if lobby else "LoL"
            ui.message(f"Já em saguão de {mode}. Pressione Control+Shift+J para iniciar busca.")
            return

        ok = False
        for q_id in [880, 450, 2000, 2010, 2020]:
            if create_lcu_lobby(q_id):
                ok = True
                break
        if ok:
            tones.beep(987, 100)
            tones.beep(1318, 120)
            ui.message("Saguão criado com sucesso! Pressione Control+Shift+J para buscar partida.")
        else:
            ui.message("Não foi possível criar saguão no momento.")

    # ========================================================================
    # ATALHOS NA PARTIDA AO VIVO 3D (LIVE CLIENT DATA API)
    # ========================================================================

    @script(
        description="Consulta a Vida e Recursos atuais do jogador na partida.",
        gestures=["kb:h", "kb:control+shift+h"]
    )
    def script_queryHealth(self, gesture):
        if not is_live_game_active():
            gesture.send()
            return
        player = get_live_active_player()
        if not player:
            gesture.send()
            return
        stats = player.get("championStats") or player.get("champion_stats") or {}
        hp = int(stats.get("currentHealth") or stats.get("current_health") or 0)
        max_hp = int(stats.get("maxHealth") or stats.get("max_health") or 1)
        pct = int((hp / max_hp) * 100) if max_hp > 0 else 0
        res_type = (stats.get("resourceType") or stats.get("resource_type") or "MANA").capitalize()
        res_val = int(stats.get("resourceValue") or stats.get("resource_value") or 0)
        res_max = int(stats.get("resourceMax") or stats.get("resource_max") or 1)
        res_pct = int((res_val / res_max) * 100) if res_max > 0 else 0
        ui.message(f"Vida: {hp} de {max_hp} ({pct}%). {res_type}: {res_val} de {res_max} ({res_pct}%).")

    @script(
        description="Consulta o Placar e KDA do jogador na partida.",
        gestures=["kb:k", "kb:control+shift+k"]
    )
    def script_queryKDA(self, gesture):
        if not is_live_game_active():
            gesture.send()
            return
        player = get_live_active_player()
        if not player:
            gesture.send()
            return
        scores = player.get("scores") or {}
        k = scores.get("kills", 0)
        d = scores.get("deaths", 0)
        a = scores.get("assists", 0)
        cs = scores.get("creepScore") or scores.get("creep_score") or 0
        ui.message(f"KDA: {k} abates, {d} mortes, {a} assistências. Farm: {cs} tropas.")

    @script(
        description="Consulta os Itens comprados e Ouro atual.",
        gestures=["kb:i", "kb:control+shift+i"]
    )
    def script_queryItems(self, gesture):
        if not is_live_game_active():
            gesture.send()
            return
        player = get_live_active_player()
        if not player:
            gesture.send()
            return
        gold = int(player.get("currentGold") or player.get("current_gold") or 0)
        items = player.get("items", [])
        item_names = [it.get("displayName") or it.get("display_name") or "Item" for it in items if it.get("slot", 0) < 6 and (it.get("count", 0) > 0 or "count" not in it)]
        items_str = ", ".join(item_names) if item_names else "Nenhum item comprado"
        ui.message(f"Ouro: {gold}. Itens: {items_str}.")

    @script(
        description="Consulta as Habilidades e Nível do campeão.",
        gestures=["kb:u", "kb:control+shift+u"]
    )
    def script_queryAbilities(self, gesture):
        if not is_live_game_active():
            gesture.send()
            return
        abilities = get_live_active_player_abilities()
        player = get_live_active_player()
        lvl = player.get("level", 1) if player else 1
        champ = player.get("championName") or player.get("champion_name") or "Campeão" if player else "Campeão"
        if not abilities:
            ui.message(f"{champ}, Nível {lvl}.")
            return
        details = []
        for key in ["Q", "W", "E", "R"]:
            ab = abilities.get(key, {})
            ab_lvl = ab.get("abilityLevel") or ab.get("ability_level") or 0
            details.append(f"{key}: nível {ab_lvl}")
        ui.message(f"{champ} nível {lvl}. Habilidades: " + ", ".join(details))

    @script(
        description="Anuncia quais inimigos estão vivos ou mortos.",
        gestures=["kb:o", "kb:control+shift+o"]
    )
    def script_queryEnemies(self, gesture):
        if not is_live_game_active():
            gesture.send()
            return
        players = get_live_player_list()
        active = get_live_active_player()
        if not players or not active:
            gesture.send()
            return
        my_team = active.get("team", "ORDER")
        enemies = [p for p in players if p.get("team") != my_team]
        dead = [p.get("championName") or p.get("champion_name") or "Inimigo" for p in enemies if p.get("isDead", False) or p.get("is_dead", False)]
        alive = [p.get("championName") or p.get("champion_name") or "Inimigo" for p in enemies if not (p.get("isDead", False) or p.get("is_dead", False))]
        if not dead:
            ui.message(f"Todos os {len(enemies)} inimigos estão vivos.")
        else:
            ui.message(f"Inimigos mortos: {', '.join(dead)}. Vivos: {', '.join(alive)}.")

    @script(
        description="Consulta o Tempo de Jogo da partida.",
        gestures=["kb:t", "kb:control+shift+t"]
    )
    def script_queryGameTime(self, gesture):
        if not is_live_game_active():
            gesture.send()
            return
        stats = get_live_game_stats()
        if not stats:
            ui.message("Tempo de jogo indisponível.")
            return
        t = int(stats.get("gameTime") or stats.get("game_time") or 0)
        m = t // 60
        s = t % 60
        mode = stats.get("gameMode") or stats.get("game_mode") or "LoL"
        ui.message(f"Tempo de jogo: {m} minutos e {s} segundos ({mode}).")

    @script(
        description="Consulta as rotas dos inimigos (1 toque: rotas deduzidas, 2 toques: feitiços de invocador).",
        gestures=["kb:control+shift+e"]
    )
    def script_queryEnemyLanes(self, gesture):
        if not is_live_game_active():
            gesture.send()
            return
        lane_info = get_live_enemy_lane_assignments()
        if not lane_info:
            ui.message("Rotas inimigas indisponíveis no momento.")
            return
        count = getLastScriptRepeatCount()
        if count >= 1:
            spells_txt = lane_info.get("spells_summary", "")
            if spells_txt:
                ui.message(spells_txt)
            else:
                ui.message("Feitiços inimigos indisponíveis.")
        else:
            txt = lane_info.get("text", "")
            if txt:
                ui.message(txt)
            else:
                ui.message("Rotas inimigas não identificadas.")

    @script(
        description="Consulta mensagens e pings recentes do chat (1 toque: últimos 3; 2 toques: varredura completa).",
        gestures=["kb:m", "kb:control+shift+m"]
    )
    def script_queryChatAndPings(self, gesture):
        if not is_live_game_active():
            gesture.send()
            return
        reader = getattr(self, "_chat_reader", None)
        if not reader:
            ui.message("Leitor de chat indisponível.")
            return
        count = getLastScriptRepeatCount()
        if count >= 1:
            new_items = reader.scan_chat_sync()
            if new_items:
                msgs = [it.get("announcement", "") for it in new_items if it.get("announcement")]
                ui.message(". ".join(msgs))
            else:
                summary = reader.get_recent_summary(max_count=5)
                ui.message(f"Varredura concluída. {summary}")
        else:
            summary = reader.get_recent_summary(max_count=3)
            ui.message(summary)

    @script(
        description="Consulta o status tático do minimapa (1 toque: resumo rápido; 2 toques: análise zona por zona).",
        gestures=["kb:n", "kb:control+shift+n"]
    )
    def script_queryMinimap(self, gesture):
        if not is_live_game_active():
            gesture.send()
            return
        scanner = getattr(self, "_minimap_scanner", None)
        if not scanner:
            ui.message("Scanner de minimapa indisponível.")
            return

        active = get_live_active_player() or {}
        players = get_live_player_list() or []
        my_team = "ORDER"
        summoner = active.get("summonerName", "")
        for p in players:
            if p.get("summonerName") == summoner:
                my_team = p.get("team", "ORDER")
                break

        live_data = {"allPlayers": players, "gameData": get_live_game_stats() or {}}
        count = getLastScriptRepeatCount()
        if count >= 1:
            msg = scanner.get_tactical_summary(live_data=live_data, my_team=my_team, detailed=True)
        else:
            msg = scanner.get_tactical_summary(live_data=live_data, my_team=my_team, detailed=False)
        ui.message(msg)

    @script(
        description="Executa a Varredura do Radar de Áudio Espacial 3D (bips estéreo direcionais de inimigos e anúncio falado).",
        gestures=["kb:m", "kb:control+shift+m"]
    )
    def script_queryRadarSweep(self, gesture):
        if not is_live_game_active():
            gesture.send()
            return
        scanner = getattr(self, "_minimap_scanner", None)
        if not scanner:
            ui.message("Scanner de radar indisponível.")
            return

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

        scan = scanner.scan_radar(player_lane=my_lane, my_team=my_team)
        if not scan:
            ui.message("Não foi possível capturar o radar no momento.")
            return

        player = getattr(self, "_spatial_player", None)
        if player:
            player.play_radar_sweep(scan.get("targets", []))

        ui.message(scan.get("text", "Radar executado."))

    @script(
        description="Alterna o Radar de Proximidade de Áudio Espacial 3D em tempo real.",
        gestures=["kb:control+shift+r"]
    )
    def script_toggleAudioRadar(self, gesture):
        self._spatial_radar_enabled = not getattr(self, "_spatial_radar_enabled", True)
        state = "ativado" if self._spatial_radar_enabled else "desativado"
        player = getattr(self, "_spatial_player", None)
        if player:
            if self._spatial_radar_enabled:
                player.play_spatial_tone(880, 80, -0.6, volume=0.6)
                player.play_spatial_tone(1175, 100, 0.6, volume=0.6)
            else:
                player.play_spatial_tone(880, 80, 0.6, volume=0.6)
                player.play_spatial_tone(440, 100, -0.6, volume=0.6)
        ui.message(f"Radar de áudio espacial 3D {state}.")

    @script(
        description="Abre a Loja Acessível durante a partida (tecla P).",
        gestures=["kb:p"]
    )
    def script_shopKey(self, gesture):
        if is_live_game_active():
            self._open_in_game_shop()
        else:
            gesture.send()

    @script(
        description="Inicia o retorno à base (Recall / tecla B) com áudio e monitor de dano/interrupção.",
        gestures=["kb:b"]
    )
    def script_recallKey(self, gesture):
        if is_live_game_active():
            active = get_live_active_player() or {}
            stats = active.get("championStats", {})
            cur_hp = stats.get("currentHealth", 1000.0)
            combat = getattr(self, "_combat_status", None)
            if combat:
                msg = combat.start_recall(cur_hp)
                ui.message(msg)
            gesture.send()
        else:
            gesture.send()

    @script(
        description="Consulta o status, nível e tempo de recarga de todas as habilidades (Q, W, E, R).",
        gestures=["kb:u", "kb:control+shift+u"]
    )
    def script_queryAbilities(self, gesture):
        if is_live_game_active():
            combat = getattr(self, "_combat_status", None)
            abilities = get_live_active_player_abilities()
            if combat and abilities:
                ui.message(combat.get_abilities_summary(abilities))
            else:
                ui.message("Dados de habilidades indisponíveis no momento.")
        else:
            gesture.send()

    @script(
        description="Move o campeão pelo minimapa para a Rota Superior (Top Lane).",
        gestures=["kb:alt+1"]
    )
    def script_navTop(self, gesture):
        if is_live_game_active():
            nav = getattr(self, "_tactical_navigator", None)
            if nav:
                ok, msg = nav.navigate_to("TOP")
                ui.message(msg)
            else:
                ui.message("Navegador indisponível.")
        else:
            gesture.send()

    @script(
        description="Move o campeão pelo minimapa para a Rota do Meio (Mid Lane).",
        gestures=["kb:alt+2"]
    )
    def script_navMid(self, gesture):
        if is_live_game_active():
            nav = getattr(self, "_tactical_navigator", None)
            if nav:
                ok, msg = nav.navigate_to("MID")
                ui.message(msg)
            else:
                ui.message("Navegador indisponível.")
        else:
            gesture.send()

    @script(
        description="Move o campeão pelo minimapa para a Rota Inferior (Bot Lane).",
        gestures=["kb:alt+3"]
    )
    def script_navBot(self, gesture):
        if is_live_game_active():
            nav = getattr(self, "_tactical_navigator", None)
            if nav:
                ok, msg = nav.navigate_to("BOT")
                ui.message(msg)
            else:
                ui.message("Navegador indisponível.")
        else:
            gesture.send()

    @script(
        description="Move o campeão pelo minimapa de volta para a Base Aliada (Fonte Segura).",
        gestures=["kb:alt+4"]
    )
    def script_navBase(self, gesture):
        if is_live_game_active():
            nav = getattr(self, "_tactical_navigator", None)
            if nav:
                ok, msg = nav.navigate_to("BASE")
                ui.message(msg)
            else:
                ui.message("Navegador indisponível.")
        else:
            gesture.send()

    @script(
        description="Centraliza a câmera e o cursor do mouse no Campeão.",
        gestures=["kb:alt+space"]
    )
    def script_centerChampion(self, gesture):
        if is_live_game_active():
            nav = getattr(self, "_tactical_navigator", None)
            if nav:
                ok, msg = nav.center_camera_and_cursor()
                ui.message(msg)
            else:
                ui.message("Navegador indisponível.")
        else:
            gesture.send()

    @script(
        description="Abre o menu completo de navegação e waypoints de Summoner's Rift.",
        gestures=["kb:control+shift+n"]
    )
    def script_navMenu(self, gesture):
        if is_live_game_active():
            nav = getattr(self, "_tactical_navigator", None)
            if not nav:
                ui.message("Navegador tático indisponível.")
                return
            team = nav.get_player_team()
            def _do_nav(target_key):
                ok, msg = nav.navigate_to(target_key, team=team)
                ui.message(msg)
            prompt_navigation_dialog(_do_nav, team=team)
        else:
            gesture.send()

    @script(
        description="Consulta o placar da partida: KDA do jogador, tropas (CS) e placar geral de abates.",
        gestures=["kb:control+shift+k"]
    )
    def script_queryScoreboard(self, gesture):
        if is_live_game_active():
            ui.message(format_scoreboard_summary())
        else:
            gesture.send()

    @script(
        description="Consulta as estatísticas detalhadas do campeão (vida, mana/energia, atributos).",
        gestures=["kb:control+shift+s"]
    )
    def script_queryStats(self, gesture):
        if is_live_game_active():
            ui.message(format_champion_stats_summary())
        else:
            gesture.send()

    @script(
        description="Consulta o tempo de jogo e status de objetivos globais (dragões, barões, torres).",
        gestures=["kb:control+shift+o"]
    )
    def script_queryObjectives(self, gesture):
        if is_live_game_active():
            ui.message(format_objectives_summary())
        else:
            gesture.send()

    @script(
        description="Consulta a lista de inimigos, rotas deduzidas, feitiços de invocador e tempo de renascimento.",
        gestures=["kb:control+shift+e"]
    )
    def script_queryEnemies(self, gesture):
        if is_live_game_active():
            ui.message(format_enemies_summary())
        else:
            gesture.send()






