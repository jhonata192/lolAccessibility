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

class SocialItemInspector:
    items = []
    @classmethod
    def scan(cls, o, depth=0):
        if depth > 25: return
        ia2 = getattr(o, "IA2Attributes", None)
        ia2_dict = dict(ia2) if (ia2 and hasattr(ia2, "items")) else {}
        cls_name = ia2_dict.get("class", "")
        
        if "social-item" in cls_name:
            sub = []
            for c in (getattr(o, "children", None) or []):
                c_ia2 = getattr(c, "IA2Attributes", None)
                c_dict = dict(c_ia2) if (c_ia2 and hasattr(c_ia2, "items")) else {}
                sub.append({
                    "name": getattr(c, "name", ""),
                    "role": int(getattr(c, "role", 0)),
                    "class": c_dict.get("class", ""),
                    "tag": c_dict.get("tag", "")
                })
            cls.items.append({
                "name": getattr(o, "name", ""),
                "role": int(getattr(o, "role", 0)),
                "class": cls_name,
                "children": sub
            })
        for c in (getattr(o, "children", None) or []):
            cls.scan(c, depth + 1)

desktop = api.getDesktopObject()
for c in desktop.children:
    if "riot client" in (getattr(c, "name", "") or "").lower():
        SocialItemInspector.scan(c)
        break
result = SocialItemInspector.items
"""

res = call("execute_code", {"code": code})
print(json.dumps(res.get("result", {}).get("result", []), indent=2, ensure_ascii=False))
