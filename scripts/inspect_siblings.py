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
    return json.loads(resp.read().decode())["result"]

tree = call("inspect_focus_tree")
print("Total siblings in parent:", len(tree.get("siblings", [])))
for i, s in enumerate(tree.get("siblings", [])):
    print(f"[{i:02d}] Name: '{s.get('name')}', Role: {s.get('role')}, IA2: {s.get('ia2Attributes')}")
