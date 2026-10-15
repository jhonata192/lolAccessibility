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

class CentralScanner:
    elements = []
    @classmethod
    def scan(cls, o, depth=0):
        if depth > 22: return
        ia2 = getattr(o, "IA2Attributes", None)
        ia2_dict = dict(ia2) if (ia2 and hasattr(ia2, "items")) else {}
        cls_name = ia2_dict.get("class", "")
        tag = ia2_dict.get("tag", "")
        loc = getattr(o, "location", None)
        if loc and 150 < loc.left < 1400:
            name = (getattr(o, "name", "") or "").strip()
            role = int(o.role)
            clean = "".join(ch for ch in name if ord(ch) < 0xE000 or ord(ch) > 0xF8FF).strip()
            if role in (9, 22, 11, 8, 10, 30) or any(k in cls_name for k in ("cta", "button", "tab", "item", "game", "play", "card")):
                cls.elements.append({
                    "name": clean[:70],
                    "role": role,
                    "roleText": getattr(o, "roleText", ""),
                    "class": cls_name[:50],
                    "tag": tag,
                    "loc": f"L{loc.left}_T{loc.top}_W{loc.width}_H{loc.height}"
                })
        for c in (getattr(o, "children", None) or []):
            cls.scan(c, depth + 1)

desktop = api.getDesktopObject()
for c in desktop.children:
    if "riot client" in (getattr(c, "name", "") or "").lower():
        CentralScanner.scan(c)
        break
result = CentralScanner.elements
"""
res = call("execute_code", {"code": code})
items = res.get("result", {}).get("result", [])
print(f"Total central items found: {len(items)}")
for i, el in enumerate(items[:20]):
    print(f"[{i:02d}] Name: '{el['name']}' | Role: {el['role']} ({el['roleText']}) | Class: '{el['class']}'")
