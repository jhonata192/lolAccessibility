import urllib.request
import json

BASE_URL = 'http://127.0.0.1:8765/action'
HEADERS = {'X-NVDA-Bridge-Token': 'nvda-bridge-secret-change-me', 'Content-Type': 'application/json'}

code = '''
import api, NVDAObjects.IAccessible, speech, controlTypes, traceback

try:
    desktop = api.getDesktopObject()
    riot = [c for c in desktop.children if 'riot' in (c.name or '').lower()][0]
    html_doc = riot.children[3].children[0].children[0].children[0].children[0].children[0].children[1]
    portal = html_doc.children[13]

    class Scanner:
        @classmethod
        def find_main(cls, o):
            ia2 = getattr(o, 'IA2Attributes', None)
            c = ia2.get('class', '') if (ia2 and hasattr(ia2, 'items')) else ''
            if 'settings-drawer-main' in c:
                return o
            for ch in (getattr(o, 'children', []) or []):
                res = cls.find_main(ch)
                if res: return res
            return None

    main_panel = Scanner.find_main(portal)

    class Capturer:
        captured = []
        @classmethod
        def speak(cls, s, *a, **k):
            cls.captured.extend([str(x) for x in s if isinstance(x, str)])

    def test_speech(obj):
        Capturer.captured = []
        old_speak = speech.speech.speak
        speech.speech.speak = Capturer.speak
        try:
            speech.speakObject(obj, reason=controlTypes.OutputReason.FOCUS)
        finally:
            speech.speech.speak = old_speak
        return ' '.join(Capturer.captured)

    class Collector:
        _Role = getattr(controlTypes, "Role", None)
        ROLE_BUTTON = getattr(_Role, "BUTTON", getattr(controlTypes, "ROLE_BUTTON", 9))
        ROLE_CHECKBOX = getattr(_Role, "CHECKBOX", getattr(controlTypes, "ROLE_CHECKBOX", 10))
        ROLE_COMBOBOX = getattr(_Role, "COMBOBOX", getattr(controlTypes, "ROLE_COMBOBOX", 12))
        ROLE_EDITABLETEXT = getattr(_Role, "EDITABLETEXT", getattr(controlTypes, "ROLE_EDITABLETEXT", 8))
        ROLE_LINK = getattr(_Role, "LINK", getattr(controlTypes, "ROLE_LINK", 30))

        @classmethod
        def collect(cls, o, out=None):
            if out is None: out = []
            role = getattr(o, 'role', 0)
            ia2 = getattr(o, 'IA2Attributes', None)
            c_cls = ia2.get('class', '') if (ia2 and hasattr(ia2, 'items')) else ''
            tag = ia2.get('tag', '') if (ia2 and hasattr(ia2, 'items')) else ''
            
            if role in (cls.ROLE_BUTTON, cls.ROLE_CHECKBOX, cls.ROLE_COMBOBOX, cls.ROLE_EDITABLETEXT, cls.ROLE_LINK) or any(k in c_cls.lower() for k in ('button', 'checkbox', 'dropdown', 'selection', 'input', 'folder')):
                spk = test_speech(o)
                out.append({
                    'name': o.name,
                    'role': str(role),
                    'tag': tag,
                    'cls': c_cls,
                    'value': getattr(o, 'value', ''),
                    'spoken': spk,
                    'type': type(o).__name__
                })

            for ch in (getattr(o, 'children', []) or []):
                cls.collect(ch, out)
            return out

    result = Collector.collect(main_panel)
except Exception:
    result = {'error': traceback.format_exc()}
'''

req = urllib.request.Request(BASE_URL, data=json.dumps({'action': 'execute_code', 'params': {'code': code}}).encode('utf-8'), headers=HEADERS)
res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))['result']['result']

if isinstance(res, dict) and 'error' in res:
    print("Error:", res['error'])
else:
    for item in res:
        name = (item.get('name') or '').encode('ascii', 'replace').decode('ascii')
        spoken = (item.get('spoken') or '').encode('ascii', 'replace').decode('ascii')
        val = (item.get('value') or '').encode('ascii', 'replace').decode('ascii')
        cls_name = item.get('cls', '')
        print(f"Name: {name:<30} | Spoken: '{spoken}' | Value: '{val}' | Class: {cls_name[:35]}")
