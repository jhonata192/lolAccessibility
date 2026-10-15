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
    return json.loads(resp.read().decode())["result"]

code_inspect = """
import api

class MenuWalker:
    menu_items = []
    
    @classmethod
    def walk(cls, o, depth=0):
        if not o or depth > 22: return
        import controlTypes
        role = getattr(o, "role", 0)
        name = (getattr(o, "name", "") or "").strip()
        ia2 = getattr(o, "IA2Attributes", {})
        cls_name = ""
        if isinstance(ia2, dict): cls_name = ia2.get("class", "")
        else: cls_name = str(ia2)
        
        lower_cls = cls_name.lower()
        if "menu" in lower_cls or "identity" in lower_cls or "item" in lower_cls or "setting" in lower_cls or "status" in lower_cls or "signout" in lower_cls or "logout" in lower_cls or role in (controlTypes.Role.MENUITEM, controlTypes.Role.POPUPMENU):
            cls.menu_items.append({
                "name": name,
                "role": int(role),
                "roleText": getattr(o, "roleText", ""),
                "class": cls_name,
                "childCount": getattr(o, "childCount", 0)
            })
        for child in (getattr(o, "children", None) or []):
            cls.walk(child, depth + 1)

fg = api.getForegroundObject()
MenuWalker.walk(fg)
result = MenuWalker.menu_items
"""
res2 = call("execute_code", {"code": code_inspect})
print(f"\nTotal menu items discovered: {len(res2['result'])}")
for i, item in enumerate(res2["result"]):
    print(f"[{i:02d}] Name: '{item['name']}' | Role: {item['role']} ({item['roleText']}) | Class: '{item['class']}'")
