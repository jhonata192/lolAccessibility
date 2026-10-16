import urllib.request
import json

BASE_URL = "http://127.0.0.1:8765/action"
HEADERS = {
    "X-NVDA-Bridge-Token": "nvda-bridge-secret-change-me",
    "Content-Type": "application/json"
}

code = """
import NVDAObjects.IAccessible
import traceback

try:
    hwnd = 16974194
    root = NVDAObjects.IAccessible.getNVDAObjectFromEvent(hwnd, -4, 0)

    results = []

    def extract_text(obj, max_depth=8):
        texts = []
        stack = [(obj, 0)]
        while stack:
            o, d = stack.pop(0)
            if d > max_depth:
                continue
            name = (getattr(o, "name", "") or "").strip()
            clean = "".join(ch for ch in name if ord(ch) < 0xE000 or ord(ch) > 0xF8FF).strip()
            clean_lower = clean.lower()
            if clean and clean_lower not in ("animation", "lottie", "item", "botão", "button", "div", "span") and "unable to play media" not in clean_lower:
                if clean not in texts:
                    texts.append(clean)
            for c in (getattr(o, "children", []) or []):
                stack.append((c, d + 1))
        return texts

    def parse_tutorial_card(cls, texts):
        is_locked = "locked" in cls
        if "reward" in cls:
            status = "Bloqueada" if is_locked else "Disponível para resgate"
            hint = ""
            for t in texts:
                if "conclua" in t.lower():
                    hint = f" ({t})"
                    break
            return f"Recompensa do Tutorial: Cápsula de Iniciante (Status: {status}){hint}"
        
        # Sequence number
        seq = ""
        for t in texts:
            if t.isdigit():
                seq = t
                break
                
        # Title
        title = ""
        for t in texts:
            if t not in ("RECOMPENSAS", seq) and (t.isupper() or "LEAGUE" in t or "BEM-VINDO" in t):
                if "exp" not in t.lower() and not t.lower().startswith("conclua"):
                    title = t
                    break
        if not title and len(texts) > 1:
            title = texts[1]
            
        # Reward
        rew = ""
        for t in texts:
            tl = t.lower()
            if ("exp" in tl or " ea" in tl or "essência" in tl) and t != title:
                rew = t
                break
                
        # Description
        desc = ""
        for t in texts:
            tl = t.lower()
            if len(t) > 15 and t != title and "exp" not in tl and not tl.startswith("conclua") and "unable" not in tl:
                desc = t
                break
                
        # Lock hint
        lock_hint = ""
        if is_locked:
            for t in texts:
                if t.lower().startswith("conclua"):
                    lock_hint = f" - {t}"
                    break
            status = f"Bloqueado{lock_hint}"
        else:
            status = "Disponível - Pressione Enter para iniciar"
            
        parts = []
        if seq:
            parts.append(f"Tutorial {seq}: {title}")
        else:
            parts.append(title or "Tutorial")
            
        parts.append(f"(Status: {status})")
        if rew:
            parts.append(f"Recompensa: {rew}")
        if desc:
            parts.append(f"Descrição: {desc}")
            
        return ". ".join(parts)

    stack = [root]
    while stack and len(results) < 50:
        o = stack.pop(0)
        ia2 = getattr(o, "IA2Attributes", None)
        ia2_dict = dict(ia2) if (ia2 and hasattr(ia2, "items")) else {}
        cls = ia2_dict.get("class", "")

        if "npe-tutorial-item-card-component" in cls or "npe-tutorial-item-reward-component" in cls:
            texts = extract_text(o, 8)
            lbl = parse_tutorial_card(cls, texts)
            results.append({"type": "TutorialCard", "accessible": lbl, "cls": cls})

        for c in (getattr(o, "children", []) or []):
            stack.append(c)

    result = {
        "count": len(results),
        "results": results
    }
except Exception as e:
    result = {"error": str(e), "tb": traceback.format_exc()}
"""

req = urllib.request.Request(
    BASE_URL,
    data=json.dumps({"action": "execute_code", "params": {"code": code}}).encode("utf-8"),
    headers=HEADERS
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    print(json.dumps(data.get("result", {}).get("result", {}), indent=2, ensure_ascii=False))
