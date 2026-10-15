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
    return json.loads(resp.read().decode())

code = """
import traceback
try:
    import api, controlTypes

    class ClientScanner:
        @classmethod
        def find_riot(cls):
            desktop = api.getDesktopObject()
            for child in desktop.children:
                child_name = (getattr(child, "name", "") or "").lower()
                if "riot" in child_name:
                    return child
            return None

        @classmethod
        def scan_tree(cls, obj, depth=0, max_depth=15, collected=None):
            if collected is None:
                collected = []
            if depth > max_depth or not obj:
                return collected
            
            try:
                name = getattr(obj, "name", "") or ""
                role = getattr(obj, "role", 0)
                role_text = getattr(obj, "roleText", "") or ""
                states = [str(s) for s in (getattr(obj, "states", set()) or set())]
                ia2 = getattr(obj, "IA2Attributes", None)
                ia2_dict = dict(ia2) if (ia2 and hasattr(ia2, "items")) else {}
                cls_name = ia2_dict.get("class", "") or getattr(obj, "className", "") or ""
                tag = ia2_dict.get("tag", "")
                auto_id = ia2_dict.get("id", "") or getattr(obj, "UIAAutomationId", "") or ""
                loc = getattr(obj, "location", None)
                loc_tuple = (loc.left, loc.top, loc.width, loc.height) if loc else None

                collected.append({
                    "depth": depth,
                    "name": name,
                    "role": int(role) if hasattr(role, "value") else int(role or 0),
                    "role_text": str(role_text),
                    "class": str(cls_name),
                    "tag": str(tag),
                    "id": str(auto_id),
                    "states": states,
                    "location": loc_tuple,
                    "type": type(obj).__name__
                })
            except Exception as item_err:
                pass

            for child in (getattr(obj, "children", []) or []):
                cls.scan_tree(child, depth + 1, max_depth, collected)
                
            return collected

    riot_win = ClientScanner.find_riot()
    if not riot_win:
        result = {"error": "Riot window not found"}
    else:
        items = ClientScanner.scan_tree(riot_win)
        result = {
            "title": riot_win.name,
            "count": len(items),
            "items": items
        }
except Exception:
    result = {"error": traceback.format_exc()}
"""

if __name__ == "__main__":
    res = call("execute_code", {"code": code})["result"]
    if isinstance(res, dict) and "error" in res:
        print("Error:", res["error"])
    else:
        data = res.get("result", res)
        print(f"Riot Window: '{data.get('title')}' | Found {data.get('count')} elements.")
        with open("scripts/audit_dump.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("Saved full dump to scripts/audit_dump.json")
