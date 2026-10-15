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

class HeaderInspector:
    elements = []
    
    @classmethod
    def find_header(cls, o, depth=0):
        if not o or depth > 20: return
        ia2 = getattr(o, "IA2Attributes", {})
        cls_name = ia2.get("class", "") if isinstance(ia2, dict) else str(ia2)
        if "app-header" in cls_name:
            # dump all descendants of header
            def dump(node, d=0):
                if not node or d > 10: return
                loc = getattr(node, "location", None)
                loc_str = f"L{loc.left}_T{loc.top}_W{loc.width}_H{loc.height}" if loc else ""
                n_ia2 = getattr(node, "IA2Attributes", {})
                n_cls = n_ia2.get("class", "") if isinstance(n_ia2, dict) else str(n_ia2)
                cls.elements.append({
                    "depth": d,
                    "name": (getattr(node, "name", "") or "").strip(),
                    "role": int(getattr(node, "role", 0)),
                    "roleText": getattr(node, "roleText", ""),
                    "class": n_cls,
                    "loc": loc_str,
                    "childCount": getattr(node, "childCount", 0)
                })
                for c in (getattr(node, "children", None) or []):
                    dump(c, d + 1)
            dump(o)
            return
        for child in (getattr(o, "children", None) or []):
            cls.find_header(child, depth + 1)

fg = api.getForegroundObject()
HeaderInspector.find_header(fg)
result = HeaderInspector.elements
"""
res = call("execute_code", {"code": code})
print(f"Header subtree count: {len(res['result'])}")
for el in res['result']:
    indent = "  " * el["depth"]
    print(f"{indent}[Role {el['role']} ({el['roleText']})] Name: '{el['name']}' | Class: '{el['class']}' | Loc: {el['loc']}")
