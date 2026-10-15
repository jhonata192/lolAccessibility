import urllib.request
import json

BASE_URL = 'http://127.0.0.1:8765/action'
HEADERS = {'X-NVDA-Bridge-Token': 'nvda-bridge-secret-change-me', 'Content-Type': 'application/json'}

code = '''
import api

desktop = api.getDesktopObject()
riot = [c for c in desktop.children if 'riot' in (c.name or '').lower()][0]
html_doc = riot.children[3].children[0].children[0].children[0].children[0].children[0].children[1]
portal = html_doc.children[13]

dialog = portal.children[0].children[1]
content = dialog.children[1]
main = content.children[4]

scroller = main.children[0].children[0]
result = []
for i, c in enumerate(scroller.children):
    ia2 = getattr(c, 'IA2Attributes', None)
    c_cls = ia2.get('class', '') if (ia2 and hasattr(ia2, 'items')) else ''
    tag = ia2.get('tag', '') if (ia2 and hasattr(ia2, 'items')) else ''
    name = (c.name or '').encode('ascii', 'replace').decode('ascii')
    result.append({
        'idx': i,
        'name': name,
        'role': str(c.role),
        'tag': tag,
        'cls': c_cls,
        'childCount': getattr(c, 'childCount', 0),
        'sub_children': [{'name': (s.name or '').encode('ascii', 'replace').decode('ascii'), 'role': str(s.role), 'cls': getattr(s, 'IA2Attributes', {}).get('class', '')} for s in (getattr(c, 'children', []) or [])]
    })
'''

req = urllib.request.Request(BASE_URL, data=json.dumps({'action': 'execute_code', 'params': {'code': code}}).encode('utf-8'), headers=HEADERS)
res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))['result']['result']

for r in res:
    print(f"[{r['idx']:02d}] Name: {repr(r['name']):<30} | Tag: {r['tag']:<6} | Class: {r['cls']}")
    for s in r['sub_children']:
        print(f"     Sub: Name={repr(s['name']):<25} | Role={s['role']:<4} | Class={s['cls']}")
