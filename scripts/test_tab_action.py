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

code = """
import api

class ActionTester:
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

desktop = api.getDesktopObject()
for c in desktop.children:
    if "riot client" in (getattr(c, "name", "") or "").lower():
        ActionTester.find_hub_tab(c)
        break

res = {}
if ActionTester.tab_target:
    t = ActionTester.tab_target
    res["tab_name"] = t.name
    # Tentar doAction
    try:
        t.doAction()
        res["doAction"] = True
    except Exception as e:
        res["doAction"] = str(e)
        
    try:
        t.setFocus()
        res["setFocus"] = True
    except Exception as e:
        res["setFocus"] = str(e)

result = res
"""

res = call("execute_code", {"code": code})
print(json.dumps(res.get("result", {}).get("result", {}), indent=2, ensure_ascii=False))

time.sleep(0.5)
focus = call("get_current_focus")
print("Novo Foco:", focus.get("result", {}).get("name"), "| RoleText:", focus.get("result", {}).get("roleText"))
history = call("get_speech_history", {"count": 3})
print("Fala do NVDA:", history.get("result", {}).get("phrases"))
