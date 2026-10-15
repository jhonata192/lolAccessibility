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
    return json.loads(resp.read().decode())["result"]

code = """
import api

class TabInspector:
    tabs = []
    
    @classmethod
    def find_tabs(cls, o, depth=0):
        if not o or depth > 20: return
        ia2 = getattr(o, "IA2Attributes", {})
        cls_name = ia2.get("class", "") if isinstance(ia2, dict) else str(ia2)
        loc = getattr(o, "location", None)
        
        if "tab-button" in cls_name and loc and loc.left > 1500:
            sub = []
            for c in (getattr(o, "children", None) or []):
                sub.append({
                    "name": c.name,
                    "role": int(c.role),
                    "class": c.IA2Attributes.get("class", "") if getattr(c, "IA2Attributes", None) else ""
                })
            cls.tabs.append({
                "name": o.name,
                "role": int(o.role),
                "roleText": getattr(o, "roleText", ""),
                "class": cls_name,
                "loc": f"L{loc.left}_T{loc.top}_W{loc.width}_H{loc.height}",
                "states": str(o.states),
                "children": sub
            })
        for child in (getattr(o, "children", None) or []):
            cls.find_tabs(child, depth + 1)

fg = api.getForegroundObject()
TabInspector.find_tabs(fg)
result = TabInspector.tabs
"""
res = call("execute_code", {"code": code})
print(json.dumps(res, indent=2))
