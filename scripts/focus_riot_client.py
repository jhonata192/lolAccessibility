import win32gui
import win32process
import win32con
import time

riot_pids = set()
import psutil
for p in psutil.process_iter(['pid', 'name']):
    if 'riot' in p.info['name'].lower():
        riot_pids.add(p.info['pid'])

found = []
def cb(hwnd, extra):
    if win32gui.IsWindowVisible(hwnd):
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if pid in riot_pids:
            title = win32gui.GetWindowText(hwnd)
            cls = win32gui.GetClassName(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            w = rect[2] - rect[0]
            h = rect[3] - rect[1]
            if w > 400 and h > 300:
                found.append((hwnd, pid, cls, title, rect))

win32gui.EnumWindows(cb, None)
print(f"Found {len(found)} candidate windows:")
for hwnd, pid, cls, title, rect in found:
    print(f"HWND {hwnd}: PID {pid}, Class '{cls}', Title '{title}', Rect {rect}")
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.3)
