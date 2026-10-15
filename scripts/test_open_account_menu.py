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

code_open = """
import api

class Opener:
    target = None
    @classmethod
    def search(cls, o, depth=0):
        if not o or depth > 25 or cls.target: return
        ia2 = getattr(o, "IA2Attributes", None)
        ia2_dict = dict(ia2) if ia2 and hasattr(ia2, "items") else {}
        cls_name = ia2_dict.get("class", "")
        if "identity-menu-disclosure" in cls_name:
            cls.target = o
            return
        for c in (getattr(o, "children", None) or []):
            cls.search(c, depth + 1)

fg = api.getForegroundObject()
Opener.search(fg)
res = {}
if Opener.target:
    res["found"] = True
    Opener.target.setFocus()
    try:
        Opener.target.doAction()
        res["action_done"] = True
    except Exception as e:
        res["err"] = str(e)
else:
    res["found"] = False
result = res
"""
res = call("execute_code", {"code": code_open})
print("Open result:", json.dumps(res, indent=2))

time.sleep(0.5)

code_items = """
import api

class ItemsCollector:
    items = []
    @classmethod
    def search(cls, o, depth=0):
        if not o or depth > 25: return
        ia2 = getattr(o, "IA2Attributes", None)
        ia2_dict = dict(ia2) if ia2 and hasattr(ia2, "items") else {}
        cls_name = ia2_dict.get("class", "")
        if "identity-menu-item" in cls_name or "menu-item" in cls_name:
            cls.items.append({
                "name": o.name,
                "role": int(o.role),
                "class": cls_name,
                "location": str(getattr(o, "location", None))
            })
        for c in (getattr(o, "children", None) or []):
            cls.search(c, depth + 1)

fg = api.getForegroundObject()
ItemsCollector.search(fg)
result = ItemsCollector.items
"""
res_items = call("execute_code", {"code": code_items})
print("Items discovered:", json.dumps(res_items, indent=2))
