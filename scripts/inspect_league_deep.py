import urllib.request
import json

BASE_URL = "http://127.0.0.1:8765/action"
HEADERS = {
    "X-NVDA-Bridge-Token": "nvda-bridge-secret-change-me",
    "Content-Type": "application/json"
}

code = """
import NVDAObjects.IAccessible
import traceback

try:
    hwnd = 16974194
    root = NVDAObjects.IAccessible.getNVDAObjectFromEvent(hwnd, -4, 0)

    tree = []

    stack = [(root, 0)]
    while stack and len(tree) < 150:
        obj, depth = stack.pop(0)
        if depth > 10:
            continue
        name = getattr(obj, "name", "") or ""
        role = int(getattr(obj, "role", 0))
        role_text = getattr(obj, "roleText", "") or ""
        cls_name = getattr(obj, "windowClassName", "") or ""
        ia2 = getattr(obj, "IA2Attributes", None)
        ia2_dict = dict(ia2) if (ia2 and hasattr(ia2, "items")) else {}
        tag = ia2_dict.get("tag", "")
        html_class = ia2_dict.get("class", "")
        auto_id = getattr(obj, "UIAAutomationId", "") or ""
        
        node = {
            "d": depth,
            "n": name,
            "r": role,
            "rt": role_text,
            "tag": tag,
            "cls": html_class,
            "id": auto_id,
            "wcls": cls_name,
            "cc": getattr(obj, "childCount", 0)
        }
        tree.append(node)
        
        sub = []
        try:
            sub = getattr(obj, "children", []) or []
        except Exception:
            pass
        for c in sub:
            stack.append((c, depth + 1))

    result = {
        "total": len(tree),
        "tree": tree[:60]
    }
except Exception as e:
    result = {
        "error": str(e),
        "tb": traceback.format_exc()
    }
"""

req = urllib.request.Request(
    BASE_URL,
    data=json.dumps({"action": "execute_code", "params": {"code": code}}).encode("utf-8"),
    headers=HEADERS
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    print(json.dumps(data.get("result", {}).get("result", {}), indent=2, ensure_ascii=False))
