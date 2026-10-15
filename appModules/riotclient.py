# -*- coding: utf-8 -*-
"""
Módulo de Aplicativo NVDA para o Riot Client (Riot Client.exe e RiotClientUx.exe).
Corrige e aprimora a acessibilidade da interface Electron/Chromium:
- Desativa o buffer virtual (Browse Mode) instável, permitindo navegação limpa via Tab/Setas.
- Silencia elementos decorativos 'animation' e SVGs sem texto.
- Suprime o aviso repetitivo 'Para ver descrições ausentes de imagens, abra o menu de contexto'.
- Rotula guias (Tabs) sem nome ("guia selecionado botão animation" -> "Amigos guia selecionado").
- Rotula botões de controle de janela, perfil, configurações, carrossel e ação principal.
- Fornece atalhos para anunciar progresso de download e status do usuário.
"""

import os
import sys
import re
import time
import appModuleHandler
import controlTypes
import ui
import api
import NVDAObjects
from NVDAObjects import NVDAObject
from scriptHandler import script
from logHandler import log

_addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_lol_lib_dir = os.path.join(_addon_dir, "lol_lib")
if _addon_dir not in sys.path:
    sys.path.insert(0, _addon_dir)
if _lol_lib_dir not in sys.path:
    sys.path.insert(0, _lol_lib_dir)

try:
    from lol_lib.riot_api_helper import (
        get_riot_user_info,
        get_riot_install_status,
        get_riot_eula_status,
        accept_riot_eula,
        launch_riot_game,
        get_riot_friends_summary,
    )
except Exception:
    try:
        from riot_api_helper import (
            get_riot_user_info,
            get_riot_install_status,
            get_riot_eula_status,
            accept_riot_eula,
            launch_riot_game,
            get_riot_friends_summary,
        )
    except Exception:
        try:
            from lib.riot_api_helper import (
                get_riot_user_info,
                get_riot_install_status,
                get_riot_eula_status,
                accept_riot_eula,
                launch_riot_game,
                get_riot_friends_summary,
            )
        except Exception as e:
            log.error(f"lolAccessibility: Falha ao importar riot_api_helper em riotclient: {e}")
            get_riot_user_info = lambda: None
            get_riot_install_status = lambda: None
            get_riot_eula_status = lambda: None
            accept_riot_eula = lambda: (False, "API indisponível")
            launch_riot_game = lambda *a, **kw: (False, "API indisponível")
            get_riot_friends_summary = lambda: "API indisponível"

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
# COMPATIBILIDADE DE ROLES (NVDA 2021+)
# ============================================================================

_Role = getattr(controlTypes, "Role", None)
ROLE_TAB = getattr(_Role, "TAB", getattr(controlTypes, "ROLE_TAB", 37))
ROLE_BUTTON = getattr(_Role, "BUTTON", getattr(controlTypes, "ROLE_BUTTON", 9))
ROLE_LINK = getattr(_Role, "LINK", getattr(controlTypes, "ROLE_LINK", 30))
ROLE_ANIMATION = getattr(_Role, "ANIMATION", getattr(controlTypes, "ROLE_ANIMATION", 54))
ROLE_GRAPHIC = getattr(_Role, "GRAPHIC", getattr(controlTypes, "ROLE_GRAPHIC", 40))
ROLE_DOCUMENT = getattr(_Role, "DOCUMENT", getattr(controlTypes, "ROLE_DOCUMENT", 53))
ROLE_PANE = getattr(_Role, "PANE", getattr(controlTypes, "ROLE_PANE", 16))
ROLE_POPUPMENU = getattr(_Role, "POPUPMENU", getattr(controlTypes, "ROLE_POPUPMENU", 102))
ROLE_MENUITEM = getattr(_Role, "MENUITEM", getattr(controlTypes, "ROLE_MENUITEM", 11))
ROLE_EDITABLETEXT = getattr(_Role, "EDITABLETEXT", getattr(controlTypes, "ROLE_EDITABLETEXT", 8))
ROLE_LISTITEM = getattr(_Role, "LISTITEM", getattr(controlTypes, "ROLE_LISTITEM", 15))
ROLE_CHECKBOX = getattr(_Role, "CHECKBOX", getattr(controlTypes, "ROLE_CHECKBOX", 10))
ROLE_RADIOBUTTON = getattr(_Role, "RADIOBUTTON", getattr(controlTypes, "ROLE_RADIOBUTTON", 11))
ROLE_COMBOBOX = getattr(_Role, "COMBOBOX", getattr(controlTypes, "ROLE_COMBOBOX", 12))
ROLE_TOGGLEBUTTON = getattr(_Role, "TOGGLEBUTTON", getattr(controlTypes, "ROLE_TOGGLEBUTTON", 103))


def extract_all_inner_text(obj, max_depth=3):
    """Extrai recursivamente todos os fragmentos de texto válidos dentro de uma hierarquia IAccessible."""
    texts = []
    def _walk(o, d=0):
        if d > max_depth or not o:
            return
        name = getattr(o, "name", "") or ""
        clean = "".join(ch for ch in name if ord(ch) < 0xE000 or ord(ch) > 0xF8FF).strip()
        if clean and clean.lower() not in (
            "animation", "lottie", "item", "link", "botão", "button",
            "opção de configuração", "seção", "section", "div", "span"
        ):
            if clean not in texts:
                texts.append(clean)
        sub_list = getattr(o, "children", []) or []
        if not sub_list and hasattr(o, "IAccessibleObject"):
            try:
                import NVDAObjects.IAccessible
                sub_list = NVDAObjects.IAccessible.IAccessible._get_children(o)
            except Exception:
                pass
        for ch in sub_list:
            _walk(ch, d + 1)
    _walk(obj)
    return texts


def get_element_identifiers(obj):
    """
    Retorna (id, class_name, tag) combinando UIAAutomationId, UIAClassName
    e IA2Attributes do Chromium/IAccessible2.
    """
    auto_id = getattr(obj, "UIAAutomationId", "") or ""
    class_name = getattr(obj, "UIAClassName", "") or getattr(obj, "className", "") or ""
    tag = ""

    # IAccessible2 no Chromium/Electron
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
# MAPAS E DICIONÁRIOS DE RECONHECIMENTO SEMÂNTICO (RIOT CLIENT)
# ============================================================================

KNOWN_TAB_NAMES = {
    # Painel Social
    "friendslist": "Amigos",
    "friends-list": "Amigos",
    "friends": "Amigos",
    "conversationlist": "Conversas",
    "conversations": "Conversas",
    "chat": "Conversas e Bate-papo",
    "friendrequestslist": "Pedidos de amizade",
    "friend-requests": "Pedidos de amizade",
    "requests": "Pedidos de amizade",
    
    # Game Hub (Página do Jogo)
    "overview": "Visão Geral",
    "patch-notes": "Notas de Atualização",
    "patchnotes": "Notas de Atualização",
    "news": "Notícias",
    "esports": "Esportes e Bolão",
    "pickems": "Bolão e Pick'ems",
    "events": "Eventos e Passe",
    "battlepass": "Passe de Batalha",
    
    # Login
    "initial": "Entrar com Riot ID",
    "signin": "Entrar com Riot ID",
    "sign-in": "Entrar com Riot ID",
    "keyboard": "Entrar com Riot ID",
    "qrcode": "Entrar com QR Code",
    
    # Requisitos do Sistema
    "windows": "Windows",
    "mac": "macOS",
    "macos": "macOS",
    
    # Navegação Lateral / Jogos
    "home": "Página Inicial",
    "game-library": "Meus Jogos",
    "library": "Meus Jogos",
    "league_of_legends": "League of Legends",
    "teamfighttactics": "Teamfight Tactics",
    "valorant": "VALORANT",
    "bacon": "VALORANT",
    "lor": "Legends of Runeterra",
    "2xko": "2XKO",
    "wildrift": "Wild Rift",
    "game-bar": "Barra de Jogos",
    "campaign-hub": "Campanha e Passes",
    "side-panel": "Menu Lateral",
    "social-friends-list": "Amigos",
    "social-conversations-list": "Conversas",
    "social-friend-requests-list": "Pedidos de amizade",
    "settings-drawer-navigation": "Configurações",
}

SOCIAL_TAB_INDEX_NAMES = ["Amigos", "Conversas", "Pedidos de amizade"]
LOGIN_TAB_INDEX_NAMES = ["Entrar com Riot ID", "Entrar com QR Code"]
SYSTEM_TAB_INDEX_NAMES = ["Windows", "macOS"]
GAME_HUB_TAB_INDEX_NAMES = ["Visão Geral", "Notas de Atualização", "eSports", "Pick'Ems"]
SIDEBAR_GAMES = [
    "League of Legends",
    "Teamfight Tactics",
    "VALORANT",
    "Legends of Runeterra",
    "2XKO",
]



