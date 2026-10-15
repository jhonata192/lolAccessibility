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

class Inspector:
    tabs = []
    
    @classmethod
    def find_tabs(cls, o, depth=0):
        if not o or depth > 20: return
        ia2 = getattr(o, "IA2Attributes", None)
        ia2_dict = dict(ia2) if ia2 and hasattr(ia2, "items") else {}
        cls_name = ia2_dict.get("class", "")
        loc = getattr(o, "location", None)
        if "tab-button" in cls_name and loc and loc.left > 1500:
            cls.tabs.append({
                "ia2": ia2_dict,
                "posInGroup": getattr(o, "positionInGroup", None)
            })
        for c in (getattr(o, "children", None) or []):
            cls.find_tabs(c, depth + 1)

fg = api.getForegroundObject()
Inspector.find_tabs(fg)
result = Inspector.tabs
"""
res = call("execute_code", {"code": code})
print(json.dumps(res, indent=2))
