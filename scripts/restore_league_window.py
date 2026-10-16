import urllib.request
import json
import ctypes

BASE_URL = "http://127.0.0.1:8765/action"
HEADERS = {
    "X-NVDA-Bridge-Token": "nvda-bridge-secret-change-me",
    "Content-Type": "application/json"
}

code = """
import api
import ctypes

user32 = ctypes.windll.user32
desktop = api.getDesktopObject()
target_hwnd = None
for child in desktop.children:
    pname = (getattr(child, "appModule", None) and getattr(child.appModule, "appName", "")) or ""
    if "leagueclientux" in pname.lower():
        target_hwnd = getattr(child, "windowHandle", 0)
        break

if target_hwnd:
    # SW_RESTORE = 9, SW_SHOW = 5
    user32.ShowWindow(target_hwnd, 9)
    user32.SetForegroundWindow(target_hwnd)
    result = {"success": True, "hwnd": target_hwnd}
else:
    result = {"success": False, "msg": "League client window not found"}
"""

req = urllib.request.Request(
    BASE_URL,
    data=json.dumps({"action": "execute_code", "params": {"code": code}}).encode("utf-8"),
    headers=HEADERS
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    print(json.dumps(data.get("result", {}).get("result", {}), indent=2, ensure_ascii=False))