# ============================================================================
# CLASSES DE SOBREPOSIÇÃO (OVERLAYS)
# ============================================================================

class RiotChromeVBufTextInfo(ChromeVBufTextInfo):
    """
    Substitui a extração de texto do buffer virtual do Chromium/Electron no Riot Client.
    Limpa em tempo real ruídos como 'animation', avisos de descrições ausentes,
    formata download técnico e rotula guias e botões.
    """
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


class RiotChromeVBuf(ChromeVBuf):
    """Buffer virtual customizado para a interface Chromium do Riot Client."""
    TextInfo = RiotChromeVBufTextInfo


class RiotDocument(NVDAObjects.NVDAObject):
    """
    Documento do Riot Client.
    Desativa o buffer virtual (Browse Mode) instável, permitindo navegação limpa e direta
    por foco (Tab / Setas), garantindo que o NVDA pronuncie os nomes semânticos calculados
    para cada botão, link e controle da interface Electron.
    """
    def _get_treeInterceptorClass(self):
        return None



class RiotDecorativeAnimation(NVDAObjects.NVDAObject):
    """
    Mascara animações e SVGs decorativos como elementos de layout,
    impedindo que o NVDA pronuncie 'animation' desnecessariamente.
    """
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


class RiotAccessibleGraphic(NVDAObjects.NVDAObject):
    """
    Trata gráficos e banners sem texto alternativo, evitando o anúncio incômodo
    'Para ver descrições ausentes de imagens, abra o menu de contexto'.
    """
    def _get_name(self):
        raw_name = super().name
        if raw_name and len(raw_name.strip()) > 1 and raw_name.lower() not in ("animation", "graphic", "imagem"):
            return raw_name
        return "Imagem ilustrativa"

    def _get_description(self):
        desc = super().description or ""
        if "descrições ausentes" in desc.lower():
            return ""
        return desc


class RiotSmartTab(NVDAObjects.NVDAObject):
    """
    Substitui anúncios genéricos de 'guia selecionado botão animation' por nomes
    semânticos claros baseados na identificação do componente, ícone ou posição.
    """
    def _get_role(self):
        return getattr(controlTypes.Role, "TAB", 22)

    def _get_roleText(self):
        return "guia"

    def _get_positionInGroup(self):
        try:
            ia2 = getattr(self, "IA2Attributes", None)
            ia2_dict = dict(ia2) if ia2 and hasattr(ia2, "items") else {}
            pos = ia2_dict.get("posinset")
            total = ia2_dict.get("setsize")
            if pos and total:
                return (int(pos), int(total))
        except Exception:
            pass
        return super().positionInGroup

    def _get_name(self):
        try:
            raw_name = (super().name or "").strip()
        except Exception:
            raw_name = getattr(self, "_name", "") or ""
        auto_id, class_name, tag = get_element_identifiers(self)

        # 1. Se já tem um nome válido e descritivo vindo da acessibilidade (não genérico)
        if raw_name and raw_name.lower() not in ("animation", "lottie", "tab", "guia", "button", "botão") and not raw_name.isdigit():
            return raw_name

        # 2. Verificação por dicionário semântico direto
        for key, label in KNOWN_TAB_NAMES.items():
            if key in auto_id or key in class_name:
                return label

        # 3. Inspecionar filhos (ícone SVG ou texto oculto) usando super().children
        try:
            for child in super().children:
                c_name = (child.name or "").strip()
                if c_name and c_name.lower() not in ("animation", "lottie", "graphic", "imagem", "button", "botão"):
                    return c_name
                c_id, c_class, _ = get_element_identifiers(child)
                for key, label in KNOWN_TAB_NAMES.items():
                    if key in c_id or key in c_class:
                        return label
        except Exception:
            pass

        # 4. Verificação direta de IA2Attributes (posinset / setsize) e coordenadas espaciais
        try:
            ia2 = getattr(self, "IA2Attributes", None)
            ia2_dict = dict(ia2) if ia2 and hasattr(ia2, "items") else {}
            pos = ia2_dict.get("posinset")
            set_size = ia2_dict.get("setsize")
            loc = getattr(self, "location", None)
            if pos:
                p_int = int(pos)
                # Abas Sociais (Painel Direito: setsize == 3, ou left > 1400, ou classe social)
                if set_size == "3" or (loc and loc.left > 1400) or "social" in class_name:
                    if 1 <= p_int <= len(SOCIAL_TAB_INDEX_NAMES):
                        return SOCIAL_TAB_INDEX_NAMES[p_int - 1]
                elif set_size == "2" or (loc and loc.left < 500 and "login" in class_name):
                    if 1 <= p_int <= len(LOGIN_TAB_INDEX_NAMES):
                        return LOGIN_TAB_INDEX_NAMES[p_int - 1]
                elif ((set_size and int(set_size) >= 4) or (loc and 150 < loc.left < 1400)):
                    if 1 <= p_int <= len(GAME_HUB_TAB_INDEX_NAMES):
                        return GAME_HUB_TAB_INDEX_NAMES[p_int - 1]
        except Exception:
            pass

        # 5. Inferência por posição entre as guias irmãs (tablist)
        try:
            parent = self.parent
            if parent:
                p_id, p_class, _ = get_element_identifiers(parent)
                loc = getattr(self, "location", None)
                
                # Coletar irmãos que sejam guias
                tab_siblings = [
                    c for c in parent.children 
                    if getattr(c, "role", None) == ROLE_TAB 
                    or "tab" in get_element_identifiers(c)[1]
                    or "tab" in get_element_identifiers(c)[0]
                ]
                idx = -1
                if self in tab_siblings:
                    idx = tab_siblings.index(self)
                else:
                    for i, c in enumerate(tab_siblings):
                        if c is self or (getattr(c, "location", None) and getattr(c, "location", None) == getattr(self, "location", None)):
                            idx = i
                            break
                if idx >= 0:
                    total = len(tab_siblings)
                    
                    if (loc and loc.left > 1400) or "social" in p_class or "social" in p_id or total == 3:
                        if idx < len(SOCIAL_TAB_INDEX_NAMES):
                            return SOCIAL_TAB_INDEX_NAMES[idx]
                    elif "login" in p_class or "login" in p_id or (total == 2 and "sign" in p_class):
                        if idx < len(LOGIN_TAB_INDEX_NAMES):
                            return LOGIN_TAB_INDEX_NAMES[idx]
                    elif "system" in p_class:
                        if idx < len(SYSTEM_TAB_INDEX_NAMES):
                            return SYSTEM_TAB_INDEX_NAMES[idx]
                    elif (loc and 150 < loc.left < 1400) or "hub" in p_class or total >= 4:
                        if idx < len(GAME_HUB_TAB_INDEX_NAMES):
                            return GAME_HUB_TAB_INDEX_NAMES[idx]
                    else:
                        return f"Guia {idx + 1}"
        except Exception:
            pass

        if raw_name and raw_name.isdigit():
            return f"Guia {raw_name}"
            
        return "Guia de navegação"

    def _get_firstChild(self):
        # Tratar a guia como elemento atômico, impedindo que o leitor
        # desça para o botão interno e para a animação SVG
        return None

    def _get_children(self):
        return []

    def _get_childCount(self):
        return 0


