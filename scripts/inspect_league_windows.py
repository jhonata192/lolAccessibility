import urllib.request
import json

BASE_URL = "http://127.0.0.1:8765/action"
HEADERS = {
    "X-NVDA-Bridge-Token": "nvda-bridge-secret-change-me",
    "Content-Type": "application/json"
}

code = """
import api

results = []
desktop = api.getDesktopObject()
for child in desktop.children:
    pname = (getattr(child, "appModule", None) and getattr(child.appModule, "appName", "")) or ""
    wtitle = getattr(child, "name", "") or ""
    wclass = getattr(child, "windowClassName", "") or ""
    hwnd = getattr(child, "windowHandle", 0) or 0
    if "league" in pname.lower() or "league" in wtitle.lower() or "riot" in pname.lower():
        results.append({
            "appName": pname,
            "title": wtitle,
            "className": wclass,
            "hwnd": hwnd,
            "role": int(getattr(child, "role", 0)),
            "childCount": len(child.children) if hasattr(child, "children") else 0
        })

result = results
"""

req = urllib.request.Request(
    BASE_URL,
    data=json.dumps({"action": "execute_code", "params": {"code": code}}).encode("utf-8"),
    headers=HEADERS
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    print(json.dumps(data.get("result", {}).get("result", []), indent=2, ensure_ascii=False))
