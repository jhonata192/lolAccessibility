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

def step(key="tab"):
    print(f"\n--- Sending key: {key} ---")
    call("send_key", {"key": key})
    time.sleep(0.3)
    focus = call("get_current_focus", {})["result"]
    tree = call("inspect_focus_tree", {})["result"]
    speech = call("get_speech_history", {"count": 3})["result"]
    
    print(f"Name: {focus.get('name')}")
    print(f"Role: {focus.get('role')} ({focus.get('roleText')})")
    print(f"IA2: {focus.get('ia2Attributes')}")
    p = tree.get("parent", {})
    print(f"Parent IA2: {p.get('ia2Attributes')}")
    print(f"NVDA Speech: {speech.get('phrases')}")

if __name__ == "__main__":
    for i in range(12):
        step("tab")
