
import json
import os
import glob
import sys

# Find latest odds file
files = glob.glob('data_cache/odds_api/odds_*.json')
if not files:
    print("No odds cache file found.")
    sys.exit()

latest_file = max(files, key=os.path.getctime)
print(f"Reading {latest_file}...")

with open(latest_file, 'r') as f:
    data = json.load(f)

# Find Leicester
for event in data:
    s = str(event)
    if 'Leicester' in s:
        bookies = event.get('bookmakers', {})
        if isinstance(bookies, dict):
             # Try to find Bet365
             for k, v in bookies.items():
                 if 'bet365' in k.lower():
                     if isinstance(v, list):
                         for m in v:
                             if 'goals over/under' in str(m).lower():
                                 print(f"\nRAW MARKET JSON (Goals Over/Under):")
                                 print(json.dumps(m, indent=2))
