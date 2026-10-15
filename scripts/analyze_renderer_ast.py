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
    code = f.read(renderer_entry["size"]).decode("utf-8", errors="ignore")

# 1. Routes
routes = set(re.findall(r'path:\s*["\'](/[^"\']+)["\']', code))
print(f"Routes found in renderer.js ({len(routes)}):")
for r in sorted(routes):
    print(" ", r)

# 2. Buttons / Testids / Roles
test_ids = set(re.findall(r'data-testid["\']?\s*[:=]\s*["\']([^"\']+)["\']', code))
print(f"\nTest IDs found ({len(test_ids)}):")
for tid in sorted(test_ids):
    print(" ", tid)

# 3. Action button text or classes
action_btns = set(re.findall(r'["\']([a-zA-Z0-9_\-]+action-button[a-zA-Z0-9_\-]*)["\']', code, re.I))
print(f"\nAction button classes/ids ({len(action_btns)}):")
for ab in sorted(action_btns):
    print(" ", ab)

# 4. Search for play / launch game invocation
launches = set(re.findall(r'([a-zA-Z0-9_]+launch[a-zA-Z0-9_]*)', code, re.I))
print(f"\nLaunch identifiers ({len(launches)}):")
for l in sorted([x for x in launches if len(x) > 6 and not x.startswith("_")])[:40]:
    print(" ", l)

# 5. Search for product names
products = set(re.findall(r'productName["\']?\s*[:=]\s*["\']([^"\']+)["\']', code))
print(f"\nProduct names ({len(products)}):")
for p in sorted(products):
    print(" ", p)
