import urllib.request
import json

BASE_URL = 'http://127.0.0.1:8765/action'
HEADERS = {'X-NVDA-Bridge-Token': 'nvda-bridge-secret-change-me', 'Content-Type': 'application/json'}

code = '''
import api

desktop = api.getDesktopObject()
riot = [c for c in desktop.children if 'riot' in (c.name or '').lower()][0]
html_doc = riot.children[3].children[0].children[0].children[0].children[0].children[0].children[1]

class PScanner:
    @classmethod
    def scan(cls, o, depth=0):
        if depth > 10 or not o: return []
        ia2 = getattr(o, 'IA2Attributes', None)
        cls_name = ia2.get('class', '') if (ia2 and hasattr(ia2, 'items')) else ''
        tag = ia2.get('tag', '') if (ia2 and hasattr(ia2, 'items')) else ''
        res = [{
            'depth': depth,
            'name': (o.name or '').encode('ascii', 'replace').decode('ascii'),
            'role': str(o.role),
            'tag': tag,
            'cls': cls_name,
            'childCount': getattr(o, 'childCount', 0)
        }]
        for ch in (getattr(o, 'children', []) or []):
            res.extend(cls.scan(ch, depth + 1))
        return res

result = []
for i in [1, 3, 4, 5, 6, 9, 13]:
    if i < len(html_doc.children):
        result.append({'index': i, 'tree': PScanner.scan(html_doc.children[i])})
'''

req = urllib.request.Request(BASE_URL, data=json.dumps({'action': 'execute_code', 'params': {'code': code}}).encode('utf-8'), headers=HEADERS)
res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))['result']['result']

for p in res:
    print(f"\n--- Portal at index {p['index']} (Total nodes: {len(p['tree'])}) ---")
    for item in p['tree']:
        if item['name'] or item['cls']:
            print(f"  D{item['depth']}: {item['name']:<30} | {item['tag']:<5} | {item['cls']}")
