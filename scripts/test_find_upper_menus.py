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

class Finder:
    account_menu = None
    social_tabs = []
    
    @classmethod
    def search(cls, o, depth=0):
        if not o or depth > 25: return
        ia2 = getattr(o, "IA2Attributes", None)
        ia2_dict = dict(ia2) if ia2 and hasattr(ia2, "items") else {}
        cls_name = ia2_dict.get("class", "")
        loc = getattr(o, "location", None)
        
        if "identity-menu-disclosure" in cls_name:
            cls.account_menu = {
                "name": o.name,
                "role": int(o.role),
                "left": loc.left if loc else 0,
                "top": loc.top if loc else 0
            }
            
        if "tab-button" in cls_name and loc and loc.left > 1500:
            cls.social_tabs.append({
                "name": o.name,
                "posinset": ia2_dict.get("posinset"),
                "left": loc.left,
                "top": loc.top
            })
            
        for c in (getattr(o, "children", None) or []):
            cls.search(c, depth + 1)

fg = api.getForegroundObject()
Finder.search(fg)
result = {
    "account_menu": Finder.account_menu,
    "social_tabs": Finder.social_tabs
}
"""

res = call("execute_code", {"code": code})
print(json.dumps(res, indent=2))
