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

class TabSeeker:
    tabs = []
    @classmethod
    def scan(cls, o):
        loc = getattr(o, 'location', None)
        ia2 = getattr(o, 'IA2Attributes', None)
        cls_name = ia2.get('class', '') if (ia2 and hasattr(ia2, 'items')) else ''
        if loc and loc.left > 1400 and loc.top > 100 and (getattr(o, 'role', 0) == 22 or 'tab-button' in cls_name):
            cls.tabs.append(o)
        for c in (getattr(o, 'children', []) or []):
            cls.scan(c)

desktop = api.getDesktopObject()
for c in desktop.children:
    if 'riot client' in (getattr(c, 'name', '') or '').lower():
        TabSeeker.scan(c)
        break

res = {}
if len(TabSeeker.tabs) >= 3:
    req_tab = TabSeeker.tabs[2]
    res['target'] = req_tab.name
    req_tab.doAction()
    req_tab.setFocus()
    res['success'] = True
else:
    res['success'] = False
result = res
"""

res = call("execute_code", {"code": code})
print("Seleção da Aba:", res.get("result", {}).get("result"))

time.sleep(0.6)
focus = call("get_current_focus")
print("Novo Foco:", focus.get("result", {}).get("name"), "| RoleText:", focus.get("result", {}).get("roleText"))
history = call("get_speech_history", {"count": 3})
print("Fala do NVDA:", [p.encode('ascii', 'replace').decode('ascii') for p in history.get('result', {}).get('phrases', [])])
