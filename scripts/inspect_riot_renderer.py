# -*- coding: utf-8 -*-
import struct
import json
import re

path = r"C:\Riot Games\Riot Client\RiotClientElectron\resources\app.asar"
with open(path, "rb") as f:
    d = f.read(16)
    size1, size2, size3, json_len = struct.unpack("<IIII", d)
    header = json.loads(f.read(json_len).decode("utf-8"))
    
    renderer_entry = header["files"]["dist"]["files"]["renderer"]["files"]["renderer.js"]
    offset = 16 + json_len + int(renderer_entry["offset"])
    f.seek(offset)
    # Read first 1MB or search directly
    renderer_code = f.read(renderer_entry["size"]).decode("utf-8", errors="ignore")

print(f"renderer.js size: {len(renderer_code)} bytes")

# Find REST endpoints in renderer.js
endpoints = set(re.findall(r"[\"'](/[a-zA-Z0-9_\-\/]+)[\"']", renderer_code))
riot_eps = [ep for ep in endpoints if any(k in ep for k in ["product", "patch", "install", "launch", "game", "session", "user", "player", "eula", "terms"])]
print(f"Riot Client REST Endpoints in renderer ({len(riot_eps)}):")
for ep in sorted(riot_eps)[:40]:
    print("  ", ep)

# Find HTML data-testid or aria labels
test_ids = set(re.findall(r"data-testid=[\"']([^\"']+)[\"']", renderer_code))
print(f"\ndata-testid attributes found ({len(test_ids)}):")
for tid in sorted(test_ids)[:30]:
    print("  test-id:", tid)

# Find button texts or actions
aria_labels = set(re.findall(r"aria-label=[\"']([^\"']+)[\"']", renderer_code))
print(f"\naria-label attributes found ({len(aria_labels)}):")
for al in sorted(aria_labels)[:30]:
    print("  aria:", al)
