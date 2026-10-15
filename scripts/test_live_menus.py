import urllib.request
import json
import time

BASE_URL = "http://127.0.0.1:8765/action"
HEADERS = {
    "X-NVDA-Bridge-Token": "nvda-bridge-secret-change-me",
    "Content-Type": "application/json"
}

def call(action, params={}):
    req = urllib.request.Request(BASE_URL, data=json.dumps({"action": action, "params": params}).encode("utf-8"), headers=HEADERS)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read().decode())

print("=== VERIFICANDO MENUS SUPERIORES E ABAS SOCIAIS AO VIVO ===")

code_inspect = """
import api

class Inspector:
    account_menu = None
    social_tabs = []
    
    @classmethod
    def walk(cls, o, depth=0):
        if not o or depth > 25: return
        ia2 = getattr(o, "IA2Attributes", None)
        ia2_dict = dict(ia2) if ia2 and hasattr(ia2, "items") else {}
        cls_name = ia2_dict.get("class", "")
        loc = getattr(o, "location", None)
        
        if "identity-menu-disclosure" in cls_name:
            cls.account_menu = {
                "name": o.name,
                "role": int(o.role),
                "roleText": getattr(o, "roleText", ""),
                "class": cls_name,
                "states": str(o.states)
            }
            
        if "tab-button" in cls_name and loc and loc.left > 1400:
            cls.social_tabs.append({
                "name": o.name,
                "role": int(o.role),
                "roleText": getattr(o, "roleText", ""),
                "posInGroup": getattr(o, "positionInGroup", None),
                "states": str(o.states)
            })
            
        for c in (getattr(o, "children", None) or []):
            cls.walk(c, depth + 1)

fg = api.getForegroundObject()
Inspector.walk(fg)
result = {
    "account_menu": Inspector.account_menu,
    "social_tabs": Inspector.social_tabs
}
"""
res = call("execute_code", {"code": code_inspect})
print("Resultados dos Elementos Superiores:")
print(json.dumps(res.get("result", {}).get("result", {}), indent=2, ensure_ascii=False))

# Testar o script_focusAccountMenu via atalho ou execução direta
print("\n--- Testando Acionamento do Foco no Menu da Conta ---")
code_run_acc = """
import api
app = api.getFocusObject().appModule
gesture_mock = None
app.script_focusAccountMenu(gesture_mock)
result = "script_focusAccountMenu executado com sucesso"
"""
call("execute_code", {"code": code_run_acc})
time.sleep(0.4)
focus_now = call("get_current_focus")
print("Objeto Focado após script_focusAccountMenu:")
print(f"Nome: '{focus_now['result']['name']}' | Role: {focus_now['result']['role']} | Class: '{focus_now['result']['className']}'")

speech = call("get_speech_history", {"count": 2})
print("Fala do NVDA:")
for p in speech.get("result", {}).get("phrases", []):
    print(" -", p)

# Testar o script_focusSocialTabs
print("\n--- Testando Acionamento do Foco nas Abas Sociais ---")
code_run_tabs = """
import api
app = api.getFocusObject().appModule
gesture_mock = None
app.script_focusSocialTabs(gesture_mock)
result = "script_focusSocialTabs executado com sucesso"
"""
call("execute_code", {"code": code_run_tabs})
time.sleep(0.4)
focus_tab = call("get_current_focus")
print("Objeto Focado após script_focusSocialTabs:")
print(f"Nome: '{focus_tab['result']['name']}' | Role: {focus_tab['result']['role']} | Class: '{focus_tab['result']['className']}'")

speech_tab = call("get_speech_history", {"count": 2})
print("Fala do NVDA:")
for p in speech_tab.get("result", {}).get("phrases", []):
    print(" -", p)
