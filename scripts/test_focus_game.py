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
    return json.loads(resp.read().decode())["result"]

for i in range(10):
    call("send_key", {"key": "shift+tab"})
    time.sleep(0.35)
    f = call("get_current_focus")
    speech = call("get_speech_history", {"count": 1}).get("phrases", [""])[-1]
    name = f.get("name")
    obj_type = f.get("objectType")
    print(f"[{i:02d}] Name: '{name}' | Speech: '{speech}' | Type: '{obj_type}'")
    if "Menu rápido" in (name or "") or "quick-action" in str(f.get("ia2Attributes")):
        break

code = """
focus = api.getFocusObject()
import speech
result = {
    'name': focus.name,
    'raw_name': getattr(super(type(focus), focus), 'name', None),
    'type': type(focus).__name__,
    'ia2': dict(focus.IA2Attributes) if getattr(focus, 'IA2Attributes', None) else {},
    'parent_name': focus.parent.name if focus.parent else None,
    'parent_ia2': dict(focus.parent.IA2Attributes) if (focus.parent and getattr(focus.parent, 'IA2Attributes', None)) else {},
}
"""
res = call("execute_code", {"code": code})
print("\nDeep Focus Info:")
print(json.dumps(res, indent=2))
