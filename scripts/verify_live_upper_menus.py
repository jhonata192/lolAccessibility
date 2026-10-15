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

print("=== VERIFICAÇÃO AO VIVO DOS MENUS SUPERIORES NO RIOT CLIENT ===")

# 1. Inspecionar o Account Menu e as Social Tabs na árvore ativa
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
            
        if "tab-button" in cls_name and loc and loc.left > 1500:
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
print("Resultados da árvore de acessibilidade:")
print(json.dumps(res["result"], indent=2, ensure_ascii=False))

# 2. Testar foco direto no Account Menu
print("\n--- Testando Foco no Menu da Conta ---")
code_focus_acc = """
import api
target = None
def find_acc(o, depth=0):
    global target
    if target or depth > 25: return
    ia2 = getattr(o, "IA2Attributes", None)
    cls_name = ia2.get("class", "") if (ia2 and hasattr(ia2, "items")) else ""
    if "identity-menu-disclosure" in cls_name:
        target = o
        return
    for c in (getattr(o, "children", None) or []):
        find_acc(c, depth + 1)
fg = api.getForegroundObject()
find_acc(fg)
if target:
    target.setFocus()
    result = {"focused": True, "name": target.name, "role": int(target.role), "roleText": getattr(target, "roleText", "")}
else:
    result = {"focused": False}
"""
res_acc = call("execute_code", {"code": code_focus_acc})
print("Foco no Menu da Conta:", json.dumps(res_acc["result"], indent=2, ensure_ascii=False))

# Verificar última fala do NVDA
time.sleep(0.3)
sp_acc = call("get_last_speech")
print("NVDA Falou:", sp_acc["result"]["last_spoken"])

# 3. Testar foco na Guia Social (Amigos)
print("\n--- Testando Foco na Guia Social ---")
code_focus_tab = """
import api, controlTypes
target = None
def find_tab(o, depth=0):
    global target
    if target or depth > 25: return
    ia2 = getattr(o, "IA2Attributes", None)
    cls_name = ia2.get("class", "") if (ia2 and hasattr(ia2, "items")) else ""
    loc = getattr(o, "location", None)
    if "tab-button" in cls_name and loc and loc.left > 1400:
        target = o
        return
    for c in (getattr(o, "children", None) or []):
        find_tab(c, depth + 1)
fg = api.getForegroundObject()
find_tab(fg)
if target:
    target.setFocus()
    result = {"focused": True, "name": target.name, "role": int(target.role), "roleText": getattr(target, "roleText", ""), "posInGroup": getattr(target, "positionInGroup", None)}
else:
    result = {"focused": False}
"""
res_tab = call("execute_code", {"code": code_focus_tab})
print("Foco na Guia Social:", json.dumps(res_tab["result"], indent=2, ensure_ascii=False))

time.sleep(0.3)
sp_tab = call("get_last_speech")
print("NVDA Falou:", sp_tab["result"]["last_spoken"])
