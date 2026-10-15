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

class LiveVerifier:
    tabs = []
    inputs = []
    cards = []
    social_items = []
    
    @classmethod
    def scan(cls, o, depth=0):
        if depth > 25: return
        ia2 = getattr(o, "IA2Attributes", None)
        ia2_dict = dict(ia2) if (ia2 and hasattr(ia2, "items")) else {}
        cls_name = ia2_dict.get("class", "")
        role = int(getattr(o, "role", 0))
        tag = ia2_dict.get("tag", "")
        loc = getattr(o, "location", None)
        
        # Tabs
        if role == 22 or "tab-button" in cls_name:
            cls.tabs.append({
                "name": getattr(o, "name", ""),
                "roleText": getattr(o, "roleText", ""),
                "pos": getattr(o, "positionInGroup", None),
                "left": loc.left if loc else None
            })
            
        # Inputs
        if tag == "input" or role == 8:
            cls.inputs.append({
                "name": getattr(o, "name", ""),
                "desc": getattr(o, "description", ""),
                "roleText": getattr(o, "roleText", ""),
                "placeholder": ia2_dict.get("placeholder")
            })
            
        # Cards
        if "base-card-button" in cls_name or "video-button" in cls_name or "volume-button" in cls_name:
            cls.cards.append({
                "name": getattr(o, "name", ""),
                "roleText": getattr(o, "roleText", ""),
                "class": cls_name
            })
            
        # Social Items
        if "social-item" in cls_name and not any(k in cls_name for k in ("avatar", "heading", "caption")):
            cls.social_items.append({
                "name": getattr(o, "name", ""),
                "roleText": getattr(o, "roleText", "")
            })
            
        for c in (getattr(o, "children", None) or []):
            cls.scan(c, depth + 1)

desktop = api.getDesktopObject()
for c in desktop.children:
    if "riot client" in (getattr(c, "name", "") or "").lower():
        LiveVerifier.scan(c)
        break

result = {
    "tabs": LiveVerifier.tabs,
    "inputs": LiveVerifier.inputs,
    "cards": LiveVerifier.cards,
    "social_items": LiveVerifier.social_items
}
"""

res = call("execute_code", {"code": code})
print(json.dumps(res.get("result", {}).get("result", {}), indent=2, ensure_ascii=False))
