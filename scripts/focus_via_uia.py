import uiautomation as auto

root = auto.GetRootControl()
for child in root.GetChildren():
    name = child.Name or ""
    cls = child.ClassName or ""
    pid = child.ProcessId
    if "Riot" in name or "riot" in cls.lower() or pid in [1732, 2020, 5592, 4960, 5908, 8744]:
        print(f"UIA Window: Name='{name}', Class='{cls}', Handle={child.NativeWindowHandle}, PID={pid}")
        try:
            child.SetActive()
            child.SetFocus()
            print("Successfully activated and focused!")
        except Exception as e:
            print("Activation error:", e)
