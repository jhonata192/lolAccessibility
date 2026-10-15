import urllib.request
import json
import time

BASE_URL = 'http://127.0.0.1:8765/action'
HEADERS = {'X-NVDA-Bridge-Token': 'nvda-bridge-secret-change-me', 'Content-Type': 'application/json'}

def call(action, params={}):
    req = urllib.request.Request(BASE_URL, data=json.dumps({'action': action, 'params': params}).encode('utf-8'), headers=HEADERS)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read().decode())

inspect_account_menu = """
import traceback
try:
    import api, controlTypes, time

    class AccountScanner:
        @classmethod
        def find_riot(cls):
            desktop = api.getDesktopObject()
            for c in desktop.children:
                if 'riot' in (c.name or '').lower():
                    return c
            return None

        @classmethod
        def find_element_by_class(cls, o, match_str, depth=0):
            if depth > 20 or not o:
                return None
            ia2 = getattr(o, 'IA2Attributes', None)
            c_name = ia2.get('class', '') if (ia2 and hasattr(ia2, 'items')) else ''
            if match_str in c_name:
                return o
            for ch in (getattr(o, 'children', []) or []):
                res = cls.find_element_by_class(ch, match_str, depth + 1)
                if res:
                    return res
            return None

        @classmethod
        def collect_tree(cls, o, depth=0, out=None):
            if out is None:
                out = []
            if depth > 15 or not o:
                return out
            name = (getattr(o, 'name', '') or '').strip()
            ia2 = getattr(o, 'IA2Attributes', None)
            c_name = ia2.get('class', '') if (ia2 and hasattr(ia2, 'items')) else ''
            role = getattr(o, 'role', 0)
            role_text = getattr(o, 'roleText', '') or ''
            tag = ia2.get('tag', '') if (ia2 and hasattr(ia2, 'items')) else ''
            auto_id = ia2.get('id', '') if (ia2 and hasattr(ia2, 'items')) else ''
            
            out.append({
                'depth': depth,
                'name': name,
                'role': int(role) if hasattr(role, 'value') else int(role or 0),
                'role_text': str(role_text),
                'class': c_name,
                'tag': tag,
                'id': auto_id,
                'type': type(o).__name__
            })
            for ch in (getattr(o, 'children', []) or []):
                cls.collect_tree(ch, depth + 1, out)
            return out

    riot_win = AccountScanner.find_riot()
    target = AccountScanner.find_element_by_class(riot_win, 'identity-menu-disclosure')

    if target:
        target.setFocus()
        try:
            target.doAction()
        except Exception:
            pass
        time.sleep(0.6)

        # Collect only from riot_win
        items = AccountScanner.collect_tree(riot_win)
        result = {'items': items}
    else:
        result = {'error': 'identity-menu-disclosure not found'}
except Exception:
    result = {'error': traceback.format_exc()}
"""

if __name__ == '__main__':
    res = call('execute_code', {'code': inspect_account_menu})['result']
    data = res.get('result', {})
    if 'error' in data:
        print('Error:', data['error'])
    else:
        items = data.get('items', [])
        print(f"Total elements inspected: {len(items)}")
        with open('scripts/account_menu_dump.json', 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        print("Dump saved to scripts/account_menu_dump.json")