class RiotSmartButton(NVDAObjects.NVDAObject):
    """
    Identifica e fornece nomes intuitivos para botões que não possuem rótulo de texto.
    """
    def _get_role(self):
        auto_id, class_name, tag = get_element_identifiers(self)
        if "identity-menu-disclosure" in class_name or "identity-menu" in auto_id:
            return getattr(controlTypes.Role, "POPUPMENU", 102)
        elif "identity-menu-item" in class_name:
            return getattr(controlTypes.Role, "MENUITEM", 11)
        elif "identity-menu-riot-id" in class_name:
            return getattr(controlTypes.Role, "BUTTON", 9)
        try:
            return super().role
        except Exception:
            return getattr(self, "_role", getattr(controlTypes.Role, "BUTTON", 9))

    def _get_name(self):
        try:
            raw_name = (super().name or "").strip()
        except Exception:
            raw_name = getattr(self, "_name", "") or ""
        auto_id, class_name, tag = get_element_identifiers(self)
        search_target = f"{auto_id} {class_name}"

        # 0. Menu da Conta e Perfil no Cabeçalho Superior (identity-menu-disclosure)
        if "identity-menu-disclosure" in class_name or "identity-menu" in auto_id:
            user = get_riot_user_info()
            user_tag = user["full_tag"] if user and user.get("full_tag") else "Minha Conta"
            status = "Online"
            notice = ""
            if raw_name and "multifator" in raw_name.lower():
                notice = " (Aviso: Habilitar autenticação multifator)"
            elif raw_name and raw_name.lower() not in ("identity", "perfil", "menu", "botão", "button"):
                notice = f" ({raw_name})"
            return f"Menu da Conta: {user_tag} (Status: {status}){notice}"

        # 0.04 Perfil do Usuário no topo do Menu da Conta aberto (identity-menu-riot-id)
        if "identity-menu-riot-id" in class_name:
            texts = extract_all_inner_text(self, max_depth=3)
            if texts:
                riot_id = "".join(texts) if any(t.startswith("#") for t in texts) else " ".join(texts)
                return f"Perfil conectado: {riot_id} (Menu da Conta)"
            user = get_riot_user_info()
            user_tag = user["full_tag"] if user and user.get("full_tag") else ""
            if user_tag:
                return f"Perfil conectado: {user_tag} (Menu da Conta)"
            return "Perfil conectado (Menu da Conta)"

        # 0.05 Itens do Menu da Conta (identity-menu-item)
        if "identity-menu-item" in class_name:
            if raw_name and raw_name.lower() not in ("item", "menuitem", "button", "botão"):
                return raw_name
            try:
                for c in (getattr(self, "children", None) or []):
                    c_name = (c.name or "").strip()
                    if c_name and c_name.lower() not in ("item", "menuitem"):
                        return c_name
            except Exception:
                pass
            return "Opção do Menu da Conta"

        # 0.08 Itens de Navegação nas Configurações (settings-navigation-item)
        if "settings-navigation-item" in class_name:
            texts = extract_all_inner_text(self, max_depth=3)
            is_sub = "settings-sub-navigation-item" in class_name
            sub_label = " (Sub-categoria de configuração)" if is_sub else ""
            if texts:
                return f"{' - '.join(texts).title()}{sub_label}"
            clean_self = "".join(ch for ch in (raw_name or "") if ord(ch) < 0xE000 or ord(ch) > 0xF8FF).strip()
            if clean_self and clean_self.lower() not in ("item", "opção de configuração"):
                return f"{clean_self.title()}{sub_label}"
            return "Opção de Configuração"

        # 0.09 Fechar Modal / Configurações (riot-modal-close)
        if "riot-modal-close" in class_name or "settings-close" in class_name:
            return "Fechar configurações"

        # 0.091 Menus suspensos / Dropdowns nas Configurações (current-selection / dropdown)
        if "current-selection" in class_name or "dropdown" in class_name:
            clean_val = "".join(ch for ch in (raw_name or "") if ord(ch) < 0xE000 or ord(ch) > 0xF8FF).strip()
            label = ""
            try:
                p = getattr(self, "parent", None)
                if p:
                    p_children = getattr(p.parent, "children", []) or []
                    if p in p_children:
                        idx = p_children.index(p)
                        for prev in reversed(p_children[:idx]):
                            prev_name = (getattr(prev, "name", "") or "").strip()
                            if prev_name and len(prev_name) > 2 and prev_name.lower() not in ("dropdown", "imagem ilustrativa"):
                                label = prev_name
                                break
            except Exception:
                pass
            if not label and getattr(self, "parent", None):
                p_name = (getattr(self.parent, "name", "") or "").strip()
                if p_name and len(p_name) > 2:
                    label = p_name
            label_prefix = f"{label.title()}: " if label else "Seleção: "
            return f"{label_prefix}{clean_val} (Menu suspenso - pressione Enter para alterar)"

        # 0.092 Campo Seletor de Pasta nas Configurações (folder-picker-input-field)
        if "folder-picker-input-field" in class_name:
            clean_path = "".join(ch for ch in (raw_name or "") if ord(ch) < 0xE000 or ord(ch) > 0xF8FF).strip()
            return f"Local de instalação: {clean_path} (Pressione Enter para alterar pasta)"

        # 0.093 Botão de testar som de notificações (notifications-settings-sound-button)
        if "notifications-settings-sound-button" in class_name:
            row_name = ""
            try:
                p = getattr(self, "parent", None)
                while p:
                    p_cls = get_element_identifiers(p)[1]
                    p_tag = get_element_identifiers(p)[2]
                    if "notifications-settings" in p_cls or p_tag in ("tr", "table"):
                        for td in (getattr(p, "children", []) or []):
                            td_cls = get_element_identifiers(td)[1]
                            if "type" in td_cls:
                                row_name = (getattr(td, "name", "") or "").strip()
                                break
                        break
                    p = getattr(p, "parent", None)
            except Exception:
                pass
            if row_name:
                return f"Testar som de {row_name}"
            return "Testar som de notificação"

        # 0.094 Botões de ação do produto nas Configurações (Reparar, Criar atalho)
        if "product-settings-button" in class_name:
            clean = "".join(ch for ch in (raw_name or "") if ord(ch) < 0xE000 or ord(ch) > 0xF8FF).strip()
            if "reparar" in clean.lower():
                return "Reparar arquivos do jogo"
            elif "atalho" in clean.lower():
                return "Adicionar Atalho na Área de Trabalho"
            return clean or "Botão de configuração do jogo"

        # Tratar botões de vídeo promocional (Video Off / Video On)
        if raw_name.lower() == "video off":
            return "Vídeo promocional (Pausado - pressione Enter para reproduzir)"
        elif raw_name.lower() == "video on":
            return "Vídeo promocional (Reproduzindo - pressione Enter para pausar)"

        # Tratar botão de áudio/volume (Distinguindo Configurações de Notificações vs Vídeo Promocional)
        if "volume-button" in class_name:
            is_settings = False
            try:
                p = getattr(self, "parent", None)
                for _ in range(5):
                    if not p:
                        break
                    if "settings" in get_element_identifiers(p)[1].lower():
                        is_settings = True
                        break
                    p = getattr(p, "parent", None)
            except Exception:
                pass
            if is_settings:
                if "off" in raw_name.lower() or "mute" in raw_name.lower():
                    return "Ativar áudio das notificações (Silenciado)"
                elif "on" in raw_name.lower():
                    return "Silenciar volume das notificações (Ativado)"
                return "Controle de volume das notificações"
            # Fallback para vídeo promocional
            if raw_name.lower() in ("volume on", "volumeon") or ("on" in raw_name.lower()):
                return "Áudio do vídeo promocional (Ativado - pressione Enter para silenciar)"
            elif raw_name.lower() in ("volume off", "volumeoff", "mute") or ("off" in raw_name.lower()):
                return "Áudio do vídeo promocional (Silenciado - pressione Enter para ativar som)"
            return "Áudio do vídeo promocional"

        # 0. Botões de jogos na barra lateral (quick-action-disclosure)
        if "quick-action-disclosure" in class_name or "quick-action-disclosure" in auto_id:
            game_name = "Jogo"
            try:
                parent = self.parent
                if parent:
                    game_btns = [
                        c for c in (parent.children or [])
                        if "quick-action-disclosure" in get_element_identifiers(c)[1]
                    ]
                    idx = -1
                    for i, b in enumerate(game_btns):
                        if b is self or (getattr(b, "location", None) and getattr(b, "location", None) == getattr(self, "location", None)):
                            idx = i
                            break
                    if 0 <= idx < len(SIDEBAR_GAMES):
                        game_name = SIDEBAR_GAMES[idx]
            except Exception:
                pass
            badge_str = f" ({raw_name} notificações)" if raw_name.isdigit() and int(raw_name) > 0 else ""
            return f"{game_name} (Menu rápido){badge_str}"

        # 0.1 Botão de ação rápida (Jogar / Instalar o jogo ativo)
        if "quick-action-button" in class_name or "quick-action-button" in auto_id:
            action_text = raw_name if raw_name and raw_name.lower() not in ("button", "botão") else "Jogar"
            game_name = ""
            try:
                content_parent = self.parent
                if content_parent:
                    nav = content_parent.parent
                    if nav:
                        nav_children = list(nav.children or [])
                        if content_parent in nav_children:
                            c_idx = nav_children.index(content_parent)
                            for prev_c in reversed(nav_children[:c_idx]):
                                if "quick-action-disclosure" in get_element_identifiers(prev_c)[1]:
                                    game_btns = [
                                        c for c in nav_children
                                        if "quick-action-disclosure" in get_element_identifiers(c)[1]
                                    ]
                                    if prev_c in game_btns:
                                        g_idx = game_btns.index(prev_c)
                                        if 0 <= g_idx < len(SIDEBAR_GAMES):
                                            game_name = SIDEBAR_GAMES[g_idx]
                                    break
            except Exception:
                pass
            if game_name:
                return f"{action_text} {game_name}"
            return f"{action_text} jogo selecionado"

        # 0.2 Botão de navegação inicial / meus jogos (basic-nav-button)
        if "basic-nav-button" in class_name:
            curr = self
            for _ in range(5):
                if not curr:
                    break
                c_name = (getattr(curr, "name", "") or "").strip().lower()
                c_desc = (getattr(curr, "description", "") or "").strip().lower()
                if any(k in c_name or k in c_desc for k in ("jogos", "games", "meus jogos")):
                    return "Meus Jogos"
                elif any(k in c_name or k in c_desc for k in ("início", "inicio", "home", "página inicial")):
                    return "Página Inicial"
                curr = getattr(curr, "parent", None)
            return "Página Inicial"

        # 0.3 Botão de novidades e campanhas
        if "campaign-button" in class_name:
            return "Novidades e Destaques"

        # Tratar números soltos de carrossel de notícias (ex: '0', '1', '13')
        if raw_name.isdigit() and "quick-action" not in class_name and "disclosure" not in class_name:
            return f"Slide {raw_name}"

        # Tratar cards promocionais e destaques do Game Hub
        if "base-card-button" in class_name or "card-button" in class_name:
            if raw_name and raw_name.lower() not in ("animation", "button", "botão") and not raw_name.isdigit():
                return f"Destaque: {raw_name}"

        # Se já tiver um nome legítimo e não for genérico
        if raw_name and raw_name.lower() not in ("animation", "lottie", "button", "botão", "graphic", "imagem"):
            return raw_name

        # 0.4 Termos de Serviço (ToS / EULA descobertos via REA)
        if "tos-accept" in search_target:
            return "Aceitar Termos de Serviço"
        elif "tos-checkbox" in search_target:
            return "Caixa de seleção: Li e concordo com os Termos de Serviço"
        elif "tos-decline" in search_target:
            return "Recusar Termos de Serviço"
        elif "tos-content-error-retry" in search_target:
            return "Tentar novamente carregar Termos de Serviço"

        # 1. Controles de Janela
        if "close" in search_target or "fechar" in search_target:
            return "Fechar janela"
        elif "min" in search_target or "minimizar" in search_target:
            return "Minimizar janela"
        elif "max" in search_target or "maximizar" in search_target:
            return "Maximizar janela"

        # 2. Carrossel e Mídia
        elif any(k in search_target for k in ["prev", "anterior", "chevron-left"]):
            return "Slide anterior"
        elif any(k in search_target for k in ["next", "proximo", "próximo", "chevron-right"]):
            return "Próximo slide"
        elif "chevron-down" in search_target:
            return "Expandir ou recolher seção"

        # 3. Cabeçalho, Painel Lateral e Social
        elif "side-panel-collapse-button" in search_target:
            return "Recolher ou expandir painel lateral"
        elif "side-panel-riot-id" in search_target:
            return "Meu Riot ID"
        elif any(k in search_target for k in ["presence", "status"]):
            return "Status da Conta: Online"
        elif any(k in search_target for k in ["profile", "avatar", "identity"]):
            return "Meu Perfil"
        elif any(k in search_target for k in ["setting", "gear", "config"]):
            return "Configurações"
        elif any(k in search_target for k in ["notif", "bell"]):
            return "Notificações"
        elif any(k in search_target for k in ["downloadsquare", "download"]):
            return "Gerenciador de Downloads"
        elif any(k in search_target for k in ["friend", "social-presence-bar", "social-presence-button"]):
            return "Painel Social e Amigos"
        elif "add-friend" in search_target:
            return "Adicionar Amigo"
        elif "chat-window-close" in search_target:
            return "Fechar Bate-papo"
        elif "social-chat-item" in search_target:
            return "Conversa"
        elif "social-friend-item" in search_target:
            return "Amigo"
        elif "whats-new-modal" in search_target:
            return "Fechar novidades"

        # 4. Ação Principal (CTA - cta-button-resting-state-button, etc.)
        elif any(k in search_target for k in [
            "cta-button", "cta-button-resting-state-button", "cta-button-working-state-launchable-button",
            "quick-action-button", "cta", "play", "install", "update", "jogar", "instalar"
        ]):
            return "Jogar / Iniciar League of Legends"
        elif "cta-button-working-state-button" in search_target:
            return "Atualizando League of Legends (Pausar/Retomar)"

        # 5. Inspecionar filhos em busca de texto usando super().children
        try:
            for child in super().children:
                c_name = (child.name or "").strip()
                if c_name and c_name.lower() not in ("animation", "lottie", "graphic", "imagem"):
                    return c_name
        except Exception:
            pass

        # 6. Fallback por coordenadas de tela
        try:
            loc = self.location
            if loc and loc.top < 60:
                if loc.left > 1200:
                    return "Fechar janela"
                elif loc.left > 1150:
                    return "Minimizar janela"
        except Exception:
            pass

        return raw_name or "Botão"

    def _get_firstChild(self):
        auto_id, class_name, _ = get_element_identifiers(self)
        if any(k in class_name for k in ("quick-action", "basic-nav", "campaign", "app-controls", "side-panel-collapse", "identity-menu-disclosure", "identity-menu-riot-id", "settings-navigation-item", "riot-modal-close", "video-button", "volume-button", "base-card-button", "current-selection", "folder-picker", "notifications-settings-sound-button", "product-settings-button")):
            return None
        raw = self.name
        if raw and raw.lower() not in ("botão", "button"):
            return None
        return super().firstChild

    def _get_children(self):
        auto_id, class_name, _ = get_element_identifiers(self)
        if any(k in class_name for k in ("quick-action", "basic-nav", "campaign", "app-controls", "side-panel-collapse", "identity-menu-disclosure", "identity-menu-riot-id", "settings-navigation-item", "riot-modal-close", "video-button", "volume-button", "base-card-button", "current-selection", "folder-picker", "notifications-settings-sound-button", "product-settings-button")):
            return []
        raw = self.name
        if raw and raw.lower() not in ("botão", "button"):
            return []
        return super().children


