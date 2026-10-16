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
    while stack and len(items) < 1500:
        o, d = stack.pop(0)
        ia2 = getattr(o, 'IA2Attributes', None)
        ia2_d = dict(ia2) if ia2 and hasattr(ia2, 'items') else {}
        n = getattr(o, 'name', '') or ''
        cls = ia2_d.get('class', '') or ''
        tag = ia2_d.get('tag', '') or ''
        role = int(getattr(o, 'role', 0))
        cc = getattr(o, 'childCount', 0)
        auto_id = getattr(o, 'UIAAutomationId', '') or ''
        
        # Only keep interesting elements or containers with classes/names
        if n or cls or auto_id or role in (8, 9, 10, 11, 14, 25, 27, 30, 48, 56):
            items.append({'d': d, 'tag': tag, 'cls': cls, 'n': n, 'role': role, 'id': auto_id, 'cc': cc})
            
        children = []
        try:
            children = getattr(o, 'children', []) or []
        except Exception:
            pass
        for c in children:
            stack.append((c, d + 1))

    result = items
except Exception as e:
    result = {'error': str(e), 'tb': traceback.format_exc()}
"""

req = urllib.request.Request(
    BASE_URL,
    data=json.dumps({"action": "execute_code", "params": {"code": code}}).encode("utf-8"),
    headers=HEADERS
)

try:
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode("utf-8"))
        items = res.get("result", {}).get("result", [])
        print(f"Total elements at depth <= 5: {len(items)}")
        with open("temp_league_tree.json", "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
except Exception as e:
    print(f"Error: {e}")
