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

    nav_items = []
    stack = [(root, 0)]
    while stack:
        obj, depth = stack.pop(0)
        cls_name = getattr(obj, "windowClassName", "") or ""
        ia2 = getattr(obj, "IA2Attributes", None)
        ia2_dict = dict(ia2) if (ia2 and hasattr(ia2, "items")) else {}
        html_class = ia2_dict.get("class", "")
        tag = ia2_dict.get("tag", "")
        name = getattr(obj, "name", "") or ""
        role = int(getattr(obj, "role", 0))
        auto_id = getattr(obj, "UIAAutomationId", "") or ""
        
        is_match = "rcp-fe-lol-navigation" in html_class
        if not is_match:
            target_str = (html_class + " " + auto_id + " " + tag).lower()
            for k in ["navigation", "navbar", "play-button", "currency", "wallet", "parties", "social", "status", "tab", "button"]:
                if k in target_str:
                    is_match = True
                    break
        
        if is_match:
            nav_items.append({
                "d": depth,
                "n": name,
                "r": role,
                "rt": getattr(obj, "roleText", ""),
                "tag": tag,
                "cls": html_class,
                "id": auto_id,
                "cc": getattr(obj, "childCount", 0)
            })
        
        sub = []
        try:
            sub = getattr(obj, "children", []) or []
        except Exception:
            pass
        for c in sub:
            stack.append((c, depth + 1))

    result = {
        "count": len(nav_items),
        "items": nav_items[:100]
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
with open("temp_league_nav.json", "w", encoding="utf-8") as f:
    json.dump(data.get("result", {}).get("result", {}), f, indent=2, ensure_ascii=False)
print("Saved to temp_league_nav.json. Count:", data.get("result", {}).get("result", {}).get("count"))
