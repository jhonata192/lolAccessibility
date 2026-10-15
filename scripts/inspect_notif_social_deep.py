import urllib.request
import json
import time

BASE_URL = 'http://127.0.0.1:8765/action'
HEADERS = {'X-NVDA-Bridge-Token': 'nvda-bridge-secret-change-me', 'Content-Type': 'application/json'}

def inspect_tab(tab_idx, tab_name):
    code = '''
import api, NVDAObjects.IAccessible, time

tab_idx = %d

desktop = api.getDesktopObject()
riot = [c for c in desktop.children if 'riot' in (c.name or '').lower()][0]
html_doc = riot.children[3].children[0].children[0].children[0].children[0].children[0].children[1]

dialog = None
for p in html_doc.children:
    for c in (getattr(p, 'children', []) or []):
        for sub in (getattr(c, 'children', []) or []):
            if 'settings-drawer-dialog' in getattr(sub, 'IA2Attributes', {}).get('class', ''):
                dialog = sub
                break
        if dialog: break
    if dialog: break

content = dialog.children[1]
nav_list = content.children[1]

target_item = nav_list.children[tab_idx]
# Click inner link
for ch in NVDAObjects.IAccessible.IAccessible._get_children(target_item):
    try:
        ch.setFocus()
        ch.doAction()
    except Exception:
        pass

time.sleep(0.7)

# Re-find dialog
dialog2 = None
for p in html_doc.children:
    for c in (getattr(p, 'children', []) or []):
        for sub in (getattr(c, 'children', []) or []):
            if 'settings-drawer-dialog' in getattr(sub, 'IA2Attributes', {}).get('class', ''):
                dialog2 = sub
                break
        if dialog2: break
    if dialog2: break

active_dialog = dialog2 or dialog
content2 = active_dialog.children[1]
main = content2.children[4]
scroller = main.children[0].children[0]

class Scanner:
    @classmethod
    def dump_all(cls, o, depth=0):
        if depth > 6 or not o: return []
        res = []
        name = (o.name or '').encode('ascii', 'replace').decode('ascii')
        ia2 = getattr(o, 'IA2Attributes', None)
        c_cls = ia2.get('class', '') if (ia2 and hasattr(ia2, 'items')) else ''
        tag = ia2.get('tag', '') if (ia2 and hasattr(ia2, 'items')) else ''
        role = getattr(o, 'role', 0)
        
        if name or any(k in c_cls.lower() for k in ('title', 'button', 'checkbox', 'toggle', 'dropdown', 'slider', 'table', 'row', 'cell', 'radio')):
            res.append({
                'depth': depth,
                'name': name,
                'role': str(role),
                'tag': tag,
                'cls': c_cls
            })
        for ch in (getattr(o, 'children', []) or []):
            res.extend(cls.dump_all(ch, depth + 1))
        return res

result = Scanner.dump_all(scroller)
''' % tab_idx

    req = urllib.request.Request(BASE_URL, data=json.dumps({'action': 'execute_code', 'params': {'code': code}}).encode('utf-8'), headers=HEADERS)
    res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))['result']['result']
    return res

if __name__ == '__main__':
    for idx, name in [(2, 'NOTIFICAÇÕES'), (3, 'SOCIAL')]:
        print(f"\n=================== {name} (Index {idx}) ===================")
        items = inspect_tab(idx, name)
        for it in items:
            print(f"D{it['depth']}: {it['name']:<35} | {it['tag']:<6} | {it['cls']}")
