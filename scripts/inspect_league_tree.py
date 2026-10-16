import urllib.request
import json

BASE_URL = "http://127.0.0.1:8765/action"
HEADERS = {
    "X-NVDA-Bridge-Token": "nvda-bridge-secret-change-me",
    "Content-Type": "application/json"
}

code = """
import api
import traceback

try:
    league_obj = None
    desktop = api.getDesktopObject()
    for child in desktop.children:
        pname = (getattr(child, "appModule", None) and getattr(child.appModule, "appName", "")) or ""
        if "leagueclientux" in pname.lower():
            league_obj = child
            break

    nodes = []

    def walk(obj, nodes_list, depth=0):
        if depth > 5:
            return
        name = (getattr(obj, "name", "") or "").strip()
        role = int(getattr(obj, "role", 0))
        role_text = getattr(obj, "roleText", "") or ""
        cls_name = getattr(obj, "windowClassName", "") or ""
        ia2 = getattr(obj, "IA2Attributes", None)
        ia2_dict = dict(ia2) if (ia2 and hasattr(ia2, "items")) else {}
        tag = ia2_dict.get("tag", "")
        html_class = ia2_dict.get("class", "")
        auto_id = getattr(obj, "UIAAutomationId", "") or ""
        loc = getattr(obj, "location", None)
        
        info = {
            "depth": depth,
            "name": name,
            "role": role,
            "roleText": role_text,
            "tag": tag,
            "class": html_class,
            "autoId": auto_id,
            "wClass": cls_name,
            "loc": [loc.left, loc.top, loc.width, loc.height] if loc else None
        }
        nodes_list.append(info)
        
        try:
            sub = getattr(obj, "children", []) or []
            for c in sub:
                walk(c, nodes_list, depth + 1)
        except Exception:
            pass

    if league_obj:
        walk(league_obj, nodes)

    result = {
        "found": bool(league_obj),
        "total_nodes": len(nodes),
        "sample": nodes[:40]
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