class RiotSmartLink(NVDAObjects.NVDAObject):
    """
    Identifica e fornece texto claro para links de novidades, banners e artigos.
    """
    def _get_name(self):
        try:
            raw_name = (super().name or "").strip()
        except Exception:
            raw_name = getattr(self, "_name", "") or ""
        auto_id, class_name, tag = get_element_identifiers(self)

        # Tratar links de novidades e destaques (evitando leitura de imagem sem etiqueta)
        if "campaign-button" in class_name or "novidades" in (raw_name or "").lower():
            return "Novidades e Destaques"

        if "basic-nav-button" in class_name:
            curr = self
            for _ in range(5):
                if not curr:
                    break
                c_name = (getattr(curr, "name", "") or "").strip().lower()
                c_desc = (getattr(curr, "description", "") or "").strip().lower()
                if any(k in c_name or k in c_desc for k in ("jogos", "games", "meus jogos")):
                    return "Meus Jogos"
                elif any(k in c_name or k in c_desc for k in ("início", "inicio", "home", "página inicial")):
                    return "Página Inicial"
                curr = getattr(curr, "parent", None)
            return "Página Inicial"

        # Limpar prefixos estranhos ou "animation"
        if raw_name and raw_name.lower() not in ("animation", "lottie", "link"):
            return raw_name
            
        # Inspecionar filhos (muitas vezes o título da notícia está em um cabeçalho H2/H3 filho)
        found_texts = []
        try:
            def collect_text(o, depth=0):
                if depth > 4 or len(found_texts) > 2:
                    return
                t = (o.name or "").strip()
                if t and t.lower() not in ("animation", "lottie", "graphic", "imagem", "link"):
                    if t not in found_texts:
                        found_texts.append(t)
                for c in o.children:
                    collect_text(c, depth + 1)
            collect_text(self)
        except Exception:
            pass
            
        if found_texts:
            return " - ".join(found_texts)
            
        # Tentar pegar URL / Value
        val = getattr(self, "value", "") or ""
        if val and ("http" in val or "/" in val):
            slug = val.rstrip("/").split("/")[-1].replace("-", " ")
            if len(slug) > 3:
                return f"Notícia: {slug.capitalize()}"
                
        return raw_name or "Link de novidade"

    def _get_firstChild(self):
        auto_id, class_name, _ = get_element_identifiers(self)
        if "campaign-button" in class_name or "basic-nav-button" in class_name:
            return None
        return super().firstChild

    def _get_children(self):
        auto_id, class_name, _ = get_element_identifiers(self)
        if "campaign-button" in class_name or "basic-nav-button" in class_name:
            return []
        return super().children


