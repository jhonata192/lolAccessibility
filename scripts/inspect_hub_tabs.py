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
    return json.loads(resp.read().decode())

code = """
import api

class HubTabsInspector:
    tabs = []
    @classmethod
    def scan(cls, o, depth=0):
        if depth > 22: return
        ia2 = getattr(o, "IA2Attributes", None)
        ia2_dict = dict(ia2) if (ia2 and hasattr(ia2, "items")) else {}
        cls_name = ia2_dict.get("class", "")
        loc = getattr(o, "location", None)
        if loc and 150 < loc.left < 1400 and ("tab-button" in cls_name or getattr(o, "role", 0) == 22):
            children_names = []
            for c in (getattr(o, "children", None) or []):
                children_names.append({
                    "name": c.name,
                    "role": int(c.role),
                    "class": getattr(c, "IA2Attributes", {}).get("class", "") if getattr(c, "IA2Attributes", None) else ""
                })
            cls.tabs.append({
                "raw_name": getattr(o, "_name", getattr(o, "name", "")),
                "posinset": ia2_dict.get("posinset"),
                "setsize": ia2_dict.get("setsize"),
                "loc": f"L{loc.left}_T{loc.top}_W{loc.width}_H{loc.height}",
                "children": children_names
            })
        for c in (getattr(o, "children", None) or []):
            cls.scan(c, depth + 1)

desktop = api.getDesktopObject()
for c in desktop.children:
    if "riot client" in (getattr(c, "name", "") or "").lower():
        HubTabsInspector.scan(c)
        break
result = HubTabsInspector.tabs
"""
res = call("execute_code", {"code": code})
print(json.dumps(res.get("result", {}).get("result", []), indent=2, ensure_ascii=False))
