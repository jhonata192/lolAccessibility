import urllib.request
import json

BASE_URL = "http://127.0.0.1:8765/action"
HEADERS = {
    "X-NVDA-Bridge-Token": "nvda-bridge-secret-change-me",
    "Content-Type": "application/json"
}

code = """
import api

res = []
desktop = api.getDesktopObject()
for c in desktop.children:
    res.append({
        "name": getattr(c, "name", ""),
        "class": getattr(c, "windowClassName", ""),
        "pid": getattr(c, "processId", 0),
        "hwnd": getattr(c, "windowHandle", 0),
        "loc": getattr(c, "location", None) and [c.location.left, c.location.top, c.location.width, c.location.height]
    })
result = res
"""

req = urllib.request.Request(
    BASE_URL,
    data=json.dumps({"action": "execute_code", "params": {"code": code}}).encode("utf-8"),
    headers=HEADERS
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    items = data.get("result", {}).get("result", [])
    for it in items:
        if it.get("name") or "riot" in it.get("class", "").lower() or "rclient" in it.get("class", "").lower():
            print(it)
