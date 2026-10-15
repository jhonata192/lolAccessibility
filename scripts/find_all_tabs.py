import urllib.request
import json

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

class TabFinder:
    found = []
    @classmethod
    def scan(cls, o, depth=0):
        if depth > 25: return
        ia2 = getattr(o, "IA2Attributes", None)
        ia2_dict = dict(ia2) if (ia2 and hasattr(ia2, "items")) else {}
        cls_name = ia2_dict.get("class", "")
        role = int(getattr(o, "role", 0))
        loc = getattr(o, "location", None)
        
        if role == 22 or "tab" in cls_name.lower():
            cls.found.append({
                "name": getattr(o, "name", ""),
                "role": role,
                "class": cls_name,
                "pos": ia2_dict.get("posinset"),
                "setsize": ia2_dict.get("setsize"),
                "loc": f"L{loc.left}_T{loc.top}_W{loc.width}_H{loc.height}" if loc else None
            })
        for c in (getattr(o, "children", None) or []):
            cls.scan(c, depth + 1)

desktop = api.getDesktopObject()
for c in desktop.children:
    if "riot client" in (getattr(c, "name", "") or "").lower():
        TabFinder.scan(c)
        break
result = TabFinder.found
"""

res = call("execute_code", {"code": code})
tabs = res.get("result", {}).get("result", [])
print(f"Total tabs found: {len(tabs)}")
for t in tabs:
    print(t)
