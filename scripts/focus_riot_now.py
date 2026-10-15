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

code_focus = """
import api, win32gui, win32con

desktop = api.getDesktopObject()
target = None
for c in desktop.children:
    app_name = getattr(c, "appModule", None)
    app_str = str(getattr(app_name, "appName", "")) if app_name else ""
    w_title = getattr(c, "name", "")
    if "riot" in app_str.lower() or "riot" in w_title.lower():
        target = c
        break

res = {}
if target:
    hwnd = getattr(target, "windowHandle", 0)
    if hwnd:
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            pass
    target.setFocus()
    res["focused"] = True
    res["hwnd"] = hwnd
    res["name"] = target.name
else:
    res["focused"] = False

result = res
"""
res = call("execute_code", {"code": code_focus})
print("Focus Riot Result:", json.dumps(res, indent=2))

time.sleep(0.5)

# Verificar objeto em foco
focus_info = call("get_current_focus")
print("Novo Foco:", json.dumps(focus_info.get("result", {}), indent=2, ensure_ascii=False))

# Verificar fala do NVDA
speech = call("get_last_speech")
print("NVDA Falou:", speech.get("result", {}).get("last_spoken"))
