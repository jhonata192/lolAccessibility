import urllib.request
import json

BASE_URL = 'http://127.0.0.1:8765/action'
HEADERS = {'X-NVDA-Bridge-Token': 'nvda-bridge-secret-change-me', 'Content-Type': 'application/json'}

code = '''
import api, NVDAObjects.IAccessible, traceback

try:
    desktop = api.getDesktopObject()
    riot = [c for c in desktop.children if 'riot' in (c.name or '').lower()][0]
    html_doc = riot.children[3].children[0].children[0].children[0].children[0].children[0].children[1]
    side_nav = html_doc.children[0].children[7]

    class LinkFinder:
        @classmethod
        def find_links(cls, o, depth=0):
            if depth > 10 or not o: return []
            res = []
            ia2 = getattr(o, 'IA2Attributes', None)
            tag = ia2.get('tag', '') if (ia2 and hasattr(ia2, 'items')) else ''
            cls_name = ia2.get('class', '') if (ia2 and hasattr(ia2, 'items')) else ''
            name = (o.name or '').encode('ascii', 'replace').decode('ascii')
            
            if tag in ('a', 'button') or any(k in cls_name.lower() for k in ('disclosure', 'button')):
                res.append({'name': name, 'tag': tag, 'cls': cls_name, 'role': str(o.role)})
            
            for ch in (getattr(o, 'children', []) or []):
                res.extend(cls.find_links(ch, depth + 1))
            return res

    result = LinkFinder.find_links(side_nav)
except Exception:
    result = {'error': traceback.format_exc()}
'''

req = urllib.request.Request(BASE_URL, data=json.dumps({'action': 'execute_code', 'params': {'code': code}}).encode('utf-8'), headers=HEADERS)
res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))['result']['result']

if isinstance(res, dict) and 'error' in res:
    print('Error:', res['error'])
else:
    for r in res:
        print(f"Name: {r['name']:<35} | Tag: {r['tag']:<6} | Class: {r['cls']}")
