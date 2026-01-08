import json
import os

try:
    with open('data_cache/dashboard_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print(f"Loaded {len(data['matches'])} matches.")
    
    count_btts = 0
    sample_btts = None
    
    for m in data['matches']:
        keys = [k for k in m.keys() if 'B365' in k]
        if 'B365_BTTS_Yes' in keys:
            count_btts += 1
            if not sample_btts:
                 sample_btts = {k: m[k] for k in keys}
                 
    print(f"Found BTTS in {count_btts} matches.")
    if sample_btts:
        print("Sample Odds:", sample_btts)
    else:
        print("NO BTTS FOUND. Sample matched keys:", [k for k in data['matches'][0].keys() if 'B365' in k] if data['matches'] else "No matches")
        
except Exception as e:
    print(f"Error: {e}")
