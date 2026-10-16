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

    items = []
    stack = [(root, 0)]
    while stack:
        obj, depth = stack.pop(0)
        name = getattr(obj, "name", "") or ""
        role = int(getattr(obj, "role", 0))
        role_text = getattr(obj, "roleText", "") or ""
        ia2 = getattr(obj, "IA2Attributes", None)
        ia2_dict = dict(ia2) if (ia2 and hasattr(ia2, "items")) else {}
        tag = ia2_dict.get("tag", "")
        html_class = ia2_dict.get("class", "")
        auto_id = getattr(obj, "UIAAutomationId", "") or ""
        
        # Collect buttons, headings, text, or elements with interesting classes
        is_interactive = role in (9, 10, 11, 12, 14, 15, 22, 30, 37, 8, 86) or name
        if is_interactive and (name or html_class or auto_id):
            items.append({
                "d": depth,
                "n": name,
                "r": role,
                "rt": role_text,
                "tag": tag,
                "cls": html_class,
                "id": auto_id
            })
        
        sub = []
        try:
            sub = getattr(obj, "children", []) or []
        except Exception:
            pass
        for c in sub:
            stack.append((c, depth + 1))

    result = {
        "total_items": len(items),
        "items": items[:80]
    }
except Exception as e:
    result = {"error": str(e), "tb": traceback.format_exc()}
"""

req = urllib.request.Request(
    BASE_URL,
    data=json.dumps({"action": "execute_code", "params": {"code": code}}).encode("utf-8"),
    headers=HEADERS
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
with open("temp_league_elements.json", "w", encoding="utf-8") as f:
    json.dump(data.get("result", {}).get("result", {}), f, indent=2, ensure_ascii=False)
print("Saved to temp_league_elements.json. Total:", data.get("result", {}).get("result", {}).get("total_items"))
