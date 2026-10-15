import win32gui
import win32con
import time

hwnd = win32gui.FindWindow(None, "Riot Client")
print("FindWindow 'Riot Client' result:", hwnd)

if hwnd:
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)
    print("Riot Client brought to foreground!")
else:
    # Buscar por títulos parecidos
    def enum_cb(h, _):
        t = win32gui.GetWindowText(h)
        if "Riot Client" in t:
            print(f"Candidate: {h} - {t}")
            win32gui.ShowWindow(h, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(h)
    win32gui.EnumWindows(enum_cb, None)
