import urllib.request
import json
import time
import sys
import ctypes

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = "http://127.0.0.1:8765/action"
HEADERS = {
    "X-NVDA-Bridge-Token": "nvda-bridge-secret-change-me",
    "Content-Type": "application/json"
}

def call(action, params={}):
    req = urllib.request.Request(
        BASE_URL,
        data=json.dumps({"action": action, "params": params}).encode("utf-8"),
        headers=HEADERS
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode()).get("result", {})

bring_to_front_code = """
import api
import ctypes

user32 = ctypes.windll.user32
desktop = api.getDesktopObject()
target_hwnd = None
for child in desktop.children:
    pname = (getattr(child, "appModule", None) and getattr(child.appModule, "appName", "")) or ""
    if "leagueclientux" in pname.lower():
        target_hwnd = getattr(child, "windowHandle", 0)
        break

if target_hwnd:
    user32.ShowWindow(target_hwnd, 9)
    user32.SetForegroundWindow(target_hwnd)
    result = {"success": True, "hwnd": target_hwnd}
else:
    result = {"success": False}
"""

inspect_code = """
import api
import speech
import controlTypes

focus = api.getFocusObject()

class Capturer:
    captured = []
    @classmethod
    def speak(cls, s, *a, **k):
        cls.captured.extend([str(x) for x in s if isinstance(x, str)])

old_speak = speech.speech.speak
speech.speech.speak = Capturer.speak
try:
    speech.speakObject(focus, reason=controlTypes.OutputReason.FOCUS)
finally:
    speech.speech.speak = old_speak

app_name = (getattr(focus, "appModule", None) and getattr(focus.appModule, "appName", "")) or ""

result = {
    'app': app_name,
    'name': getattr(focus, 'name', None),
    'role': str(getattr(focus, 'role', None)),
    'roleText': getattr(focus, 'roleText', None),
    'cls': focus.__class__.__name__,
    'states': [str(s) for s in getattr(focus, 'states', set())],
    'spoken': " ".join(Capturer.captured)
}
"""

def run_tab_test(steps=12):
    print("=" * 70)
    print("ATIVANDO JANELA DO LEAGUE OF LEGENDS E TESTANDO NAVEGAÇÃO")
    print("=" * 70)
    
    # 1. Bring window to front
    front_res = call("execute_code", {"code": bring_to_front_code}).get("result", {})
    print(f"Trazer League Client para frente: {front_res}")
    time.sleep(0.8)
    
    # 2. Check focus
    init_res = call("execute_code", {"code": inspect_code}).get("result", {})
    print(f"[00 - Início] App: {init_res.get('app')} | Nome: '{init_res.get('name')}' | Classe: {init_res.get('cls')} | Falado: '{init_res.get('spoken')}'\n")
    
    if "leagueclientux" not in init_res.get("app", "").lower():
        print("AVISO: Foco ainda não está no LeagueClientUx! Tentando focar...")
        time.sleep(0.5)

    print("--- INICIANDO CICLO DE TAB ---")
    for i in range(1, steps + 1):
        call("send_key", {"key": "tab"})
        time.sleep(0.4)
        res = call("execute_code", {"code": inspect_code}).get("result", {})
        app = res.get("app")
        name = res.get("name")
        cls_name = res.get("cls")
        role_text = res.get("roleText") or res.get("role")
        spoken = res.get("spoken")
        print(f"[{i:02d} - TAB] App: {app} | Nome: '{name}' | Tipo: {role_text} ({cls_name}) | Fala: '{spoken}'")
        time.sleep(0.1)

    print("\n--- INICIANDO CICLO DE SHIFT+TAB (VOLTAR) ---")
    for i in range(1, 5):
        call("send_key", {"key": "shift+tab"})
        time.sleep(0.4)
        res = call("execute_code", {"code": inspect_code}).get("result", {})
        name = res.get("name")
        role_text = res.get("roleText") or res.get("role")
        spoken = res.get("spoken")
        print(f"[{i:02d} - SHIFT+TAB] Nome: '{name}' | Tipo: {role_text} | Fala: '{spoken}'")
        time.sleep(0.1)

if __name__ == "__main__":
    run_tab_test(10)
