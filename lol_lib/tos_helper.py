# -*- coding: utf-8 -*-
"""
Módulo de Automação de Acessibilidade para Termos de Serviço (ToS)
League of Legends e Riot Client (lolAccessibility).

Resolve a barreira de acessibilidade em containers Chromium/CEF onde:
1. O texto dos termos possui mais de 40.000px e só responde a eventos físicos de mouse wheel.
2. Leitores de tela (NVDA/JAWS) e teclas de navegação (PageDown, End, Setas) são ignorados.
3. O botão 'Aceitar' / 'Tô dentro' permanece desabilitado com o texto 'Role para aceitar'.
4. Execuções em segundo plano requerem vinculação à Área de Trabalho Interativa ('Default').
"""

import os
import sys
import time
import threading
import ctypes
from ctypes import wintypes

try:
    from logHandler import log
except Exception:
    import logging
    log = logging.getLogger("lolAccessibility.tos_helper")

try:
    import ui
except Exception:
    ui = None

try:
    import api
except Exception:
    api = None

try:
    import tones
    def _beep(freq, dur):
        try:
            tones.beep(freq, dur)
        except Exception:
            pass
except Exception:
    import winsound
    def _beep(freq, dur):
        try:
            winsound.Beep(freq, dur)
        except Exception:
            pass

# Win32 Constants
DESKTOP_ALL = 0x01FF
SW_RESTORE = 9
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_WHEEL = 0x0800
WHEEL_DELTA_DOWN = -240
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


def ensure_interactive_desktop():
    """
    Associa a thread atual à Área de Trabalho interativa ('Default').
    Garante que SetCursorPos e mouse_event funcionem mesmo se disparados
    por threads em segundo plano ou processos de automação.
    """
    try:
        hDesk = user32.OpenDesktopW("Default", 0, False, DESKTOP_ALL)
        if hDesk:
            user32.SetThreadDesktop(hDesk)
            return hDesk
    except Exception as e:
        log.debug(f"tos_helper: Erro ao vincular thread desktop: {e}")
    return None


def get_process_name_by_pid(pid):
    """Obtém o nome do executável a partir de seu PID com permissão restrita."""
    if not pid:
        return ""
    h_proc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h_proc:
        return ""
    buf = ctypes.create_unicode_buffer(1024)
    size = wintypes.DWORD(len(buf))
    name = ""
    try:
        if kernel32.QueryFullProcessImageNameW(h_proc, 0, buf, ctypes.byref(size)):
            name = os.path.basename(buf.value).lower()
    except Exception:
        pass
    finally:
        kernel32.CloseHandle(h_proc)
    return name


def find_target_window():
    """
    Localiza a janela do Riot Client ou League of Legends.
    Retorna (hwnd, title, class_name, (left, top, right, bottom)) ou None.
    Aplica filtros rígidos para evitar tocar em navegadores, Discord ou IDEs.
    """
    found = None

    def enum_cb(hwnd, lparam):
        nonlocal found
        if not user32.IsWindowVisible(hwnd):
            return True

        title_buf = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, title_buf, 512)
        cls_buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls_buf, 256)

        t_str = title_buf.value.strip()
        c_str = cls_buf.value.strip()
        t_lower = t_str.lower()

        is_match = False
        if "riot client" in t_lower or "league of legends" in t_lower:
            is_match = True
        elif c_str == "RiotWindowClass":
            is_match = True
        elif c_str == "Chrome_WidgetWin_1" and t_str:
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value:
                pname = get_process_name_by_pid(pid.value)
                if "riot" in pname or "league" in pname:
                    is_match = True

        if is_match:
            r = RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(r))
            w = r.right - r.left
            h = r.bottom - r.top
            if w > 400 and h > 300:
                found = (hwnd, t_str, c_str, (r.left, r.top, r.right, r.bottom))
                return False
        return True

    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    return found