class RiotSmartEdit(NVDAObjects.NVDAObject):
    """
    Melhora a acessibilidade de campos de entrada de texto no Riot Client,
    como 'Nome do jogo' (Riot ID) e 'Tagline' (#TAG) ao adicionar amigos, campos de busca e filtros.
    """
    def _get_name(self):
        try:
            raw_name = (super().name or "").strip()
        except Exception:
            raw_name = getattr(self, "_name", "") or ""

        ia2 = getattr(self, "IA2Attributes", None)
        ia2_dict = dict(ia2) if (ia2 and hasattr(ia2, "items")) else {}
        placeholder = (ia2_dict.get("placeholder", "") or "").strip()
        auto_id, class_name, tag = get_element_identifiers(self)

        p = getattr(self, "parent", None)
        gp = getattr(p, "parent", None) if p else None
        ggp = getattr(gp, "parent", None) if gp else None

        parent_classes = " ".join([
            get_element_identifiers(p)[1] if p else "",
            get_element_identifiers(gp)[1] if gp else "",
            get_element_identifiers(ggp)[1] if ggp else "",
        ]).lower()

        if placeholder:
            plow = placeholder.lower()
            if "nome do jogo" in plow or "game name" in plow or "game-name" in parent_classes:
                return "Riot ID do amigo (Nome do jogo)"
            elif "tagline" in plow or "tag-line" in parent_classes:
                return "Tagline (#TAG do amigo, ex: BR1)"
            elif "pesquis" in plow or "search" in plow:
                return f"Pesquisar: {placeholder}"
            return placeholder.capitalize()

        if "add-friend-tag-line" in parent_classes:
            return "Tagline (#TAG do amigo, ex: BR1)"
        elif "social-panel" in parent_classes and "add" in parent_classes:
            return "Riot ID do amigo (Nome do jogo)"

        if raw_name and raw_name.lower() not in ("edição", "input", "edit", "text") and not raw_name.isdigit():
            return raw_name

        return "Campo de texto"

    def _get_description(self):
        try:
            desc = super().description or ""
        except Exception:
            desc = ""
        ia2 = getattr(self, "IA2Attributes", None)
        ia2_dict = dict(ia2) if (ia2 and hasattr(ia2, "items")) else {}
        placeholder = (ia2_dict.get("placeholder", "") or "").strip().lower()

        if "tagline" in placeholder:
            return "Digite o identificador de região ou número do amigo sem a hashtag (exemplo: BR1)"
        elif "nome do jogo" in placeholder:
            return "Digite o Riot ID do jogador que você deseja adicionar como amigo"

        return desc


class RiotSocialItem(NVDAObjects.NVDAObject):
    """
    Identifica itens de amigos e presença no Painel Social do Riot Client,
    anunciando o nome do amigo e o status de presença (Online, Em partida, Ausente, etc.).
    """
    def _get_role(self):
        return getattr(controlTypes.Role, "LISTITEM", 15)

    def _get_roleText(self):
        return "amigo"

    def _get_name(self):
        try:
            raw_name = (super().name or "").strip()
        except Exception:
            raw_name = getattr(self, "_name", "") or ""

        heading = ""
        caption = ""

        try:
            for c in (getattr(self, "children", []) or []):
                _, c_cls, _ = get_element_identifiers(c)
                if "social-item-heading" in c_cls:
                    for sub in (getattr(c, "children", []) or [c]):
                        s_name = (getattr(sub, "name", "") or "").strip()
                        clean = "".join(ch for ch in s_name if ord(ch) < 0xE000 or ord(ch) > 0xF8FF).strip()
                        if clean:
                            heading = clean
                            break
                    if not heading and getattr(c, "name", ""):
                        heading = getattr(c, "name", "").strip()

                elif "social-item-caption" in c_cls:
                    for sub in (getattr(c, "children", []) or [c]):
                        s_name = (getattr(sub, "name", "") or "").strip()
                        clean = "".join(ch for ch in s_name if ord(ch) < 0xE000 or ord(ch) > 0xF8FF).strip()
                        if clean:
                            caption = clean
                            break
                    if not caption and getattr(c, "name", ""):
                        caption = getattr(c, "name", "").strip()
        except Exception:
            pass

        if heading:
            status_part = f" (Status: {caption})" if caption else ""
            return f"{heading}{status_part}"

        if raw_name and raw_name.lower() not in ("item", "social-item", "seção", "section"):
            return raw_name

        return "Amigo da lista social"


