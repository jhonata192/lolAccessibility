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
    return json.loads(resp.read().decode())

code = """
import api

class RiotScanner:
    elements = []
    
    @classmethod
    def scan(cls, o, depth=0):
        if not o or depth > 20: return
        try:
            name = (getattr(o, "name", "") or "").strip()
            role = int(getattr(o, "role", 0))
            role_text = getattr(o, "roleText", "") or ""
            states = getattr(o, "states", set())
            ia2 = getattr(o, "IA2Attributes", None)
            ia2_dict = dict(ia2) if (ia2 and hasattr(ia2, "items")) else {}
            cls_name = ia2_dict.get("class", "")
            tag = ia2_dict.get("tag", "")
            loc = getattr(o, "location", None)
            loc_str = f"L{loc.left}_T{loc.top}_W{loc.width}_H{loc.height}" if loc else ""
            
            # Filtrar nós relevantes: botões, links, abas, listas, campos de entrada, checkboxes, itens de menu
            is_interactive = (
                role in (9, 22, 11, 102, 10, 8, 30, 86, 26, 12, 13) or 
                any(k in cls_name for k in ("button", "tab", "item", "input", "select", "check", "disclosure", "card", "nav", "social", "friend")) or
                any(s in str(states) for s in ("FOCUSABLE", "SELECTABLE", "EXPANDED", "COLLAPSED"))
            )
            
            if is_interactive and (name or cls_name):
                # Limpar PUA icons do nome
                clean_name = "".join(ch for ch in name if ord(ch) < 0xE000 or ord(ch) > 0xF8FF).strip()
                cls.elements.append({
                    "name": clean_name[:60],
                    "role": role,
                    "roleText": role_text,
                    "class": cls_name[:50],
                    "tag": tag,
                    "loc": loc_str,
                    "states": [str(s).split(".")[-1].split(":")[0] for s in states if "FOCUS" in str(s) or "SELECT" in str(s) or "EXPAND" in str(s) or "COLLAPSE" in str(s)]
                })
        except Exception:
            pass
            
        for c in (getattr(o, "children", None) or []):
            cls.scan(c, depth + 1)

# Localizar o Riot Client no Desktop
desktop = api.getDesktopObject()
riot_win = None
for c in desktop.children:
    if "riot client" in (getattr(c, "name", "") or "").lower():
        riot_win = c
        break

if riot_win:
    RiotScanner.scan(riot_win)

result = {
    "found_window": riot_win is not None,
    "total_interactive_elements": len(RiotScanner.elements),
    "elements": RiotScanner.elements
}
"""

res = call("execute_code", {"code": code})
data = res.get("result", {}).get("result", {})
print(f"Riot Window Found: {data.get('found_window')}")
print(f"Total Interactive Elements: {data.get('total_interactive_elements')}")

# Agrupar por região de tela:
left_bar = []      # Left < 300
header = []        # Top < 150
main_content = []  # 300 <= Left <= 1400, Top >= 150
social_panel = []  # Left > 1400

for el in data.get("elements", []):
    loc = el.get("loc", "")
    left = 0
    top = 0
    if loc.startswith("L"):
        parts = loc.split("_")
        try:
            left = int(parts[0][1:])
            top = int(parts[1][1:])
        except Exception:
            pass
            
    if left < 300:
        left_bar.append(el)
    elif top < 120 and left < 1400:
        header.append(el)
    elif left >= 1400:
        social_panel.append(el)
    else:
        main_content.append(el)

print(f"\n--- Barra Lateral Esquerda ({len(left_bar)} elementos) ---")
for el in left_bar[:15]:
    print(f"[{el['role']}:{el['roleText']}] '{el['name']}' | Class: '{el['class']}' | States: {el['states']}")

print(f"\n--- Cabeçalho Superior ({len(header)} elementos) ---")
for el in header[:10]:
    print(f"[{el['role']}:{el['roleText']}] '{el['name']}' | Class: '{el['class']}' | States: {el['states']}")

print(f"\n--- Painel Social Direito ({len(social_panel)} elementos) ---")
for el in social_panel[:20]:
    print(f"[{el['role']}:{el['roleText']}] '{el['name']}' | Class: '{el['class']}' | States: {el['states']}")

print(f"\n--- Conteúdo Principal Central ({len(main_content)} elementos) ---")
for el in main_content[:15]:
    print(f"[{el['role']}:{el['roleText']}] '{el['name']}' | Class: '{el['class']}' | States: {el['states']}")
