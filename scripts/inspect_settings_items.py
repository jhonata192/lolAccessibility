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
import api

class SettingsNavInspector:
    items = []
    
    @classmethod
    def walk(cls, o, depth=0):
        if not o or depth > 20: return
        ia2 = getattr(o, "IA2Attributes", {})
        cls_name = ia2.get("class", "") if isinstance(ia2, dict) else str(ia2)
        
        if "settings-navigation-item" in cls_name:
            sub = []
            for c in (getattr(o, "children", None) or []):
                clean_name = "".join(ch for ch in (c.name or "") if ord(ch) < 0xE000 or ord(ch) > 0xF8FF).strip()
                sub.append({
                    "name": clean_name,
                    "role": int(c.role),
                    "class": c.IA2Attributes.get("class", "") if getattr(c, "IA2Attributes", None) else ""
                })
            clean_o_name = "".join(ch for ch in (o.name or "") if ord(ch) < 0xE000 or ord(ch) > 0xF8FF).strip()
            cls.items.append({
                "name": clean_o_name,
                "role": int(o.role),
                "roleText": getattr(o, "roleText", ""),
                "class": cls_name,
                "children": sub
            })
        for child in (getattr(o, "children", None) or []):
            cls.walk(child, depth + 1)

fg = api.getForegroundObject()
SettingsNavInspector.walk(fg)
result = SettingsNavInspector.items
"""
res = call("execute_code", {"code": code})
print(f"Total navigation items: {len(res['result'])}")
for i, item in enumerate(res["result"]):
    print(f"[{i:02d}] Name: '{item['name']}' | Role: {item['role']} | Class: '{item['class']}' | Sub: {item['children']}")
