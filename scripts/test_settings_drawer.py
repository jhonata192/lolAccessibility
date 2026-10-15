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

code = """
import api

class SettingsClicker:
    target = None
    
    @classmethod
    def find_settings(cls, o, depth=0):
        if not o or depth > 22 or cls.target: return
        name = (getattr(o, "name", "") or "").strip().lower()
        ia2 = getattr(o, "IA2Attributes", {})
        cls_name = ia2.get("class", "") if isinstance(ia2, dict) else str(ia2)
        if "configura" in name or "setting" in cls_name.lower():
            if "item" in cls_name.lower() or "button" in cls_name.lower():
                cls.target = o
                return
        for child in (getattr(o, "children", None) or []):
            cls.find_settings(child, depth + 1)

fg = api.getForegroundObject()
SettingsClicker.find_settings(fg)
target = SettingsClicker.find_settings(fg) or SettingsClicker.target

info = {}
if target:
    info["found"] = True
    info["name"] = target.name
    info["role"] = int(target.role)
    info["class"] = target.IA2Attributes.get("class", "") if getattr(target, "IA2Attributes", None) else ""
    target.setFocus()
    try:
        target.doAction()
        info["action_done"] = True
    except Exception as e:
        info["action_err"] = str(e)
else:
    info["found"] = False

result = info
"""
res = call("execute_code", {"code": code})
print("Settings click result:", json.dumps(res, indent=2))

time.sleep(0.6)

# Inspecionar se abriu o drawer/modal de Configurações
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
        
        if "setting" in cls_name.lower() or "drawer" in cls_name.lower() or "modal" in cls_name.lower() or "dialog" in cls_name.lower() or "config" in cls_name.lower():
            cls.elements.append({
                "name": name,
                "role": int(role),
                "roleText": getattr(o, "roleText", ""),
                "class": cls_name,
                "childCount": getattr(o, "childCount", 0)
            })
        for child in (getattr(o, "children", None) or []):
            cls.walk(child, depth + 1)

fg = api.getForegroundObject()
DrawerInspector.walk(fg)
result = DrawerInspector.elements
"""
res_drawer = call("execute_code", {"code": code_drawer})
print(f"\nSettings/Drawer elements found: {len(res_drawer['result'])}")
for el in res_drawer["result"]:
    print(f"Name: '{el['name']}' | Role: {el['role']} ({el['roleText']}) | Class: '{el['class']}'")
