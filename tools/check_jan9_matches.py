
import json
import pandas as pd
from datetime import datetime

try:
    with open('data_cache/dashboard_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    matches = data['matches']
    print(f"Total Matches: {len(matches)}")
    
    # Check Dates
    jan9 = []
    
    for m in matches:
        d = m.get('Date') # Expected format dd/mm/yyyy or yyyy-mm-dd
        # Simple string check first
        if '09/01' in str(d) or '2026-01-09' in str(d) or 'Jan 09' in str(d):
            jan9.append(m)
            
    print(f"Matches found for Jan 9: {len(jan9)}")
    for m in jan9:
        print(f" - {m.get('HomeTeam')} vs {m.get('AwayTeam')} ({m.get('Date')} {m.get('Time')}) Div: {m.get('Div')}")
        
except Exception as e:
    print(f"Error: {e}")
