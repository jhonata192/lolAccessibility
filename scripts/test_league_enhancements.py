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
            if clean and clean.lower() not in ("animation", "lottie", "item", "botão", "button", "div", "span"):
                if clean not in texts:
                    texts.append(clean)
            for c in (getattr(o, "children", []) or []):
                stack.append((c, d + 1))
        return texts

    stack = [root]
    while stack and len(results) < 50:
        o = stack.pop(0)
        ia2 = getattr(o, "IA2Attributes", None)
        ia2_dict = dict(ia2) if (ia2 and hasattr(ia2, "items")) else {}
        cls = ia2_dict.get("class", "")
        tag = ia2_dict.get("tag", "")
        raw_name = getattr(o, "name", "") or ""

        # Tutorial cards
        if "npe-tutorial-item-card-component" in cls or "npe-tutorial-item-reward-component" in cls:
            texts = extract_text(o, 8)
            is_locked = "locked" in cls
            if "reward" in cls:
                status = "Bloqueada" if is_locked else "Disponível para resgate"
                lbl = f"Recompensa do Tutorial: Cápsula de Iniciante (Status: {status})"
            else:
                seq = texts[0] if texts and texts[0].isdigit() else ""
                title = texts[1] if len(texts) > 1 else ""
                desc = texts[2] if len(texts) > 2 else ""
                rew = texts[4] if len(texts) > 4 else ""
                status = "Bloqueado" if is_locked else "Disponível"
                lbl = f"Tutorial {seq}: {title} (Status: {status}) - Recompensa: {rew} - {desc}"
            results.append({"type": "TutorialCard", "raw": raw_name, "accessible": lbl, "cls": cls})

        # Tutorial arrows
        elif "npe-tutorial-carousel-left-arrow" in cls:
            results.append({"type": "Button", "raw": raw_name, "accessible": "Tutorial anterior", "cls": cls})
        elif "npe-tutorial-carousel-right-arrow" in cls:
            results.append({"type": "Button", "raw": raw_name, "accessible": "Próximo tutorial", "cls": cls})

        # Close button
        elif tag == "lol-uikit-close-button" or "hide-close-button" in cls:
            results.append({"type": "Button", "raw": raw_name, "accessible": "Fechar", "cls": cls})

        # Summoner Badge
        elif "summoner-info-anchor" in cls or "fancy-icon-with-level" in cls:
            texts = extract_text(o, 3)
            results.append({"type": "Badge", "raw": raw_name, "accessible": f"Perfil do Invocador: {' - '.join(texts)}", "cls": cls})

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
