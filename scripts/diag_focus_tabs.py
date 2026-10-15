import urllib.request
import json

BASE_URL = "http://127.0.0.1:8765/action"
HEADERS = {
    "X-NVDA-Bridge-Token": "nvda-bridge-secret-change-me",
    "Content-Type": "application/json"
}

def call(action, params={}):
    req = urllib.request.Request(BASE_URL, data=json.dumps({"action": action, "params": params}).encode("utf-8"), headers=HEADERS)
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print("ERROR BODY:", e.read().decode())
        raise

code = """
import api

fg = api.getForegroundObject()
focus = api.getFocusObject()

res = {
    "fg_name": getattr(fg, "name", ""),
    "fg_role": int(getattr(fg, "role", 0)),
    "fg_app": str(getattr(fg, "appModule", "")),
    "focus_name": getattr(focus, "name", ""),
    "focus_role": int(getattr(focus, "role", 0)),
    "focus_app": str(getattr(focus, "appModule", ""))
}

# Procurar tab_target a partir de fg ou desktop
class Diag:
    tab_target = None
    @classmethod
    def find_hub_tab(cls, o, depth=0):
        if cls.tab_target or depth > 25:
            return
        loc = getattr(o, "location", None)
        role = getattr(o, "role", 0)
        ia2 = getattr(o, "IA2Attributes", None)
        cls_name = ia2.get("class", "") if (ia2 and hasattr(ia2, "items")) else ""
        if loc and 150 < loc.left < 1400 and loc.top < 100 and (role == 22 or "tab-button" in cls_name):
            cls.tab_target = o
            return
        for c in (getattr(o, "children", None) or []):
            cls.find_hub_tab(c, depth + 1)

Diag.find_hub_tab(fg)
if not Diag.tab_target:
    desktop = api.getDesktopObject()
    for c in desktop.children:
        if "riot client" in (getattr(c, "name", "") or "").lower():
            Diag.find_hub_tab(c)
            break

if Diag.tab_target:
    res["found_tab"] = Diag.tab_target.name
    Diag.tab_target.setFocus()
    res["set_focus_success"] = True
else:
    res["found_tab"] = None
    res["set_focus_success"] = False

result = res
"""

res = call("execute_code", {"code": code})
print(json.dumps(res.get("result", {}).get("result", {}), indent=2, ensure_ascii=False))

# Verificar foco agora
focus = call("get_current_focus")
print("Novo Foco:", focus.get("result", {}).get("name"), "| RoleText:", focus.get("result", {}).get("roleText"))
history = call("get_speech_history", {"count": 3})
print("Fala do NVDA:", history.get("result", {}).get("phrases"))