def click_via_nvda_uia():
    """
    Se estiver rodando dentro do NVDA, vasculha a árvore acessível em busca
    de botões de confirmação de termos ('Aceitar', 'Tô dentro', 'Continuar', etc.)
    e aciona sua ação padrão. Retorna True se clicou com sucesso.
    """
    if not api:
        return False
    try:
        fg = api.getForegroundObject()
        if not fg:
            return False

        target_names = [
            "aceitar", "accept", "tô dentro", "to dentro", "entendi",
            "concordo", "eu concordo", "continuar", "continue", "vamos nessa"
        ]

        def search_node(node, depth=0):
            if not node or depth > 15:
                return None
            name = (getattr(node, "name", "") or "").lower().strip()
            for tn in target_names:
                if tn in name:
                    return node

            for child in getattr(node, "children", []):
                res = search_node(child, depth + 1)
                if res:
                    return res
            return None

        btn = search_node(fg)
        if btn:
            btn.setFocus()
            btn.doDefaultAction()
            return True
    except Exception as e:
        log.debug(f"tos_helper: Erro em click_via_nvda_uia: {e}")
    return False


def scroll_and_accept_sync(scroll_steps=160, click_button=True, step_delay=0.01):
    """
    Executa a rolagem do container CEF e aciona o botão de aceitar termos sincronamente.
    Retorna (sucesso: bool, mensagem: str).
    """
    _beep(800, 150)

    h_desk = ensure_interactive_desktop()
    try:
        target = find_target_window()
        if not target:
            _beep(440, 200)
            return False, "Janela do Riot Client ou League of Legends não encontrada."

        hwnd, title, cls_name, rect = target
        left, top, right, bottom = rect
        width = right - left
        height = bottom - top

        # 1. Trazer e restaurar janela para primeiro plano
        user32.ShowWindow(hwnd, SW_RESTORE)
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.4)

        # 2. Posicionar cursor no centro geométrico do container de termos
        center_x = left + width // 2
        center_y = top + height // 2
        user32.SetCursorPos(center_x, center_y)
        time.sleep(0.1)

        # Clique inicial para dar foco no container Chromium
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        time.sleep(0.15)

        # 3. Disparar rajada de eventos de rolagem física (mouse wheel)
        for _ in range(scroll_steps):
            user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, WHEEL_DELTA_DOWN, 0)
            time.sleep(step_delay)

        # Aguardar 0.8s para o DOM do Chromium habilitar o botão
        time.sleep(0.8)

        if not click_button:
            _beep(1000, 150)
            return True, f"Container de Termos de Serviço rolado com sucesso na janela '{title}'."

        # 4. Tentar clicar no botão de aceitação via UIA do leitor de telas
        clicked = False
        if api:
            clicked = click_via_nvda_uia()

        # 5. Se não clicou via UIA, aplicar clique de fallback nas coordenadas padrão do botão
        if not clicked:
            btn_x = center_x
            btn_y = bottom - 65
            user32.SetCursorPos(btn_x, btn_y)
            time.sleep(0.1)
            user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            clicked = True

        _beep(1200, 150)
        time.sleep(0.1)
        _beep(1600, 250)
        return True, f"Termos de Serviço rolados e confirmados com sucesso na janela '{title}'!"

    except Exception as e:
        log.error(f"tos_helper: Erro inesperado ao processar termos: {e}")
        _beep(440, 250)
        return False, f"Falha ao aceitar termos: {e}"
    finally:
        if h_desk:
            try:
                user32.CloseDesktop(h_desk)
            except Exception:
                pass


def scroll_and_accept_async(scroll_steps=160, click_button=True, callback=None):
    """
    Executa a rolagem e confirmação em uma thread em segundo plano,
    garantindo que o NVDA nunca congele a fala ou a interface.
    """
    def _worker():
        ok, msg = scroll_and_accept_sync(scroll_steps=scroll_steps, click_button=click_button)
        if callback:
            try:
                callback(ok, msg)
            except Exception as e:
                log.debug(f"tos_helper: Erro no callback: {e}")
        elif ui:
            ui.message(msg)

    t = threading.Thread(target=_worker, name="LoLToSScrollThread", daemon=True)
    t.start()
    return t


class LoLToSHelper:
    """Classe utilitária para acesso direto ou injeção nos AppModules e GlobalPlugins."""
    ensure_interactive_desktop = staticmethod(ensure_interactive_desktop)
    find_target_window = staticmethod(find_target_window)
    scroll_and_accept_sync = staticmethod(scroll_and_accept_sync)
    scroll_and_accept_async = staticmethod(scroll_and_accept_async)


if __name__ == "__main__":
    print("Iniciando assistente de Termos de Servico do LoL / Riot Client...")
    ok, msg = scroll_and_accept_sync()
    print(f"Resultado: {msg}")
