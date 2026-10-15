import urllib.request
import json

BASE_URL = 'http://127.0.0.1:8765/action'
HEADERS = {'X-NVDA-Bridge-Token': 'nvda-bridge-secret-change-me', 'Content-Type': 'application/json'}

code = '''
import api, speech, controlTypes, NVDAObjects.IAccessible
desktop = api.getDesktopObject()
riot = [c for c in desktop.children if 'riot' in (c.name or '').lower()][0]

class Capturer:
    captured = []
    @classmethod
    def speak(cls, s, *a, **k):
        cls.captured.extend([str(x) for x in s if isinstance(x, str)])
    @classmethod
    def test_speech(cls, obj):
        import speech, controlTypes
        cls.captured = []
        old_speak = speech.speech.speak
        speech.speech.speak = cls.speak
        try:
            speech.speakObject(obj, reason=controlTypes.OutputReason.FOCUS)
        finally:
            speech.speech.speak = old_speak
        return ' '.join(cls.captured)

class F:
    @classmethod
    def find_all(cls, o, match_fn, depth=0):
        import NVDAObjects.IAccessible
        if depth > 10 or not o: return []
        res = []
        if match_fn(o): res.append(o)
        for ch in NVDAObjects.IAccessible.IAccessible._get_children(o):
            res.extend(cls.find_all(ch, match_fn, depth + 1))
        return res

# 1. Test side_nav buttons
side_nav = F.find_all(riot, lambda x: 'side-nav' in getattr(x, 'IA2Attributes', {}).get('class', ''))
side_nav_res = []
if side_nav:
    import NVDAObjects.IAccessible
    for c in NVDAObjects.IAccessible.IAccessible._get_children(side_nav[0]):
        spk = Capturer.test_speech(c)
        ia2 = getattr(c, 'IA2Attributes', {})
        side_nav_res.append({'name': c.name, 'role': str(c.role), 'cls': ia2.get('class'), 'spoken': spk})

# 2. Test library cards in transition-wrapper
html_doc = riot.children[3].children[0].children[0].children[0].children[0].children[0].children[1]
app_main = html_doc.children[0]
trans = app_main.children[8]
cards = F.find_all(trans, lambda x: 'library-product-card' in getattr(x, 'IA2Attributes', {}).get('class', ''))
card_res = []
for card in cards[:6]:
    spk = Capturer.test_speech(card)
    card_res.append({'name': card.name, 'role': str(card.role), 'spoken': spk})

result = {'side_nav': side_nav_res, 'cards': card_res}
'''

req = urllib.request.Request(BASE_URL, data=json.dumps({'action': 'execute_code', 'params': {'code': code}}).encode('utf-8'), headers=HEADERS)
try:
    res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))['result']['result']
    print('=== SIDE NAV ITEMS ===')
    for item in res.get('side_nav', []):
        name = (item.get('name') or '').encode('ascii', 'replace').decode('ascii')
        spoken = (item.get('spoken') or '').encode('ascii', 'replace').decode('ascii')
        print(f"Name: {name:<35} | Spoken: '{spoken}'")
    print('\n=== GAME CARDS ===')
    for card in res.get('cards', []):
        name = (card.get('name') or '').encode('ascii', 'replace').decode('ascii')
        spoken = (card.get('spoken') or '').encode('ascii', 'replace').decode('ascii')
        print(f"Name: {name:<60} | Spoken: '{spoken}'")
except urllib.error.HTTPError as e:
    print(e.code, e.read().decode('utf-8'))
