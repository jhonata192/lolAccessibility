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

code_click_lol = """
import api

class LolClicker:
    target = None
    @classmethod
    def scan(cls, o, depth=0):
        if cls.target or depth > 20: return
        n = getattr(o, "name", "") or ""
        ia2 = getattr(o, "IA2Attributes", None)
        cls_name = ia2.get("class", "") if (ia2 and hasattr(ia2, "items")) else ""
        if "League of Legends" in n and "disclosure" in cls_name:
            cls.target = o
            return
        for c in (getattr(o, "children", None) or []):
            cls.scan(c, depth + 1)

desktop = api.getDesktopObject()
for c in desktop.children:
    if "riot client" in (getattr(c, "name", "") or "").lower():
        LolClicker.scan(c)
        break

res = {}
if LolClicker.target:
    LolClicker.target.setFocus()
    try:
        LolClicker.target.doAction()
        res["clicked"] = True
    except Exception as e:
        res["err"] = str(e)
    res["name"] = LolClicker.target.name
else:
    res["clicked"] = False
result = res
"""
res = call("execute_code", {"code": code_click_lol})
print("Click LoL result:", json.dumps(res, indent=2))

time.sleep(0.5)

# O que o NVDA falou após o clique?
speech = call("get_speech_history", {"count": 3})
print("\nFala do NVDA:")
for p in speech.get("result", {}).get("phrases", []):
    print(" -", p.encode("ascii", errors="replace").decode())

# Qual o objeto focado agora?
focus = call("get_current_focus")
print("\nNovo foco:")
print(f"Nome: '{focus.get('result', {}).get('name')}' | Role: {focus.get('result', {}).get('role')} | Class: '{focus.get('result', {}).get('className')}'")
