import urllib.request
import json

BASE_URL = 'http://127.0.0.1:8765/action'
HEADERS = {'X-NVDA-Bridge-Token': 'nvda-bridge-secret-change-me', 'Content-Type': 'application/json'}

code = '''
import api, NVDAObjects.IAccessible
desktop = api.getDesktopObject()
riot = [c for c in desktop.children if 'riot' in (c.name or '').lower()][0]
html_doc = riot.children[3].children[0].children[0].children[0].children[0].children[0].children[1]
app_main = html_doc.children[0]
trans = app_main.children[8]

class F:
    @classmethod
    def dump(cls, o, depth=0):
        import NVDAObjects.IAccessible
        if depth > 7 or not o: return []
        ia2 = getattr(o, 'IA2Attributes', {})
        res = [{
            'depth': depth,
            'name': getattr(o, 'name', None),
            'role': str(getattr(o, 'role', None)),
            'tag': ia2.get('tag'),
            'cls': ia2.get('class'),
            'sub_count': len(NVDAObjects.IAccessible.IAccessible._get_children(o))
        }]
        for ch in NVDAObjects.IAccessible.IAccessible._get_children(o):
            res.extend(cls.dump(ch, depth + 1))
        return res

result = F.dump(trans)
'''

req = urllib.request.Request(BASE_URL, data=json.dumps({'action': 'execute_code', 'params': {'code': code}}).encode('utf-8'), headers=HEADERS)
try:
    res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))['result']['result']
    for item in res:
        print('  '*item['depth'] + f"tag={item['tag']} cls={item['cls']} role={item['role']} name={repr(item['name'])}")
except urllib.error.HTTPError as e:
    print(e.code, e.read().decode('utf-8'))
