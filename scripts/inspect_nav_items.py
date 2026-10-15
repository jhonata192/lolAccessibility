import urllib.request
import json

BASE_URL = 'http://127.0.0.1:8765/action'
HEADERS = {'X-NVDA-Bridge-Token': 'nvda-bridge-secret-change-me', 'Content-Type': 'application/json'}

code = '''
import api, NVDAObjects.IAccessible

desktop = api.getDesktopObject()
riot = [c for c in desktop.children if 'riot' in (c.name or '').lower()][0]
html_doc = riot.children[3].children[0].children[0].children[0].children[0].children[0].children[1]
portal = html_doc.children[13]

class Scanner:
    @classmethod
    def find_nav_items(cls, o):
        res = []
        ia2 = getattr(o, 'IA2Attributes', None)
        cls_name = ia2.get('class', '') if (ia2 and hasattr(ia2, 'items')) else ''
        if 'settings-navigation-item' in cls_name:
            raw_ch = []
            try:
                for c in NVDAObjects.IAccessible.IAccessible._get_children(o):
                    raw_ch.append({
                        'name': c.name,
                        'role': str(c.role),
                        'value': getattr(c, 'value', ''),
                        'cls': getattr(c, 'IA2Attributes', {}).get('class', '') if hasattr(c, 'IA2Attributes') else ''
                    })
            except Exception as e:
                raw_ch = [{'error': str(e)}]

            acc_name = ''
            try:
                acc_name = o.IAccessibleObject.accName(0)
            except Exception:
                pass

            res.append({
                'name': o.name,
                'role': str(o.role),
                'cls': cls_name,
                'raw_name': getattr(o, '_name', None),
                'acc_name': acc_name,
                'raw_ch': raw_ch
            })
        for ch in (getattr(o, 'children', []) or []):
            res.extend(cls.find_nav_items(ch))
        return res

result = Scanner.find_nav_items(portal)
'''

req = urllib.request.Request(BASE_URL, data=json.dumps({'action': 'execute_code', 'params': {'code': code}}).encode('utf-8'), headers=HEADERS)
res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))['result']['result']

for i, it in enumerate(res):
    name = (it.get('name') or '').encode('ascii', 'replace').decode('ascii')
    acc_name = (it.get('acc_name') or '').encode('ascii', 'replace').decode('ascii')
    print(f"Item {i}: name={repr(name)}, acc_name={repr(acc_name)}, cls={it['cls']}")
    for c in it.get('raw_ch', []):
        c_name = (c.get('name') or '').encode('ascii', 'replace').decode('ascii')
        print(f"   RawChild: name={repr(c_name)}, role={c.get('role')}, cls={c.get('cls')}")
