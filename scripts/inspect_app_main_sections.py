import urllib.request
import json

BASE_URL = 'http://127.0.0.1:8765/action'
HEADERS = {'X-NVDA-Bridge-Token': 'nvda-bridge-secret-change-me', 'Content-Type': 'application/json'}

code = '''
import api, traceback

try:
    class Dumper:
        @classmethod
        def dump_node(cls, node, depth=0, max_depth=6):
            if depth > max_depth or not node: return []
            ia2 = getattr(node, 'IA2Attributes', None)
            cls_name = ia2.get('class', '') if (ia2 and hasattr(ia2, 'items')) else ''
            tag = ia2.get('tag', '') if (ia2 and hasattr(ia2, 'items')) else ''
            res = [{
                'depth': depth,
                'name': (node.name or '').strip(),
                'role': str(node.role),
                'role_text': getattr(node, 'roleText', '') or '',
                'tag': tag,
                'cls': cls_name,
                'childCount': getattr(node, 'childCount', 0)
            }]
            for ch in (getattr(node, 'children', []) or []):
                res.extend(cls.dump_node(ch, depth + 1, max_depth))
            return res

    desktop = api.getDesktopObject()
    riot = [c for c in desktop.children if 'riot' in (c.name or '').lower()][0]
    html_doc = riot.children[3].children[0].children[0].children[0].children[0].children[0].children[1]
    app_main = html_doc.children[0]

    result = {
        'notifications': Dumper.dump_node(app_main.children[1]),
        'header': Dumper.dump_node(app_main.children[2]),
        'identity': Dumper.dump_node(app_main.children[3]),
        'side_panel': Dumper.dump_node(app_main.children[6]),
        'side_nav': Dumper.dump_node(app_main.children[7]),
        'transition_wrapper': Dumper.dump_node(app_main.children[8])
    }
except Exception:
    result = {'error': traceback.format_exc()}
'''

req = urllib.request.Request(BASE_URL, data=json.dumps({'action': 'execute_code', 'params': {'code': code}}).encode('utf-8'), headers=HEADERS)
res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))['result']['result']

with open('scripts/app_sections_dump.json', 'w', encoding='utf-8') as f:
    json.dump(res, f, ensure_ascii=False, indent=2)

print("Saved app sections to scripts/app_sections_dump.json")
for section_name, items in res.items():
    print(f"Section '{section_name}': {len(items)} nodes")
