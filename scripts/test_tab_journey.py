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

code = """
focus = api.getFocusObject()
import speech, controlTypes
class Capturer:
    captured = []
    @classmethod
    def speak(cls, s, *a, **k):
        cls.captured.extend([str(x) for x in s if isinstance(x, str)])

old_speak = speech.speech.speak
speech.speech.speak = Capturer.speak
try:
    speech.speakObject(focus, reason=controlTypes.OutputReason.FOCUS)
finally:
    speech.speech.speak = old_speak

result = {
    'name': focus.name,
    'role': focus.role,
    'captured': Capturer.captured,
}
"""

def run(steps=20):
    for i in range(steps):
        call("send_key", {"key": "tab"})
        time.sleep(0.35)
        res = call("execute_code", {"code": code})["result"]
        spoken = " ".join(res.get("captured", []))
        print(f"[{i+1:02d}] Name: '{res.get('name')}' | Spoken: '{spoken}'")

if __name__ == "__main__":
    run(20)
