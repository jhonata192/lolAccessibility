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

class Scanner:
    res = []
    @classmethod
    def scan(cls, o, depth=0):
        if depth > 25: return
        ia2 = getattr(o, "IA2Attributes", None)
        ia2_dict = dict(ia2) if (ia2 and hasattr(ia2, "items")) else {}
        tag = ia2_dict.get("tag", "")
        if tag == "input":
            p = getattr(o, "parent", None)
            gp = getattr(p, "parent", None) if p else None
            ggp = getattr(gp, "parent", None) if gp else None
            cls.res.append({
                "name": o.name,
                "desc": o.description,
                "ia2": ia2_dict,
                "parent_class": getattr(p, "IA2Attributes", {}).get("class", "") if p else "",
                "gp_class": getattr(gp, "IA2Attributes", {}).get("class", "") if gp else "",
                "ggp_class": getattr(ggp, "IA2Attributes", {}).get("class", "") if ggp else ""
            })
        for c in (getattr(o, "children", None) or []):
            cls.scan(c, depth + 1)

desktop = api.getDesktopObject()
for c in desktop.children:
    if "riot client" in (getattr(c, "name", "") or "").lower():
        Scanner.scan(c)
        break
result = Scanner.res
"""
res = call("execute_code", {"code": code})
print(json.dumps(res.get("result", {}).get("result", []), indent=2))
