import urllib.request
import json

BASE_URL = 'http://127.0.0.1:8765/action'
HEADERS = {'X-NVDA-Bridge-Token': 'nvda-bridge-secret-change-me', 'Content-Type': 'application/json'}

code = '''
import api, NVDAObjects.IAccessible, time, traceback

try:
    desktop = api.getDesktopObject()
    riot = [c for c in desktop.children if 'riot' in (c.name or '').lower()][0]
    html_doc = riot.children[3].children[0].children[0].children[0].children[0].children[0].children[1]
    side_nav = html_doc.children[0].children[7]
    btn2 = side_nav.children[2] # Meus Jogos

    class Finder:
        @classmethod
        def find_a(cls, o, depth=0):
            import NVDAObjects.IAccessible
            if depth > 6 or not o: return None
            if getattr(o, 'IA2Attributes', {}).get('tag', '') == 'a':
                return o
            for ch in NVDAObjects.IAccessible.IAccessible._get_children(o):
                res = cls.find_a(ch, depth + 1)
                if res: return res
            return None

    a_elem = Finder.find_a(btn2)
    if a_elem:
        a_elem.setFocus()
        try:
            a_elem.doAction()
        except Exception:
            pass
        time.sleep(1.0)
        result = {'clicked': True, 'name': a_elem.name}
    else:
        result = {'error': 'not found'}
except Exception:
    result = {'error': traceback.format_exc()}
'''

req = urllib.request.Request(BASE_URL, data=json.dumps({'action': 'execute_code', 'params': {'code': code}}).encode('utf-8'), headers=HEADERS)
res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))['result']['result']
print(res)
