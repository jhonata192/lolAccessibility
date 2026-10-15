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

print("1. Trazendo Riot Client para o primeiro plano...")
f_win = call("focus_window", {"title_or_class": "Riot Client"})
print("Focus Window:", f_win.get("success"))
time.sleep(0.5)

# Teste 1: Focar Abas do Game Hub (Control+Shift+H)
print("\n--- Teste 1: Enviando Control+Shift+H (Guias do Game Hub) ---")
call("send_key", {"key": "control+shift+h"})
time.sleep(0.8)
focus = call("get_current_focus")
print("Objeto Focado:", focus.get("result", {}).get("name"), "| RoleText:", focus.get("result", {}).get("roleText"))
history = call("get_speech_history", {"count": 3})
print("Fala do NVDA:", history.get("result", {}).get("phrases"))

# Navegar para a próxima guia do Game Hub com seta para a direita
print("\n--- Teste 1.1: Pressionando Seta Direita na Guia do Game Hub ---")
call("send_key", {"key": "rightArrow"})
time.sleep(0.6)
focus = call("get_current_focus")
print("Objeto Focado:", focus.get("result", {}).get("name"), "| RoleText:", focus.get("result", {}).get("roleText"))
history = call("get_speech_history", {"count": 3})
print("Fala do NVDA:", history.get("result", {}).get("phrases"))

# Teste 2: Focar Guias Sociais (Control+Shift+O)
print("\n--- Teste 2: Enviando Control+Shift+O (Guias Sociais) ---")
call("send_key", {"key": "control+shift+o"})
time.sleep(0.8)
focus = call("get_current_focus")
print("Objeto Focado:", focus.get("result", {}).get("name"), "| RoleText:", focus.get("result", {}).get("roleText"))
history = call("get_speech_history", {"count": 3})
print("Fala do NVDA:", history.get("result", {}).get("phrases"))

# Teste 3: Focar Adicionar Amigo (Control+Shift+A)
print("\n--- Teste 3: Enviando Control+Shift+A (Adicionar Amigo) ---")
call("send_key", {"key": "control+shift+a"})
time.sleep(0.8)
focus = call("get_current_focus")
print("Objeto Focado:", focus.get("result", {}).get("name"), "| Descrição:", focus.get("result", {}).get("description"))
history = call("get_speech_history", {"count": 3})
print("Fala do NVDA:", history.get("result", {}).get("phrases"))

# Teste 4: Pressionar Tab a partir do campo de Riot ID para ver a Tagline
print("\n--- Teste 4: Pressionando Tab para ir ao campo de Tagline ---")
call("send_key", {"key": "tab"})
time.sleep(0.6)
focus = call("get_current_focus")
print("Objeto Focado:", focus.get("result", {}).get("name"), "| Descrição:", focus.get("result", {}).get("description"))
history = call("get_speech_history", {"count": 3})
print("Fala do NVDA:", history.get("result", {}).get("phrases"))
