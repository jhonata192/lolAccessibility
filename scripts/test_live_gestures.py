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

# Testar chamada do script de focar adicionar amigo via NVDA
code = """
import api

fg = api.getForegroundObject()
app = getattr(fg, "appModule", None)
if app and hasattr(app, "script_focusAddFriend"):
    app.script_focusAddFriend(None)
    result = "script_focusAddFriend executado"
else:
    result = "AppModule ou script_focusAddFriend não encontrado"
"""
r = call("execute_code", {"code": code})
print("Execução script_focusAddFriend:", r.get("result", {}).get("result"))

time.sleep(1)
speech = call("get_last_speech")
print("Fala capturada pelo NVDA após focar Add Friend:")
for sp in speech.get("result", {}).get("history", [])[-5:]:
    print(" -", sp)

# Agora testar script_focusGameHubTabs
code_hub = """
import api
fg = api.getForegroundObject()
app = getattr(fg, "appModule", None)
if app and hasattr(app, "script_focusGameHubTabs"):
    app.script_focusGameHubTabs(None)
    result = "script_focusGameHubTabs executado"
else:
    result = "AppModule ou script_focusGameHubTabs não encontrado"
"""
r_hub = call("execute_code", {"code": code_hub})
print("\nExecução script_focusGameHubTabs:", r_hub.get("result", {}).get("result"))

time.sleep(1)
speech_hub = call("get_last_speech")
print("Fala capturada pelo NVDA após focar Game Hub Tabs:")
for sp in speech_hub.get("result", {}).get("history", [])[-5:]:
    print(" -", sp)
