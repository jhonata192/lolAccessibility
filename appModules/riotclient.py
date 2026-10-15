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
GAME_HUB_TAB_INDEX_NAMES = ["Visão Geral", "Notas de Atualização", "Notícias", "Eventos"]
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
    def _get_name(self):
        raw_name = (super().name or "").strip()
        # Se já tem um nome válido e descritivo
        if raw_name and raw_name.lower() not in ("animation", "lottie", "tab", "guia", "button", "botão") and not raw_name.isdigit():
            return raw_name
            
        auto_id, class_name, tag = get_element_identifiers(self)
        
        for key, label in KNOWN_TAB_NAMES.items():
            if key in auto_id or key in class_name:
                return label
                
        # 1. Inspecionar filhos (ícone SVG ou texto oculto) usando super().children
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

        # 2. Inferência por posição entre as guias irmãs (tablist)
        try:
            parent = self.parent
            if parent:
                p_id, p_class, _ = get_element_identifiers(parent)
                
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
                    
                    if "social" in p_class or "social" in p_id or total == 3:
                        if idx < len(SOCIAL_TAB_INDEX_NAMES):
                            return SOCIAL_TAB_INDEX_NAMES[idx]
                    elif "login" in p_class or "login" in p_id or (total == 2 and "sign" in p_class):
                        if idx < len(LOGIN_TAB_INDEX_NAMES):
                            return LOGIN_TAB_INDEX_NAMES[idx]
                    elif "system" in p_class or total == 2:
                        if idx < len(SYSTEM_TAB_INDEX_NAMES):
                            return SYSTEM_TAB_INDEX_NAMES[idx]
                    elif total >= 3 and idx < len(GAME_HUB_TAB_INDEX_NAMES):
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
    def _get_name(self):
        raw_name = (super().name or "").strip()
        auto_id, class_name, tag = get_element_identifiers(self)
        search_target = f"{auto_id} {class_name}"
        
        # Tratar botões de vídeo promocional (Video Off / Video On)
        if raw_name.lower() == "video off":
            return "Vídeo promocional (Pausado - pressione Enter para reproduzir)"
        elif raw_name.lower() == "video on":
            return "Vídeo promocional (Reproduzindo - pressione Enter para pausar)"

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
            p = self.parent
            for _ in range(3):
                if not p:
                    break
                p_desc = (getattr(p, "description", "") or "").strip()
                if p_desc:
                    if p_desc.lower() in ("início", "inicio", "home"):
                        return "Página Inicial"
                    elif p_desc.lower() in ("jogos", "games", "meus jogos"):
                        return "Meus Jogos"
                    return p_desc
                p = getattr(p, "parent", None)
            return "Página Inicial"

        # 0.3 Botão de novidades e campanhas
        if "campaign-button" in class_name:
            return "Novidades e Destaques"

        # Tratar números soltos de carrossel de notícias (ex: '0', '1', '13')
        if raw_name.isdigit() and "quick-action" not in class_name and "disclosure" not in class_name:
            return f"Slide {raw_name}"

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
        if any(k in class_name for k in ("quick-action", "basic-nav", "campaign", "app-controls", "side-panel-collapse")):
            return None
        raw = self.name
        if raw and raw.lower() not in ("botão", "button"):
            return None
        return super().firstChild

    def _get_children(self):
        auto_id, class_name, _ = get_element_identifiers(self)
        if any(k in class_name for k in ("quick-action", "basic-nav", "campaign", "app-controls", "side-panel-collapse")):
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
        raw_name = (super().name or "").strip()
        auto_id, class_name, tag = get_element_identifiers(self)

        # Tratar links de novidades e destaques (evitando leitura de imagem sem etiqueta)
        if "campaign-button" in class_name or "novidades" in (raw_name or "").lower():
            return "Novidades e Destaques"

        if "basic-nav-button" in class_name:
            p = self.parent
            for _ in range(3):
                if not p:
                    break
                p_desc = (getattr(p, "description", "") or "").strip()
                if p_desc:
                    if p_desc.lower() in ("início", "inicio", "home"):
                        return "Página Inicial"
                    elif p_desc.lower() in ("jogos", "games", "meus jogos"):
                        return "Meus Jogos"
                    return p_desc
                p = getattr(p, "parent", None)
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

            # Silencia elementos de animação pura ou decorativos mesmo que venham com role botão no Chromium
            elif role == ROLE_ANIMATION or "animation" in class_name or tag == "svg" or raw_name in ("animation", "lottie"):
                clsList.insert(0, RiotDecorativeAnimation)

            # 1. Tratar Guias (Tabs)
            elif role == ROLE_TAB or "tab-button" in class_name or "tab" in auto_id or tag == "tab":
                clsList.insert(0, RiotSmartTab)

            # 2. Tratar Botões (incluindo disclosures de ação rápida e navegação)
            elif role == ROLE_BUTTON or "button" in class_name or tag == "button" or "disclosure" in class_name:
                clsList.insert(0, RiotSmartButton)

            # 3. Tratar Links
            elif role == ROLE_LINK or "link" in class_name or tag == "a":
                clsList.insert(0, RiotSmartLink)

            # 4. Tratar imagens e gráficos sem texto alternativo
            elif role == ROLE_GRAPHIC or tag == "img":
                clsList.insert(0, RiotAccessibleGraphic)

        except Exception as e:
            log.debug(f"lolAccessibility: Erro em chooseNVDAObjectOverlayClasses: {e}")

        super().chooseNVDAObjectOverlayClasses(obj, clsList)

    def event_gainFocus(self, obj, nextHandler):
        """Notifica o usuário se houver Termos de Serviço pendentes logo ao focar o cliente."""
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
        description="Exibe os atalhos de acessibilidade do Riot Client e League of Legends.",
        gestures=["kb:f1"]
    )
    def script_help(self, gesture):
        help_text = (
            "Atalhos de Acessibilidade Riot & LoL: "
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


