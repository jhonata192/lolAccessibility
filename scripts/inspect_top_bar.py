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
class TopBarInspector:
    elements = []
    
    @classmethod
    def parse_ia2(cls, ia2):
        if not ia2: return {}
        if isinstance(ia2, dict): return ia2
        res = {}
        for part in str(ia2).split(";"):
            if ":" in part:
                k, v = part.split(":", 1)
                res[k.strip()] = v.strip()
        return res

    @classmethod
    def walk(cls, o, depth=0):
        if not o or depth > 18:
            return
        import controlTypes
        loc = getattr(o, "location", None)
        role = getattr(o, "role", 0)
        name = (getattr(o, "name", "") or "").strip()
        ia2 = cls.parse_ia2(getattr(o, "IA2Attributes", None))
        cls_name = ia2.get("class", "")
        tag = ia2.get("tag", "")
        auto_id = getattr(o, "UIAAutomationId", "") or ia2.get("id", "") or ia2.get("data-testid", "")
        
        # Elementos no topo da janela (top < 150)
        if loc and loc.top < 150 and loc.width > 0 and loc.height > 0:
            is_interactive = role in (
                controlTypes.Role.BUTTON, controlTypes.Role.LINK, controlTypes.Role.MENUITEM,
                controlTypes.Role.POPUPMENU, controlTypes.Role.CHECKBOX, controlTypes.Role.RADIOBUTTON,
                controlTypes.Role.COMBOBOX, controlTypes.Role.TAB
            ) or any(k in cls_name.lower() for k in ["button", "menu", "profile", "avatar", "account", "identity", "setting", "notif", "download", "presence", "close", "min", "max", "header", "nav"])
            
            if is_interactive or (name and len(name) > 1):
                cls.elements.append({
                    "depth": depth,
                    "name": name,
                    "role": int(role),
                    "roleText": getattr(o, "roleText", ""),
                    "class": cls_name,
                    "tag": tag,
                    "id": auto_id,
                    "left": loc.left,
                    "top": loc.top,
                    "width": loc.width,
                    "height": loc.height,
                    "childCount": getattr(o, "childCount", 0)
                })

        for child in (getattr(o, "children", None) or []):
            cls.walk(child, depth + 1)

import api
fg = api.getForegroundObject()
TopBarInspector.walk(fg)

# Ordenar por top e depois left
TopBarInspector.elements.sort(key=lambda e: (e["top"], e["left"]))

result = {
    "fg_name": fg.name if fg else None,
    "count": len(TopBarInspector.elements),
    "elements": TopBarInspector.elements
}
"""

res = call("execute_code", {"code": code})
print(f"Total top elements found: {res['result']['count']}")
for i, el in enumerate(res['result']['elements']):
    print(f"[{i:02d}] Name: '{el['name']}' | Role: {el['role']} ({el['roleText']}) | Class: '{el['class']}' | Tag: <{el['tag']}> | ID: '{el['id']}' | Pos: L{el['left']}, T{el['top']}, W{el['width']}, H{el['height']}")
