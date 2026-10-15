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

class SideNavScanner:
    items = []
    @classmethod
    def scan(cls, o, depth=0):
        if depth > 20: return
        ia2 = getattr(o, "IA2Attributes", None)
        ia2_dict = dict(ia2) if (ia2 and hasattr(ia2, "items")) else {}
        cls_name = ia2_dict.get("class", "")
        loc = getattr(o, "location", None)
        
        # Elementos na barra lateral esquerda (Left < 300)
        if loc and loc.left < 300:
            name = (getattr(o, "name", "") or "").strip()
            role = int(o.role)
            if role in (9, 22, 30, 86, 102) or any(k in cls_name for k in ("nav", "game", "button", "item", "disclosure")):
                clean_name = "".join(ch for ch in name if ord(ch) < 0xE000 or ord(ch) > 0xF8FF).strip()
                cls.items.append({
                    "name": clean_name,
                    "role": role,
                    "roleText": getattr(o, "roleText", ""),
                    "class": cls_name,
                    "loc": f"L{loc.left}_T{loc.top}_W{loc.width}_H{loc.height}",
                    "states": [str(s).split(".")[-1].split(":")[0] for s in getattr(o, "states", set())]
                })
        for c in (getattr(o, "children", None) or []):
            cls.scan(c, depth + 1)

desktop = api.getDesktopObject()
for c in desktop.children:
    if "riot client" in (getattr(c, "name", "") or "").lower():
        SideNavScanner.scan(c)
        break
result = SideNavScanner.items
"""
res = call("execute_code", {"code": code})
items = res.get("result", {}).get("result", [])
print(f"Total side nav items found: {len(items)}")
for i, item in enumerate(items[:25]):
    if item['name'] or item['class']:
        print(f"[{i:02d}] Name: '{item['name']}' | Role: {item['role']} ({item['roleText']}) | Class: '{item['class']}' | Loc: {item['loc']}")
