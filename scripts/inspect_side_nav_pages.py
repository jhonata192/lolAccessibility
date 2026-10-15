import urllib.request
import json
import time

BASE_URL = 'http://127.0.0.1:8765/action'
HEADERS = {'X-NVDA-Bridge-Token': 'nvda-bridge-secret-change-me', 'Content-Type': 'application/json'}

def switch_nav_and_dump(nav_target_name):
    code = '''
import api, NVDAObjects.IAccessible, time

target_label = %s

desktop = api.getDesktopObject()
riot = [c for c in desktop.children if 'riot' in (c.name or '').lower()][0]
html_doc = riot.children[3].children[0].children[0].children[0].children[0].children[0].children[1]
app_main = html_doc.children[0]
side_nav = app_main.children[7]

# Find button with target_label in side_nav
btn = None
for c in (getattr(side_nav, 'children', []) or []):
    if c.name and target_label.lower() in c.name.lower():
        btn = c
        break
    for sub in (getattr(c, 'children', []) or []):
        if sub.name and target_label.lower() in sub.name.lower():
            btn = sub
            break
    if btn: break

if btn:
    btn.setFocus()
    try:
        btn.doAction()
    except Exception:
        pass
    time.sleep(1.0)

# Now inspect transition-wrapper
tw = app_main.children[8]

class PageScanner:
    @classmethod
    def dump_page(cls, o, depth=0):
        if depth > 6 or not o: return []
        res = []
        name = (o.name or '').encode('ascii', 'replace').decode('ascii')
        ia2 = getattr(o, 'IA2Attributes', None)
        c_cls = ia2.get('class', '') if (ia2 and hasattr(ia2, 'items')) else ''
        tag = ia2.get('tag', '') if (ia2 and hasattr(ia2, 'items')) else ''
        role = getattr(o, 'role', 0)
        role_text = getattr(o, 'roleText', '') or ''
        
        # Keep interactive or labelled elements
        if name or any(k in c_cls.lower() for k in ('card', 'grid', 'game', 'hero', 'badge', 'button', 'tab', 'item', 'title', 'headline', 'status', 'view')):
            res.append({
                'depth': depth,
                'name': name,
                'role': str(role),
                'role_text': role_text,
                'tag': tag,
                'cls': c_cls
            })
        for ch in (getattr(o, 'children', []) or []):
            res.extend(cls.dump_page(ch, depth + 1))
        return res

result = {
    'btn_found': btn.name if btn else None,
    'page_nodes': PageScanner.dump_page(tw)
}
''' % repr(nav_target_name)

    req = urllib.request.Request(BASE_URL, data=json.dumps({'action': 'execute_code', 'params': {'code': code}}).encode('utf-8'), headers=HEADERS)
    res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))['result']['result']
    return res

if __name__ == '__main__':
    for page in ['Meus Jogos', 'Página Inicial', 'League of Legends']:
        print(f"\n=================== NAVIGATING TO: {page} ===================")
        data = switch_nav_and_dump(page)
        nodes = data.get('page_nodes', [])
        print(f"Target button: {data.get('btn_found')} | Page nodes found: {len(nodes)}")
        for n in nodes[:25]:
            print(f"D{n['depth']}: {n['name']:<35} | {n['tag']:<6} | {n['cls'][:40]}")
