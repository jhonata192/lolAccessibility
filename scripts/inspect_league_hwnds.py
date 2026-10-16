import urllib.request
import json

BASE_URL = "http://127.0.0.1:8765/action"
HEADERS = {
    "X-NVDA-Bridge-Token": "nvda-bridge-secret-change-me",
    "Content-Type": "application/json"
}

code = """
import api
import ctypes

user32 = ctypes.windll.user32
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

desktop = api.getDesktopObject()
target_hwnd = None
for child in desktop.children:
    pname = (getattr(child, "appModule", None) and getattr(child.appModule, "appName", "")) or ""
    if "leagueclientux" in pname.lower():
        target_hwnd = getattr(child, "windowHandle", 0)
        break

children_hwnds = []

def enum_cb(hwnd, lparam):
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    c_name = buf.value
    user32.GetWindowTextW(hwnd, buf, 256)
    w_text = buf.value
    children_hwnds.append({"hwnd": hwnd, "class": c_name, "title": w_text})
    return True

if target_hwnd:
    cb = WNDENUMPROC(enum_cb)
    user32.EnumChildWindows(target_hwnd, cb, 0)

result = {
    "parent_hwnd": target_hwnd,
    "children": children_hwnds
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
