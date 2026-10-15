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

code_drawer = """
import api

class DrawerInspector:
    elements = []
    
    @classmethod
    def walk(cls, o, depth=0):
        if not o or depth > 20: return
        import controlTypes
        role = getattr(o, "role", 0)
        name = (getattr(o, "name", "") or "").strip()
        ia2 = getattr(o, "IA2Attributes", {})
        cls_name = ia2.get("class", "") if isinstance(ia2, dict) else str(ia2)
        tag = ia2.get("tag", "") if isinstance(ia2, dict) else ""
        
        # Filtrar caracteres de icon font (Pua) do nome
        clean_name = "".join(ch for ch in name if ord(ch) < 0xE000 or ord(ch) > 0xF8FF).strip()
        
        if "setting" in cls_name.lower() or "riot-modal" in cls_name.lower():
            cls.elements.append({
                "name": clean_name,
                "role": int(role),
                "roleText": getattr(o, "roleText", ""),
                "class": cls_name,
                "tag": tag,
                "childCount": getattr(o, "childCount", 0)
            })
        for child in (getattr(o, "children", None) or []):
            cls.walk(child, depth + 1)

fg = api.getForegroundObject()
DrawerInspector.walk(fg)
result = DrawerInspector.elements
"""
res = call("execute_code", {"code": code_drawer})
print(f"Total settings drawer elements: {len(res['result'])}")
for el in res["result"]:
    print(f"Name: '{el['name']}' | Role: {el['role']} ({el['roleText']}) | Tag: <{el['tag']}> | Class: '{el['class']}'")
