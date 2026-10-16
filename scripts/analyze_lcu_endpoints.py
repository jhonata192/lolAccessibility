import sys
import os
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lol_lib import riot_api_helper

lock = riot_api_helper.get_league_client_lockfile()
res = riot_api_helper.request_api(lock, "/help")
if res:
    funcs = res.get("functions", {})
    categories = {}
    for name, details in funcs.items():
        prefix = name.split("V1")[0].split("V2")[0] if ("V1" in name or "V2" in name) else name
        categories.setdefault(prefix, []).append(name)
    
    print(f"Total functions: {len(funcs)}")
    print(f"Total categories: {len(categories)}")
    
    summary = {}
    for cat, items in sorted(categories.items(), key=lambda x: -len(x[1])):
        summary[cat] = len(items)
        if len(items) >= 15:
            print(f"  {cat}: {len(items)} endpoints")
            
    with open("lcu_endpoints_summary.json", "w", encoding="utf-8") as f:
        json.dump(categories, f, indent=2)
    print("Salvo em lcu_endpoints_summary.json")
