import win32gui
import win32process
import psutil

riot_pids = set()
for p in psutil.process_iter(['pid', 'name']):
    if 'riot' in p.info['name'].lower():
        riot_pids.add((p.info['pid'], p.info['name']))

print(f"Riot Processes: {riot_pids}")

pids = {pid for pid, _ in riot_pids}

def cb(hwnd, extra):
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    if pid in pids:
        title = win32gui.GetWindowText(hwnd)
        cls = win32gui.GetClassName(hwnd)
        vis = win32gui.IsWindowVisible(hwnd)
        rect = win32gui.GetWindowRect(hwnd)
        print(f"HWND {hwnd}: Vis={vis}, Title='{title}', Class='{cls}', Rect={rect}")

win32gui.EnumWindows(cb, None)
