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

class FriendsInspector:
    friends = []
    
    @classmethod
    def scan(cls, o, depth=0):
        if not o or depth > 22: return
        try:
            ia2 = getattr(o, "IA2Attributes", None)
            ia2_dict = dict(ia2) if (ia2 and hasattr(ia2, "items")) else {}
            cls_name = ia2_dict.get("class", "")
            
            if "social-item" in cls_name or "friend" in cls_name.lower():
                sub_texts = []
                def get_sub(sub_o, d=0):
                    if d > 6: return
                    n = (getattr(sub_o, "name", "") or "").strip()
                    # Limpar PUA icons
                    clean = "".join(ch for ch in n if ord(ch) < 0xE000 or ord(ch) > 0xF8FF).strip()
                    if clean and clean not in sub_texts:
                        sub_texts.append(clean)
                    for sc in (getattr(sub_o, "children", None) or []):
                        get_sub(sc, d + 1)
                get_sub(o)
                
                cls.friends.append({
                    "self_name": o.name,
                    "role": int(o.role),
                    "roleText": getattr(o, "roleText", ""),
                    "class": cls_name,
                    "states": str(o.states),
                    "collected_texts": sub_texts
                })
        except Exception:
            pass
            
        for c in (getattr(o, "children", None) or []):
            cls.scan(c, depth + 1)

desktop = api.getDesktopObject()
for c in desktop.children:
    if "riot client" in (getattr(c, "name", "") or "").lower():
        FriendsInspector.scan(c)
        break

result = FriendsInspector.friends
"""

res = call("execute_code", {"code": code})
friends = res.get("result", {}).get("result", [])
print(f"Total social/friend items found: {len(friends)}")
for i, f in enumerate(friends[:15]):
    print(f"[{i:02d}] Class: '{f['class']}' | Role: {f['role']} ({f['roleText']}) | Name: '{f['self_name']}' | Texts: {f['collected_texts']}")
