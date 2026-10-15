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

class InputFocuser:
    target = None
    @classmethod
    def scan(cls, o):
        ia2 = getattr(o, 'IA2Attributes', None)
        ia2_dict = dict(ia2) if (ia2 and hasattr(ia2, 'items')) else {}
        if ia2_dict.get('placeholder') == 'Nome do jogo':
            cls.target = o
            return
        for c in (getattr(o, 'children', []) or []):
            if not cls.target:
                cls.scan(c)

desktop = api.getDesktopObject()
for c in desktop.children:
    if 'riot client' in (getattr(c, 'name', '') or '').lower():
        InputFocuser.scan(c)
        break

res = {}
if InputFocuser.target:
    inp = InputFocuser.target
    res['name'] = inp.name
    res['desc'] = inp.description
    inp.setFocus()
    res['focused'] = True
else:
    res['focused'] = False
result = res
"""

res = call("execute_code", {"code": code})
print("Focar Input:", res.get("result", {}).get("result"))

time.sleep(0.6)
focus = call("get_current_focus")
print("Novo Foco:", focus.get("result", {}).get("name"), "| RoleText:", focus.get("result", {}).get("roleText"))
print("Descricao:", focus.get("result", {}).get("description"))
history = call("get_speech_history", {"count": 3})
print("Fala do NVDA:", [p.encode('ascii', 'replace').decode('ascii') for p in history.get('result', {}).get('phrases', [])])
