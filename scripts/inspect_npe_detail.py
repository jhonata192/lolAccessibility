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

    npe_target = None
    stack = [root]
    while stack:
        o = stack.pop(0)
        ia2 = getattr(o, "IA2Attributes", None)
        ia2_dict = dict(ia2) if (ia2 and hasattr(ia2, "items")) else {}
        cls = ia2_dict.get("class", "")
        if "npe-root-component" in cls:
            npe_target = o
            break
        for c in (getattr(o, "children", []) or []):
            stack.append(c)

    elements = []
    if npe_target:
        stack = [(npe_target, 0)]
        while stack and len(elements) < 150:
            o, d = stack.pop(0)
            ia2 = getattr(o, "IA2Attributes", None)
            ia2_dict = dict(ia2) if (ia2 and hasattr(ia2, "items")) else {}
            name = getattr(o, "name", "") or ""
            cls = ia2_dict.get("class", "")
            tag = ia2_dict.get("tag", "")
            role = int(getattr(o, "role", 0))
            role_text = getattr(o, "roleText", "") or ""
            
            elements.append({
                "d": d,
                "n": name,
                "r": role,
                "rt": role_text,
                "tag": tag,
                "cls": cls,
                "cc": getattr(o, "childCount", 0)
            })
            for c in (getattr(o, "children", []) or []):
                stack.append((c, d + 1))

    result = {
        "found": bool(npe_target),
        "total": len(elements),
        "elements": elements
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
with open("temp_npe_detail.json", "w", encoding="utf-8") as f:
    json.dump(data.get("result", {}).get("result", {}), f, indent=2, ensure_ascii=False)
print("Saved to temp_npe_detail.json. Found:", data.get("result", {}).get("result", {}).get("found"), "Total:", data.get("result", {}).get("result", {}).get("total"))
