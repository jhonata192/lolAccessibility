import urllib.request
import json

BASE_URL = 'http://127.0.0.1:8765/action'
HEADERS = {'X-NVDA-Bridge-Token': 'nvda-bridge-secret-change-me', 'Content-Type': 'application/json'}

code = '''
import api, NVDAObjects.IAccessible, speech, controlTypes
desktop = api.getDesktopObject()
riot = [c for c in desktop.children if 'riot' in (c.name or '').lower()][0]

class Scanner:
    @classmethod
    def find_container(cls, o):
        ia2 = getattr(o, 'IA2Attributes', None)
        c = ia2.get('class', '') if (ia2 and hasattr(ia2, 'items')) else ''
        if 'identity-menu-container' in c:
            return o
        for ch in (getattr(o, 'children', []) or []):
            res = cls.find_container(ch)
            if res: return res
        return None

cnt = Scanner.find_container(riot)
spoken_items = []
if cnt:
    class Capturer:
        captured = []
        @classmethod
        def speak(cls, s, *a, **k):
            cls.captured.extend([str(x) for x in s if isinstance(x, str)])

    for c in NVDAObjects.IAccessible.IAccessible._get_children(cnt):
        Capturer.captured = []
        old_speak = speech.speech.speak
        speech.speech.speak = Capturer.speak
        try:
            speech.speakObject(c, reason=controlTypes.OutputReason.FOCUS)
        finally:
            speech.speech.speak = old_speak
        spoken_items.append({
            'name': c.name,
            'role': str(c.role),
            'spoken': ' '.join(Capturer.captured),
            'cls': getattr(c, 'IA2Attributes', {}).get('class', '')
        })

result = spoken_items
'''

req = urllib.request.Request(BASE_URL, data=json.dumps({'action': 'execute_code', 'params': {'code': code}}).encode('utf-8'), headers=HEADERS)
res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))['result']['result']

for item in res:
    name = (item.get('name') or '').encode('ascii', 'replace').decode('ascii')
    spoken = (item.get('spoken') or '').encode('ascii', 'replace').decode('ascii')
    print(f"Name: {name:<30} | Spoken: '{spoken}'")
