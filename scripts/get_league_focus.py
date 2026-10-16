import urllib.request
import json

BASE_URL = "http://127.0.0.1:8765/action"
HEADERS = {
    "X-NVDA-Bridge-Token": "nvda-bridge-secret-change-me",
    "Content-Type": "application/json"
}

code = """
import api

focus = api.getFocusObject()
ia2 = getattr(focus, "IA2Attributes", None)
ia2_dict = dict(ia2) if (ia2 and hasattr(ia2, "items")) else {}

result = {
    "name": getattr(focus, "name", ""),
    "role": int(getattr(focus, "role", 0)),
    "roleText": getattr(focus, "roleText", ""),
    "appModule": str(getattr(focus, "appModule", "")),
    "className": getattr(focus, "windowClassName", ""),
    "tag": ia2_dict.get("tag", ""),
    "class": ia2_dict.get("class", ""),
    "id": getattr(focus, "UIAAutomationId", "") or ""
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
