import urllib.request
import json
import time

BASE_URL = 'http://127.0.0.1:8765/action'
HEADERS = {'X-NVDA-Bridge-Token': 'nvda-bridge-secret-change-me', 'Content-Type': 'application/json'}

def inspect_social_tab(tab_idx):
    code = '''
import api, NVDAObjects.IAccessible, time

tab_idx = %d

desktop = api.getDesktopObject()
riot = [c for c in desktop.children if 'riot' in (c.name or '').lower()][0]
html_doc = riot.children[3].children[0].children[0].children[0].children[0].children[0].children[1]
side_panel = html_doc.children[0].children[6]

# Find tabs in side_panel
tabs_container = None
for c in (getattr(side_panel, 'children', []) or []):
    for sub in (getattr(c, 'children', []) or []):
        if 'tab' in getattr(sub, 'IA2Attributes', {}).get('class', ''):
            tabs_container = c
            break
    if tabs_container: break

tabs = []
if tabs_container:
    for c in tabs_container.children:
        if 'tab-button' in getattr(c, 'IA2Attributes', {}).get('class', ''):
            tabs.append(c)

target_tab = tabs[tab_idx] if tab_idx < len(tabs) else None
if target_tab:
    target_tab.setFocus()
    try:
        target_tab.doAction()
    except Exception:
        pass
    time.sleep(0.6)

class SScanner:
    @classmethod
    def dump_panel(cls, o, depth=0):
        if depth > 6 or not o: return []
        res = []
        name = (o.name or '').encode('ascii', 'replace').decode('ascii')
        ia2 = getattr(o, 'IA2Attributes', None)
        c_cls = ia2.get('class', '') if (ia2 and hasattr(ia2, 'items')) else ''
        tag = ia2.get('tag', '') if (ia2 and hasattr(ia2, 'items')) else ''
        role = getattr(o, 'role', 0)
        
        if name or any(k in c_cls.lower() for k in ('tab', 'item', 'button', 'input', 'list', 'chat', 'message', 'friend', 'empty', 'fallback')):
            res.append({'depth': depth, 'name': name, 'role': str(role), 'tag': tag, 'cls': c_cls})
        for ch in (getattr(o, 'children', []) or []):
            res.extend(cls.dump_panel(ch, depth + 1))
        return res

result = {
    'tab_name': target_tab.name if target_tab else None,
    'nodes': SScanner.dump_panel(side_panel)
}
''' % tab_idx

    req = urllib.request.Request(BASE_URL, data=json.dumps({'action': 'execute_code', 'params': {'code': code}}).encode('utf-8'), headers=HEADERS)
    res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))['result']['result']
    return res

if __name__ == '__main__':
    for idx, name in [(1, 'CONVERSAS'), (2, 'PEDIDOS DE AMIZADE'), (0, 'AMIGOS')]:
        print(f"\n=================== SOCIAL TAB: {name} (Index {idx}) ===================")
        data = inspect_social_tab(idx)
        print(f"Tab Name: {data.get('tab_name')} | Nodes: {len(data.get('nodes', []))}")
        for n in data.get('nodes', [])[:20]:
            print(f"D{n['depth']}: {n['name']:<30} | {n['tag']:<6} | {n['cls']}")
