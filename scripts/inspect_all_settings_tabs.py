import urllib.request
import json
import time

BASE_URL = 'http://127.0.0.1:8765/action'
HEADERS = {'X-NVDA-Bridge-Token': 'nvda-bridge-secret-change-me', 'Content-Type': 'application/json'}

def click_tab_and_dump(tab_index):
    code = '''
import api, NVDAObjects.IAccessible, time

tab_idx = %d

desktop = api.getDesktopObject()
riot = [c for c in desktop.children if 'riot' in (c.name or '').lower()][0]
html_doc = riot.children[3].children[0].children[0].children[0].children[0].children[0].children[1]

# Find dialog among portals
dialog = None
for p in html_doc.children:
    for c in (getattr(p, 'children', []) or []):
        for sub in (getattr(c, 'children', []) or []):
            if 'settings-drawer-dialog' in getattr(sub, 'IA2Attributes', {}).get('class', ''):
                dialog = sub
                break
        if dialog: break
    if dialog: break

if not dialog:
    result = {'error': 'dialog not found'}
else:
    content = dialog.children[1]
    nav_list = content.children[1]

    # Click tab tab_idx
    target_item = nav_list.children[tab_idx]
    target_item.setFocus()
    try:
        target_item.doAction()
    except Exception:
        pass

    for ch in NVDAObjects.IAccessible.IAccessible._get_children(target_item):
        try:
            ch.doAction()
        except Exception:
            pass

    time.sleep(0.6)

    # Re-find dialog after click
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

    result = []
    for i, c in enumerate(scroller.children):
        ia2 = getattr(c, 'IA2Attributes', None)
        c_cls = ia2.get('class', '') if (ia2 and hasattr(ia2, 'items')) else ''
        tag = ia2.get('tag', '') if (ia2 and hasattr(ia2, 'items')) else ''
        name = (c.name or '').encode('ascii', 'replace').decode('ascii')
        result.append({
            'idx': i,
            'name': name,
            'tag': tag,
            'cls': c_cls,
            'subs': [(s.name or '').encode('ascii', 'replace').decode('ascii') for s in (getattr(c, 'children', []) or [])]
        })
''' % tab_index

    req = urllib.request.Request(BASE_URL, data=json.dumps({'action': 'execute_code', 'params': {'code': code}}).encode('utf-8'), headers=HEADERS)
    res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))['result']['result']
    return res

if __name__ == '__main__':
    for idx, tab_name in [(1, 'GERAL'), (2, 'NOTIFICAÇÕES'), (3, 'SOCIAL'), (5, 'TFT')]:
        print(f"\n=================== TAB {tab_name} (Index {idx}) ===================")
        items = click_tab_and_dump(idx)
        if isinstance(items, dict) and 'error' in items:
            print("Error:", items['error'])
        else:
            for it in items:
                print(f"[{it['idx']:02d}] Name: {repr(it['name']):<30} | Tag: {it['tag']:<6} | Class: {it['cls']}")
                if it['subs']:
                    print(f"     Subs: {it['subs']}")
