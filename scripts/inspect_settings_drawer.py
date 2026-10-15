import urllib.request
import json
import time

BASE_URL = 'http://127.0.0.1:8765/action'
HEADERS = {'X-NVDA-Bridge-Token': 'nvda-bridge-secret-change-me', 'Content-Type': 'application/json'}

def call(action, params={}):
    req = urllib.request.Request(BASE_URL, data=json.dumps({'action': action, 'params': params}).encode('utf-8'), headers=HEADERS)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read().decode())

code = '''
import api, NVDAObjects.IAccessible, time, traceback

try:
    desktop = api.getDesktopObject()
    riot = [c for c in desktop.children if 'riot' in (c.name or '').lower()][0]

    class Scanner:
        @classmethod
        def find_container(cls, o):
            ia2 = getattr(o, 'IA2Attributes', None)
            c = ia2.get('class', '') if (ia2 and hasattr(ia2, 'items')) else ''
            if 'identity-menu-container' in c:
                return o
            for ch in (getattr(o, 'children', []) or []):
                res = cls.find_container(ch)
                if res: return res
            return None

    cnt = Scanner.find_container(riot)
    cfg_btn = None
    if cnt:
        for c in NVDAObjects.IAccessible.IAccessible._get_children(cnt):
            if c.name and 'configura' in c.name.lower():
                cfg_btn = c
                break

    if cfg_btn:
        cfg_btn.setFocus()
        try:
            cfg_btn.doAction()
        except Exception:
            pass
        time.sleep(1.0)

    # Now let's find settings-drawer or modal
    class SettingsScanner:
        @classmethod
        def collect_tree(cls, o, depth=0, out=None):
            if out is None: out = []
            if depth > 20 or not o: return out
            name = (getattr(o, 'name', '') or '').strip()
            ia2 = getattr(o, 'IA2Attributes', None)
            c_name = ia2.get('class', '') if (ia2 and hasattr(ia2, 'items')) else ''
            role = getattr(o, 'role', 0)
            role_text = getattr(o, 'roleText', '') or ''
            tag = ia2.get('tag', '') if (ia2 and hasattr(ia2, 'items')) else ''
            auto_id = ia2.get('id', '') if (ia2 and hasattr(ia2, 'items')) else ''
            val = getattr(o, 'value', '') or ''
            states = [str(s) for s in (getattr(o, 'states', set()) or set())]
            
            # Use raw children if children list is empty but childCount > 0
            sub_children = getattr(o, 'children', []) or []
            if not sub_children and getattr(o, 'childCount', 0) > 0 and hasattr(o, 'IAccessibleObject'):
                try:
                    sub_children = NVDAObjects.IAccessible.IAccessible._get_children(o)
                except Exception:
                    pass

            out.append({
                'depth': depth,
                'name': name,
                'role': int(role) if hasattr(role, 'value') else int(role or 0),
                'role_text': str(role_text),
                'class': c_name,
                'tag': tag,
                'id': auto_id,
                'value': val,
                'states': states,
                'type': type(o).__name__,
                'child_count': len(sub_children)
            })

            for ch in sub_children:
                cls.collect_tree(ch, depth + 1, out)
            return out

    # Find settings drawer in riot
    drawer_items = SettingsScanner.collect_tree(riot)
    result = {'items': drawer_items}
except Exception:
    result = {'error': traceback.format_exc()}
'''

if __name__ == '__main__':
    res = call('execute_code', {'code': code})['result']
    data = res.get('result', {})
    if 'error' in data:
        print('Error:', data['error'])
    else:
        items = data.get('items', [])
        print(f"Total elements inspected: {len(items)}")
        with open('scripts/settings_drawer_dump.json', 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        print("Dump saved to scripts/settings_drawer_dump.json")
