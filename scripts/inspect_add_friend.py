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

class Scanner:
    elements = []
    @classmethod
    def scan(cls, o, depth=0):
        if depth > 22: return
        ia2 = getattr(o, "IA2Attributes", None)
        ia2_dict = dict(ia2) if (ia2 and hasattr(ia2, "items")) else {}
        cls_name = ia2_dict.get("class", "")
        tag = ia2_dict.get("tag", "")
        if "add-friend" in cls_name:
            sub = []
            for c in (getattr(o, "children", None) or []):
                sub.append({
                    "name": c.name,
                    "role": int(c.role),
                    "tag": getattr(c, "IA2Attributes", {}).get("tag", "") if getattr(c, "IA2Attributes", None) else "",
                    "class": getattr(c, "IA2Attributes", {}).get("class", "") if getattr(c, "IA2Attributes", None) else "",
                    "value": getattr(c, "value", "")
                })
            cls.elements.append({
                "name": o.name,
                "role": int(o.role),
                "class": cls_name,
                "tag": tag,
                "sub": sub
            })
        for c in (getattr(o, "children", None) or []):
            cls.scan(c, depth + 1)

desktop = api.getDesktopObject()
for c in desktop.children:
    if "riot client" in (getattr(c, "name", "") or "").lower():
        Scanner.scan(c)
        break
result = Scanner.elements
"""
res = call("execute_code", {"code": code})
print(json.dumps(res.get("result", {}).get("result", []), indent=2))
