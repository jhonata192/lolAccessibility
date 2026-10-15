import urllib.request
import json

BASE_URL = "http://127.0.0.1:8765/action"
HEADERS = {
    "X-NVDA-Bridge-Token": "nvda-bridge-secret-change-me",
    "Content-Type": "application/json"
}

# We can extend inspect_focus_tree or write a small script that inspects a full subtree
script_code = """
import api, json
focus = api.getFocusObject()
parent = focus.parent if focus else None
data = []
if parent:
    for i, child in enumerate(parent.children or []):
        c_info = {
            "index": i,
            "name": child.name,
            "role": child.role,
            "desc": child.description,
            "ia2": dict(child.IA2Attributes) if getattr(child, "IA2Attributes", None) else {},
            "subchildren": []
        }
        for sub in (child.children or []):
            c_info["subchildren"].append({
                "name": sub.name,
                "role": sub.role,
                "desc": sub.description,
                "ia2": dict(sub.IA2Attributes) if getattr(sub, "IA2Attributes", None) else {}
            })
        data.append(c_info)
print(json.dumps(data, indent=2))
"""

# Let's inspect via python using a custom bridge tool or temporary code
