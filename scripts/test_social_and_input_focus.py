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

class SocialFocus:
    social_tab = None
    input_friend = None
    input_tag = None
    
    @classmethod
    def scan(cls, o, depth=0):
        if depth > 25: return
        ia2 = getattr(o, "IA2Attributes", None)
        ia2_dict = dict(ia2) if (ia2 and hasattr(ia2, "items")) else {}
        cls_name = ia2_dict.get("class", "")
        role = int(getattr(o, "role", 0))
        tag = ia2_dict.get("tag", "")
        loc = getattr(o, "location", None)
        ph = (ia2_dict.get("placeholder", "") or "").lower()
        
        if loc and loc.left > 1400 and loc.top > 100 and (role == 22 or "tab-button" in cls_name):
            if not cls.social_tab:
                cls.social_tab = o
                
        if tag == "input":
            if "nome do jogo" in ph and not cls.input_friend:
                cls.input_friend = o
            elif "tagline" in ph and not cls.input_tag:
                cls.input_tag = o
                
        for c in (getattr(o, "children", None) or []):
            cls.scan(c, depth + 1)

desktop = api.getDesktopObject()
for c in desktop.children:
    if "riot client" in (getattr(c, "name", "") or "").lower():
        SocialFocus.scan(c)
        break

res = {}
if SocialFocus.social_tab:
    t = SocialFocus.social_tab
    res["social_tab_name"] = t.name
    res["social_tab_pos"] = getattr(t, "positionInGroup", None)
    t.doAction()
    t.setFocus()
    res["focused_tab"] = True
else:
    res["focused_tab"] = False

result = res
"""

res = call("execute_code", {"code": code})
print("Focar Aba Social:", json.dumps(res.get("result", {}).get("result", {}), indent=2, ensure_ascii=False))

time.sleep(0.5)
focus = call("get_current_focus")
print("Novo Foco:", focus.get("result", {}).get("name"), "| RoleText:", focus.get("result", {}).get("roleText"))
history = call("get_speech_history", {"count": 3})
def safe_print(label, obj):
    s = f"{label} {obj}"
    print(s.encode("ascii", "replace").decode("ascii"))

safe_print("Fala do NVDA:", history.get("result", {}).get("phrases"))

# Agora focar o campo Nome do Jogo
code_input = """
import api

class InputFocus:
    input_friend = None
    @classmethod
    def scan(cls, o, depth=0):
        if cls.input_friend or depth > 25: return
        ia2 = getattr(o, "IA2Attributes", None)
        ia2_dict = dict(ia2) if (ia2 and hasattr(ia2, "items")) else {}
        tag = ia2_dict.get("tag", "")
        ph = (ia2_dict.get("placeholder", "") or "").lower()
        if tag == "input" and "nome do jogo" in ph:
            cls.input_friend = o
            return
        for c in (getattr(o, "children", None) or []):
            cls.scan(c, depth + 1)

desktop = api.getDesktopObject()
for c in desktop.children:
    if "riot client" in (getattr(c, "name", "") or "").lower():
        InputFocus.scan(c)
        break

res = {}
if InputFocus.input_friend:
    f = InputFocus.input_friend
    res["input_name"] = f.name
    res["input_desc"] = f.description
    f.doAction()
    f.setFocus()
    res["focused_input"] = True
else:
    res["focused_input"] = False

result = res
"""
res_input = call("execute_code", {"code": code_input})
safe_print("\nFocar Campo Nome do Jogo:", res_input.get("result", {}).get("result", {}))

time.sleep(0.5)
focus_input = call("get_current_focus")
safe_print("Novo Foco:", f"{focus_input.get('result', {}).get('name')} | Descrição: {focus_input.get('result', {}).get('description')}")
history_input = call("get_speech_history", {"count": 3})
safe_print("Fala do NVDA:", history_input.get("result", {}).get("phrases"))
