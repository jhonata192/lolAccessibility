# -*- coding: utf-8 -*-
import struct
import json
import re

path = r"C:\Riot Games\Riot Client\RiotClientElectron\resources\app.asar"
with open(path, "rb") as f:
    d = f.read(16)
    size1, size2, size3, json_len = struct.unpack("<IIII", d)
    header = json.loads(f.read(json_len).decode("utf-8"))
    
    main_entry = header["files"]["dist"]["files"]["main"]["files"]["main.js"]
    offset = 16 + json_len + int(main_entry["offset"])
    f.seek(offset)
    main_code = f.read(main_entry["size"]).decode("utf-8", errors="ignore")

# Find ipcMain handlers
ipc_handles = re.findall(r"ipcMain\.(?:handle|on)\([\"']([^\"']+)[\"']", main_code)
print("IPC Channels in Riot Client main.js:")
for ch in sorted(set(ipc_handles)):
    print("  IPC:", ch)

# Search for launch game, play, or endpoints
keywords = ["launch", "play", "install", "patch", "start", "game", "product", "lockfile"]
found_kw = {}
for kw in keywords:
    matches = re.findall(r"[\"'][^\"']*" + kw + r"[^\"']*[\"']", main_code, re.IGNORECASE)
    cleaned = [m.strip("\"'") for m in matches if 3 < len(m.strip("\"'")) < 60]
    found_kw[kw] = sorted(set(cleaned))[:10]

print("\nKeywords in main.js:")
for k, v in found_kw.items():
    print(f"  [{k}] ({len(v)}):", v[:5])
