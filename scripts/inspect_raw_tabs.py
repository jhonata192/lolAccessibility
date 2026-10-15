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
        return {"error": e.read().decode()}

code = """
import api

class Scanner:
    tabs_info = []
    @classmethod
    def scan(cls, o):
        loc = getattr(o, 'location', None)
        if loc and loc.top < 100 and getattr(o, 'role', 0) == 22:
            ia2 = getattr(o, 'IA2Attributes', None)
            ia2_d = dict(ia2) if (ia2 and hasattr(ia2, 'items')) else {}
            
            iacc_name = ""
            try:
                iacc_name = o.IAccessibleObject.accName(o.IAccessibleChildID)
            except Exception as e:
                iacc_name = str(e)
                
            cls.tabs_info.append({
                'iacc_name': iacc_name,
                'pos': ia2_d.get('posinset'),
                'setsize': ia2_d.get('setsize'),
                'class': ia2_d.get('class'),
                'left': loc.left,
                'top': loc.top
            })
        for c in (getattr(o, 'children', None) or []):
            cls.scan(c)

desktop = api.getDesktopObject()
for c in desktop.children:
    if 'riot client' in (getattr(c, 'name', '') or '').lower():
        Scanner.scan(c)
        break
result = Scanner.tabs_info
"""

res = call("execute_code", {"code": code})
print(json.dumps(res, indent=2, ensure_ascii=False))
