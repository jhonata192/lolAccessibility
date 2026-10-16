import urllib.request
import json

BASE_URL = "http://127.0.0.1:8765/action"
HEADERS = {
    "X-NVDA-Bridge-Token": "nvda-bridge-secret-change-me",
    "Content-Type": "application/json"
}

code = """
import NVDAObjects.IAccessible
import api

hwnd = 16974194
obj = NVDAObjects.IAccessible.getNVDAObjectFromEvent(hwnd, -4, 0)

info = {
    "name": getattr(obj, "name", ""),
    "role": int(getattr(obj, "role", 0)),
    "roleText": getattr(obj, "roleText", ""),
    "appModule": str(getattr(obj, "appModule", "")),
    "childCount": getattr(obj, "childCount", 0),
    "children": []
}

if obj:
    for c in (getattr(obj, "children", []) or []):
        info["children"].append({
            "name": getattr(c, "name", ""),
            "role": int(getattr(c, "role", 0)),
            "roleText": getattr(c, "roleText", ""),
            "tag": (getattr(c, "IA2Attributes", None) and dict(c.IA2Attributes).get("tag", "")) or "",
            "class": (getattr(c, "IA2Attributes", None) and dict(c.IA2Attributes).get("class", "")) or "",
            "childCount": getattr(c, "childCount", 0)
        })

result = info
"""

req = urllib.request.Request(
    BASE_URL,
    data=json.dumps({"action": "execute_code", "params": {"code": code}}).encode("utf-8"),
    headers=HEADERS
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    print(json.dumps(data.get("result", {}).get("result", {}), indent=2, ensure_ascii=False))