def clean_game_card_name(raw_name):
    """
    Higieniza o nome dos cards da biblioteca de jogos do Riot Client,
    removendo duplicações de texto (ex: 'VALORANT VALORANT') e identificando o status de instalação.
    """
    if not raw_name:
        return "Jogo", False
    is_installed = "instalado" in raw_name.lower() or "installed" in raw_name.lower()
    import re
    cleaned = re.sub(r'(?i)\b(instalado|installed)\b', '', raw_name).strip()
    cleaned = ' '.join(cleaned.split())
    tokens = cleaned.split()
    half = len(tokens) // 2
    if len(tokens) >= 2 and len(tokens) % 2 == 0 and tokens[:half] == tokens[half:]:
        cleaned = " ".join(tokens[:half])
    elif len(cleaned) > 4 and cleaned.endswith(cleaned[:len(cleaned)//2]):
        cleaned = cleaned[:len(cleaned)//2].strip()
    return cleaned or "Jogo", is_installed


class RiotLibraryProductCard(NVDAObjects.NVDAObject):
    """
    Identifica e anuncia os cards de jogos da Biblioteca ('Meus Jogos'),
    eliminando redundâncias (ex: 'VALORANT VALORANT') e informando claramente se o jogo está instalado.
    """
    def _get_role(self):
        return getattr(controlTypes.Role, "BUTTON", 9)

    def _get_roleText(self):
        return "jogo"

    def _get_name(self):
        try:
            raw_name = (super().name or "").strip()
        except Exception:
            raw_name = getattr(self, "_name", "") or ""
        if not raw_name:
            texts = extract_all_inner_text(self, max_depth=4)
            raw_name = " ".join(texts)

        clean_title, is_installed = clean_game_card_name(raw_name)
        status_str = "Instalado" if is_installed else "Não instalado"
        return f"Jogo: {clean_title} (Status: {status_str}) - Pressione Enter para abrir"

    def _get_firstChild(self):
        return None

    def _get_children(self):
        return []


class RiotSmartToggle(NVDAObjects.NVDAObject):
    """
    Melhora a acessibilidade de caixas de seleção, alternadores (toggles) e botões de rádio
    nas Configurações do Riot Client (Inicialização, Aceleração de hardware, Filtro de chat, Notificações).
    """
    def _get_role(self):
        auto_id, class_name, tag = get_element_identifiers(self)
        if "radio" in class_name or getattr(self, "role", 0) == getattr(controlTypes.Role, "RADIOBUTTON", 11):
            return getattr(controlTypes.Role, "RADIOBUTTON", 11)
        return getattr(controlTypes.Role, "CHECKBOX", 10)

    def _get_name(self):
        try:
            raw_name = (super().name or "").strip()
        except Exception:
            raw_name = getattr(self, "_name", "") or ""
        auto_id, class_name, tag = get_element_identifiers(self)

        # Se for na tabela de notificações (Alertas ou Sons)
        if "notifications-settings" in class_name:
            col_name = "Alertas" if "alert" in class_name else ("Sons" if "sound" in class_name else "")
            row_name = ""
            try:
                p = getattr(self, "parent", None)
                while p:
                    p_cls = get_element_identifiers(p)[1]
                    p_tag = get_element_identifiers(p)[2]
                    if "notifications-settings" in p_cls or p_tag in ("tr", "table"):
                        cells = getattr(p, "children", []) or []
                        for td in cells:
                            td_cls = get_element_identifiers(td)[1]
                            if "type" in td_cls:
                                row_name = (getattr(td, "name", "") or "").strip()
                                break
                        if not col_name and self in cells:
                            idx = cells.index(self)
                            if idx == 1:
                                col_name = "Alertas"
                            elif idx == 2:
                                col_name = "Sons"
                        break
                    p = getattr(p, "parent", None)
            except Exception:
                pass
            if not col_name:
                col_name = "Alertas" if "alert" in class_name else ("Sons" if "sound" in class_name else "Notificação")
            if row_name:
                return f"{row_name} - {col_name}"
            return f"Opção de notificação: {col_name}"

        # Se tiver nome próprio legítimo
        clean = "".join(ch for ch in raw_name if ord(ch) < 0xE000 or ord(ch) > 0xF8FF).strip()
        if clean and clean.lower() not in ("checkbox", "toggle", "switch", "radio", "botão", "button"):
            return clean

        # Buscar rótulo no elemento pai ou irmãos anteriores
        label = ""
        try:
            p = getattr(self, "parent", None)
            if p:
                for sib in (getattr(p, "children", []) or []):
                    if sib is not self:
                        sib_name = "".join(ch for ch in (getattr(sib, "name", "") or "") if ord(ch) < 0xE000 or ord(ch) > 0xF8FF).strip()
                        if sib_name and len(sib_name) > 3 and sib_name.lower() not in ("checkbox", "toggle", "switch"):
                            label = sib_name
                            break
                if not label and getattr(p, "name", ""):
                    p_name = "".join(ch for ch in p.name if ord(ch) < 0xE000 or ord(ch) > 0xF8FF).strip()
                    if p_name and len(p_name) > 3:
                        label = p_name
        except Exception:
            pass

        return label or "Alternador de configuração"

    def _get_firstChild(self):
        return None

    def _get_children(self):
        return []


# ============================================================================
# MÓDULO PRINCIPAL DO RIOT CLIENT
# ============================================================================

class AppModule(appModuleHandler.AppModule):
    """Módulo de acessibilidade para o Riot Client."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        log.info("lolAccessibility: AppModule para Riot Client inicializado.")

    def chooseNVDAObjectOverlayClasses(self, obj, clsList):
        try:
            role = getattr(obj, "role", None)
            auto_id, class_name, tag = get_element_identifiers(obj)
            window_class = (getattr(obj, "windowClassName", "") or "").lower()
            raw_name = (getattr(obj, "name", "") or "").strip().lower()

            # Desativa o buffer virtual (Browse Mode) no Riot Client
            if role in (ROLE_DOCUMENT, ROLE_PANE) and (tag in ("#document", "document") or "chrome_renderwidgethosthwnd" in window_class):
                clsList.insert(0, RiotDocument)

            # 1. Tratar Guias (Tabs) - DEVE VIR ANTES DE ANIMAÇÃO para não silenciar as abas sociais com ícones Lottie
            elif role == ROLE_TAB or "tab-button" in class_name or "tab" in auto_id or tag == "tab" or (tag == "button" and "tab" in class_name):
                clsList.insert(0, RiotSmartTab)

            # 2. Silenciar invólucros e prefixos de inputs de texto (evita repetição de "Campo de texto")
            elif any(k in class_name for k in ("text-input-wrapper", "text-input-prefix-icon", "text-input-suffix")):
                clsList.insert(0, RiotDecorativeAnimation)

            # 3. Tratar Campos de Edição e Inputs de Texto (Nome do jogo, Tagline, busca, etc.)
            elif role == ROLE_EDITABLETEXT or (tag == "input" and "button" not in class_name) or "text-input-field" in class_name:
                clsList.insert(0, RiotSmartEdit)

            # 4. Tratar cards de jogos da Biblioteca ('Meus Jogos')
            elif "library-product-card" in class_name or "library-game-card" in class_name:
                clsList.insert(0, RiotLibraryProductCard)

            # 5. Tratar caixas de seleção, alternadores (toggles) e botões de rádio
            elif role in (ROLE_CHECKBOX, ROLE_RADIOBUTTON, ROLE_TOGGLEBUTTON) or any(k in class_name for k in ("toggle", "checkbox", "radio-button")) or "notifications-settings-toggle" in class_name:
                clsList.insert(0, RiotSmartToggle)

            # 6. Tratar Itens do Painel Social (Amigos e Presenças)
            elif "social-item" in class_name and not any(k in class_name for k in ("avatar", "heading", "caption")):
                clsList.insert(0, RiotSocialItem)

            # 7. Tratar Avatares e Ícones Decorativos no Painel Social e Configurações
            elif any(k in class_name for k in ("social-item-avatar", "settings-header-title-icon-image", "platform-availability-section-type-icon")):
                clsList.insert(0, RiotDecorativeAnimation)

            # 8. Silencia nós de animação e ícones SVG/Lottie internos dentro de abas ou botões
            elif raw_name in ("animation", "lottie") and (tag in ("div", "svg", "lottie", "span") or not class_name or (getattr(obj, "parent", None) and getattr(obj.parent, "role", None) in (ROLE_BUTTON, ROLE_TAB))):
                clsList.insert(0, RiotDecorativeAnimation)

            # 9. Tratar Botões e Menus Interativos (incluindo menu da conta, disclosures, navegação e itens de configuração)
            elif role in (ROLE_BUTTON, ROLE_POPUPMENU, ROLE_MENUITEM) or "button" in class_name or tag == "button" or "disclosure" in class_name or "settings-navigation-item" in class_name or "folder-picker-input-field" in class_name:
                clsList.insert(0, RiotSmartButton)

            # 10. Tratar Links
            elif role == ROLE_LINK or "link" in class_name or tag == "a":
                clsList.insert(0, RiotSmartLink)

            # 11. Silencia elementos de animação pura ou decorativos que não sejam botões/guias/inputs
            elif role == ROLE_ANIMATION or tag == "svg" or (raw_name in ("animation", "lottie") and not any(k in class_name for k in ("tab", "button", "disclosure", "item", "input"))):
                clsList.insert(0, RiotDecorativeAnimation)

            # 12. Tratar imagens e gráficos sem texto alternativo
            elif role == ROLE_GRAPHIC or tag == "img":
                clsList.insert(0, RiotAccessibleGraphic)

        except Exception as e:
            log.debug(f"lolAccessibility: Erro em chooseNVDAObjectOverlayClasses: {e}")

        super().chooseNVDAObjectOverlayClasses(obj, clsList)

    def event_gainFocus(self, obj, nextHandler):
        """Suprime anúncios espúrios de nós decorativos e notifica se houver Termos pendentes."""
        try:
            # Se um elemento interno decorativo receber foco (ex: ícone SVG com nome 'animation' dentro de uma aba ou botão)
            raw_name = (getattr(obj, "name", "") or "").strip().lower()
            if raw_name in ("animation", "lottie", "graphic", "imagem"):
                parent = getattr(obj, "parent", None)
                if parent and (getattr(parent, "role", None) in (ROLE_TAB, ROLE_BUTTON) or any(k in get_element_identifiers(parent)[1] for k in ("tab", "button", "disclosure", "volume", "video"))):
                    # Silenciar ruído interno da aba ou botão
                    return
        except Exception:
            pass

        try:
            eula = get_riot_eula_status()
            if eula == "AcceptanceRequired":
                ui.message("Atenção: Novos Termos de Serviço pendentes no Riot Client. Pressione Control+Shift+T para aceitar automaticamente.")
        except Exception:
            pass
        nextHandler()

    # ========================================================================
    # ATALHOS DE TECLADO (SCRIPTS)
    # ========================================================================

    @script(
        description="Anuncia o progresso de download e velocidade de instalação do jogo.",
        gestures=["kb:NVDA+shift+d", "kb:control+shift+d"]
    )
    def script_announceDownloadProgress(self, gesture):
        """Varre a tela ou consulta a API local para obter o status de download/instalação."""
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
        except Exception as e:
            log.debug(f"lolAccessibility: Erro ao varrer tela para download: {e}")

        if is_ready and not found_text:
            ui.message("League of Legends está 100% instalado e pronto para jogar! Pressione Enter em 'Jogar' ou Control+Shift+J.")
            return

        if found_text:
            msg = "Progresso de Download: " + ". ".join(found_text)
            ui.message(msg)
            return

        # Consultar via API se a varredura não achou texto
        try:
            installs = get_riot_install_status()
            if installs and "league_of_legends.live" in installs:
                lol_st = installs["league_of_legends.live"].get("patch", {})
                state = lol_st.get("state", "")
                if state == "up_to_date":
                    ui.message("League of Legends está atualizado e pronto para jogar! Pressione Control+Shift+J para iniciar.")
                    return
                elif state:
                    ui.message(f"Status do League of Legends na Riot: {state}.")
                    return
        except Exception:
            pass

        user = get_riot_user_info()
        user_name = user["full_tag"] if user else "Invocador"
        ui.message(f"Status do League of Legends: Pronto para jogar ({user_name}).")

    @script(
        description="Anuncia o perfil do usuário atualmente conectado e seu status.",
        gestures=["kb:NVDA+shift+s", "kb:control+shift+s"]
    )
    def script_announceUserInfo(self, gesture):
        """Consulta as informações do perfil autenticado na Riot."""
        info = get_riot_user_info()
        if info:
            reg = info.get("region")
            reg_str = ""
            if isinstance(reg, dict):
                reg_str = reg.get("id") or reg.get("tag") or ""
            elif isinstance(reg, str):
                reg_str = reg
            regiao = f" (Região {reg_str.upper()})" if reg_str else ""
            ui.message(f"Conectado como: {info['full_tag']}, Status: Online{regiao}")
        else:
            ui.message("Usuário conectado no Riot Client. Status: Online.")

    @script(
        description="Consulta a lista de amigos online e atividades no Riot Client.",
        gestures=["kb:NVDA+shift+f", "kb:control+shift+f"]
    )
    def script_announceFriends(self, gesture):
        """Informa amigos conectados e suas presenças nos jogos Riot."""
        res = get_riot_friends_summary()
        ui.message(res)

    @script(
        description="Aceita Termos de Serviço (ToS) via API REST da Riot ou por rolagem do container CEF.",
        gestures=["kb:NVDA+shift+t", "kb:control+shift+t"]
    )
    def script_acceptTerms(self, gesture):
        """Aceita termos instantaneamente via API ou fallback por UIA/rolagem."""
        ui.message("Verificando Termos de Serviço...")
        # 1. Tentar aceitar diretamente via API REST nativa da Riot
        try:
            ok, msg = accept_riot_eula()
            if ok:
                ui.message(msg)
                return
        except Exception as e:
            log.debug(f"lolAccessibility: Falha ao aceitar termos via API: {e}")

        # 2. Fallback via rolagem física e clique UIA
        if scroll_and_accept_async:
            ui.message("Acionando assistente de rolagem e aceitação de termos...")
            def _cb(ok, msg):
                ui.message(msg)
            scroll_and_accept_async(callback=_cb)
        else:
            ui.message("Assistente de termos não disponível.")

    @script(
        description="Inicia o League of Legends diretamente ou move o foco para o botão principal de ação (Jogar/Instalar).",
        gestures=["kb:NVDA+shift+j", "kb:control+shift+j"]
    )
    def script_focusActionButton(self, gesture):
        """Inicia League of Legends via API ou aciona o botão principal do Riot Client."""
        try:
            # 1. Se houver Termos pendentes, aceitar primeiro
            if get_riot_eula_status() == "AcceptanceRequired":
                ok, msg = accept_riot_eula()
                if ok:
                    ui.message("Termos de Serviço aceitos automaticamente! Verificando inicialização...")

            # 2. Tentar iniciar LoL diretamente via API REST nativa da Riot
            installs = get_riot_install_status()
            if installs and "league_of_legends.live" in installs:
                lol_patch = installs["league_of_legends.live"].get("patch", {})
                if lol_patch.get("state") == "up_to_date":
                    ui.message("Iniciando League of Legends pelo Riot Client...")
                    ok, launch_msg = launch_riot_game("league_of_legends", "live")
                    if ok:
                        return

            # 3. Fallback: procurar botão CTA na tela (cta-button, Jogar, etc.)
            fg = api.getForegroundObject()
            if fg:
                target = None
                def find_btn(o, depth=0):
                    nonlocal target
                    if target or depth > 10:
                        return
                    name = (o.name or "").lower()
                    auto_id, class_name, _ = get_element_identifiers(o)
                    elem_str = f"{name} {auto_id} {class_name}"
                    if o.role == ROLE_BUTTON or "button" in class_name:
                        if any(k in elem_str for k in [
                            "cta-button", "quick-action-button", "jogar", "iniciar",
                            "play", "install", "update", "começar", "comecar", "aceitar"
                        ]):
                            target = o
                            return
                    for c in o.children:
                        find_btn(c, depth + 1)
                find_btn(fg)
                
                if target:
                    target.setFocus()
                    try:
                        target.doDefaultAction()
                    except Exception:
                        pass
                    ui.message(f"Ação executada: {target.name or 'Jogar'}")
                    return
        except Exception as e:
            log.debug(f"lolAccessibility: Erro ao focar botão de ação: {e}")
            
        ui.message("Não foi possível iniciar o jogo ou localizar o botão principal.")

    @script(
        description="Move o foco diretamente para o Menu da Conta e Perfil no topo da tela.",
        gestures=["kb:NVDA+shift+u", "kb:control+shift+u"]
    )
    def script_focusAccountMenu(self, gesture):
        """Localiza o botão identity-menu-disclosure e transfere o foco."""
        try:
            fg = api.getForegroundObject()
            if fg:
                target = None
                def find_menu(o, depth=0):
                    nonlocal target
                    if target or depth > 25:
                        return
                    ia2 = getattr(o, "IA2Attributes", None)
                    cls_name = ia2.get("class", "") if (ia2 and hasattr(ia2, "items")) else ""
                    auto_id, c_name, _ = get_element_identifiers(o)
                    if "identity-menu-disclosure" in cls_name or "identity-menu-disclosure" in c_name:
                        target = o
                        return
                    for c in (getattr(o, "children", None) or []):
                        find_menu(c, depth + 1)
                find_menu(fg)
                if target:
                    target.setFocus()
                    return
        except Exception as e:
            log.debug(f"lolAccessibility: Erro ao focar menu da conta: {e}")
        ui.message("Menu da conta não localizado na tela atual.")

    @script(
        description="Abre a tela de Configurações do Riot Client diretamente.",
        gestures=["kb:NVDA+shift+p", "kb:control+shift+p"]
    )
    def script_openSettings(self, gesture):
        """Localiza o menu da conta e aciona o item Configurações."""
        try:
            fg = api.getForegroundObject()
            if fg:
                # 1. Verificar se a gaveta de configurações já está aberta
                settings_item = None
                def find_open_settings(o, depth=0):
                    nonlocal settings_item
                    if settings_item or depth > 25:
                        return
                    ia2 = getattr(o, "IA2Attributes", None)
                    cls_name = ia2.get("class", "") if (ia2 and hasattr(ia2, "items")) else ""
                    if "settings-drawer" in cls_name or "settings-navigation-item" in cls_name or "riot-modal-close" in cls_name:
                        settings_item = o
                        return
                    for c in (getattr(o, "children", None) or []):
                        find_open_settings(c, depth + 1)
                find_open_settings(fg)
                if settings_item:
                    settings_item.setFocus()
                    ui.message("Configurações já estão abertas.")
                    return

                # 2. Localizar identity-menu-disclosure
                account_menu = None
                def find_acc(o, depth=0):
                    nonlocal account_menu
                    if account_menu or depth > 25:
                        return
                    ia2 = getattr(o, "IA2Attributes", None)
                    cls_name = ia2.get("class", "") if (ia2 and hasattr(ia2, "items")) else ""
                    auto_id, c_name, _ = get_element_identifiers(o)
                    if "identity-menu-disclosure" in cls_name or "identity-menu-disclosure" in c_name:
                        account_menu = o
                        return
                    for c in (getattr(o, "children", None) or []):
                        find_acc(c, depth + 1)
                find_acc(fg)
                
                if account_menu:
                    account_menu.setFocus()
                    # Se estiver recolhido, expandir
                    states = getattr(account_menu, "states", set())
                    if getattr(controlTypes.State, "EXPANDED", 256) not in states:
                        try:
                            account_menu.doAction()
                        except Exception:
                            pass
                        time.sleep(0.4)
                    
                    # Aguardar expansão e procurar item 'Configurações'
                    cfg_target = None
                    def find_cfg(o, depth=0):
                        nonlocal cfg_target
                        if cfg_target or depth > 25:
                            return
                        name = (getattr(o, "name", "") or "").lower()
                        ia2 = getattr(o, "IA2Attributes", None)
                        cls = ia2.get("class", "") if (ia2 and hasattr(ia2, "items")) else ""
                        if "configura" in name and ("item" in cls or getattr(o, "role", None) in (ROLE_MENUITEM, ROLE_BUTTON)):
                            cfg_target = o
                            return
                        for c in (getattr(o, "children", None) or []):
                            find_cfg(c, depth + 1)

                    find_cfg(api.getForegroundObject() or fg)
                    if not cfg_target:
                        find_cfg(api.getDesktopObject())
                    
                    if cfg_target:
                        cfg_target.setFocus()
                        try:
                            cfg_target.doAction()
                        except Exception:
                            pass
                        ui.message("Configurações do Riot Client abertas.")
                        return
        except Exception as e:
            log.debug(f"lolAccessibility: Erro ao abrir configurações: {e}")
        ui.message("Não foi possível abrir as configurações do Riot Client.")

    @script(
        description="Move o foco para as Guias Sociais do Riot Client (Amigos, Conversas, Pedidos).",
        gestures=["kb:NVDA+shift+o", "kb:control+shift+o"]
    )
    def script_focusSocialTabs(self, gesture):
        """Localiza a primeira ou a guia ativa no painel social e transfere o foco."""
        try:
            fg = api.getForegroundObject()
            if fg:
                tab_target = None
                def find_tab(o, depth=0):
                    nonlocal tab_target
                    if tab_target or depth > 25:
                        return
                    ia2 = getattr(o, "IA2Attributes", None)
                    cls_name = ia2.get("class", "") if (ia2 and hasattr(ia2, "items")) else ""
                    loc = getattr(o, "location", None)
                    if "tab-button" in cls_name and loc and loc.left > 1400:
                        states = getattr(o, "states", set())
                        if getattr(controlTypes.State, "SELECTED", 4) in states:
                            tab_target = o
                            return
                        if not tab_target:
                            tab_target = o
                    for c in (getattr(o, "children", None) or []):
                        find_tab(c, depth + 1)
                find_tab(fg)
                if tab_target:
                    tab_target.setFocus()
                    return
        except Exception as e:
            log.debug(f"lolAccessibility: Erro ao focar abas sociais: {e}")
        ui.message("Guias sociais não localizadas na tela atual.")

    @script(
        description="Move o foco diretamente para o campo de adicionar amigo (Riot ID / Nome do jogo).",
        gestures=["kb:NVDA+shift+a", "kb:control+shift+a"]
    )
    def script_focusAddFriend(self, gesture):
        """Localiza o campo de texto para adicionar amigo e transfere o foco."""
        try:
            fg = api.getForegroundObject()
            if fg:
                input_target = None
                def find_input(o, depth=0):
                    nonlocal input_target
                    if input_target or depth > 25:
                        return
                    ia2 = getattr(o, "IA2Attributes", None)
                    ia2_dict = dict(ia2) if (ia2 and hasattr(ia2, "items")) else {}
                    tag = ia2_dict.get("tag", "")
                    ph = (ia2_dict.get("placeholder", "") or "").lower()
                    cls_name = ia2_dict.get("class", "")
                    if tag == "input" and ("nome do jogo" in ph or "amigo" in ph or "game" in ph or "text-input-field" in cls_name):
                        input_target = o
                        return
                    for c in (getattr(o, "children", None) or []):
                        find_input(c, depth + 1)
                find_input(fg)
                if input_target:
                    input_target.setFocus()
                    ui.message("Campo Adicionar Amigo focado: Digite o Riot ID.")
                    return
        except Exception as e:
            log.debug(f"lolAccessibility: Erro ao focar adicionar amigo: {e}")
        ui.message("Campo de adicionar amigo não localizado na tela atual.")

    @script(
        description="Move o foco para as Guias Centrais do Jogo (Visão Geral, Notas de Atualização, eSports, etc.).",
        gestures=["kb:NVDA+shift+h", "kb:control+shift+h"]
    )
    def script_focusGameHubTabs(self, gesture):
        """Localiza as guias centrais do Game Hub e transfere o foco."""
        try:
            fg = api.getForegroundObject()
            if fg:
                tab_target = None
                def find_hub_tab(o, depth=0):
                    nonlocal tab_target
                    if tab_target or depth > 25:
                        return
                    loc = getattr(o, "location", None)
                    role = getattr(o, "role", 0)
                    ia2 = getattr(o, "IA2Attributes", None)
                    cls_name = ia2.get("class", "") if (ia2 and hasattr(ia2, "items")) else ""
                    if loc and 150 < loc.left < 1400 and loc.top < 100 and (role == ROLE_TAB or "tab-button" in cls_name):
                        states = getattr(o, "states", set())
                        if getattr(controlTypes.State, "SELECTED", 4) in states:
                            tab_target = o
                            return
                        if not tab_target:
                            tab_target = o
                    for c in (getattr(o, "children", None) or []):
                        find_hub_tab(c, depth + 1)
                find_hub_tab(fg)
                if tab_target:
                    tab_target.setFocus()
                    return
        except Exception as e:
            log.debug(f"lolAccessibility: Erro ao focar abas do jogo: {e}")
        ui.message("Guias do jogo não localizadas na tela atual.")

    @script(
        description="Navega diretamente para a Biblioteca de Jogos (Meus Jogos) no Riot Client.",
        gestures=["kb:NVDA+shift+l", "kb:control+shift+l"]
    )
    def script_focusGameLibrary(self, gesture):
        """Localiza o botão 'Meus Jogos' na barra lateral de navegação e transfere o foco/aciona."""
        try:
            fg = api.getForegroundObject()
            if fg:
                target = None
                def find_games_btn(o, depth=0):
                    nonlocal target
                    if target or depth > 25:
                        return
                    ia2 = getattr(o, "IA2Attributes", None)
                    c_cls = ia2.get("class", "") if (ia2 and hasattr(ia2, "items")) else ""
                    desc = (getattr(o, "description", "") or "").lower()
                    name = (getattr(o, "name", "") or "").lower()
                    if ("basic-nav-button" in c_cls or "slide-tooltip-disclosure" in c_cls) and any(k in desc or k in name for k in ("jogos", "games", "meus jogos")):
                        target = o
                        return
                    for c in (getattr(o, "children", None) or []):
                        find_games_btn(c, depth + 1)
                find_games_btn(fg)
                if not target:
                    find_games_btn(api.getDesktopObject())
                if target:
                    target.setFocus()
                    try:
                        target.doAction()
                    except Exception:
                        pass
                    ui.message("Biblioteca de jogos (Meus Jogos) aberta.")
                    return
        except Exception as e:
            log.debug(f"lolAccessibility: Erro ao focar Meus Jogos: {e}")
        ui.message("Não foi possível localizar o botão Meus Jogos.")

    @script(
        description="Navega diretamente para a Página Inicial (Início) do Riot Client.",
        gestures=["kb:NVDA+shift+i", "kb:control+shift+i"]
    )
    def script_focusHome(self, gesture):
        """Localiza o botão 'Página Inicial' na barra lateral de navegação e transfere o foco/aciona."""
        try:
            fg = api.getForegroundObject()
            if fg:
                target = None
                def find_home_btn(o, depth=0):
                    nonlocal target
                    if target or depth > 25:
                        return
                    ia2 = getattr(o, "IA2Attributes", None)
                    c_cls = ia2.get("class", "") if (ia2 and hasattr(ia2, "items")) else ""
                    desc = (getattr(o, "description", "") or "").lower()
                    name = (getattr(o, "name", "") or "").lower()
                    if ("basic-nav-button" in c_cls or "slide-tooltip-disclosure" in c_cls) and any(k in desc or k in name for k in ("início", "inicio", "home", "página inicial")):
                        target = o
                        return
                    for c in (getattr(o, "children", None) or []):
                        find_home_btn(c, depth + 1)
                find_home_btn(fg)
                if not target:
                    find_home_btn(api.getDesktopObject())
                if target:
                    target.setFocus()
                    try:
                        target.doAction()
                    except Exception:
                        pass
                    ui.message("Página Inicial do Riot Client aberta.")
                    return
        except Exception as e:
            log.debug(f"lolAccessibility: Erro ao focar Página Inicial: {e}")
        ui.message("Não foi possível localizar o botão Página Inicial.")

    @script(
        description="Exibe os atalhos de acessibilidade do Riot Client e League of Legends.",
        gestures=["kb:f1"]
    )
    def script_help(self, gesture):
        help_text = (
            "Atalhos de Acessibilidade Riot & LoL: "
            "Control+Shift+U: Menu da Conta, Perfil e Status. "
            "Control+Shift+P: Abrir Configurações do Riot Client. "
            "Control+Shift+L: Biblioteca de Jogos (Meus Jogos). "
            "Control+Shift+I: Página Inicial do Riot Client. "
            "Control+Shift+O: Guias Sociais (Amigos, Conversas, Pedidos). "
            "Control+Shift+H: Guias Centrais do Jogo (Visão Geral, Notas de Atualização, etc.). "
            "Control+Shift+A: Campo Adicionar Amigo (Riot ID). "
            "Control+Shift+J: Iniciar League of Legends diretamente ou acionar botão principal. "
            "Control+Shift+T: Aceitar Termos de Serviço (ToS) automaticamente. "
            "Control+Shift+F: Anunciar amigos online e jogos em execução. "
            "Control+Shift+D: Anunciar progresso do download e instalação. "
            "Control+Shift+S: Anunciar usuário conectado e status. "
            "F6: Aceitar partida encontrada no LoL. "
            "Control+Shift+F6: Alternar aceitação automática de partida. "
            "Control+Shift+C: Informações da seleção de campeões."
        )
        ui.message(help_text)



