import urllib.request
import json
import time

BASE_URL = 'http://127.0.0.1:8765/action'
HEADERS = {'X-NVDA-Bridge-Token': 'nvda-bridge-secret-change-me', 'Content-Type': 'application/json'}

def call(action, params={}):
    req = urllib.request.Request(BASE_URL, data=json.dumps({'action': action, 'params': params}).encode('utf-8'), headers=HEADERS)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read().decode())

# Step 1: Focus identity menu disclosure
code_open_menu = '''
import api, time
desktop = api.getDesktopObject()
riot = [c for c in desktop.children if 'riot' in (c.name or '').lower()][0]

class Scanner:
    @classmethod
    def find_el(cls, o, match):
        ia2 = getattr(o, 'IA2Attributes', None)
        c = ia2.get('class', '') if (ia2 and hasattr(ia2, 'items')) else ''
        if match in c: return o
        for ch in (getattr(o, 'children', []) or []):
            res = cls.find_el(ch, match)
            if res: return res
        return None

target = Scanner.find_el(riot, 'identity-menu-disclosure')
if target:
    target.setFocus()
    result = {'focused': target.name}
else:
    result = {'error': 'not found'}
'''

res = call('execute_code', {'code': code_open_menu})['result']
print("Focus account menu:", res)

# Send Enter or Space to open dropdown
time.sleep(0.3)
call('send_key', {'key': 'space'})
time.sleep(0.5)

# Now check focus or navigate down
for i in range(5):
    call('send_key', {'key': 'down'})
    time.sleep(0.3)
    speech = call('get_speech_history', {'count': 1}).get('result', {}).get('phrases', [])
    focus = call('get_current_focus', {}).get('result', {})
    name = (focus.get('name') or '').encode('ascii', 'replace').decode('ascii')
    spk = (speech[-1] if speech else '').encode('ascii', 'replace').decode('ascii')
    print(f"Down {i+1}: Name='{name}', Speech='{spk}'")
