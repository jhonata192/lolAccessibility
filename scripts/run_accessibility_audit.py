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

def parse_ia2(ia2):
    if isinstance(ia2, dict):
        return ia2
    if isinstance(ia2, str):
        try:
            import ast
            return ast.literal_eval(ia2)
        except Exception:
            res = {}
            for part in ia2.split(";"):
                if ":" in part:
                    k, v = part.split(":", 1)
                    res[k.strip()] = v.strip()
            return res
    return {}

def run_audit(steps=25):
    for i in range(steps):
        call("send_key", {"key": "tab"})
        time.sleep(0.35)
        focus = call("get_current_focus", {}).get("result", {})
        tree = call("inspect_focus_tree", {}).get("result", {})
        speech_phrases = call("get_speech_history", {"count": 1}).get("result", {}).get("phrases", [])
        speech = speech_phrases[-1] if speech_phrases else ""
        
        name = focus.get("name")
        ia2 = parse_ia2(focus.get("ia2Attributes"))
        parent_ia2 = parse_ia2((tree.get("parent") or {}).get("ia2Attributes"))
        
        print(f"[{i+1:02d}] Name: '{name}' | Speech: '{speech}' | Class: '{ia2.get('class')}' | ParentClass: '{parent_ia2.get('class')}'")

if __name__ == "__main__":
    run_audit(25)
