
import json
import pandas as pd
import os
import sys

# Simulation of app.py loading logic
def test_home_data_loading():
    CACHE_FILE = "data_cache/dashboard_data.json"
    
    if not os.path.exists(CACHE_FILE):
        print("FAIL: Cache file not found.")
        return

    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        bk_data = json.load(f)
        
    backend_matches = pd.DataFrame(bk_data['matches'])
    
    print(f"Loaded {len(backend_matches)} matches.")
    
    # Find Arsenal vs Liverpool
    match = backend_matches[
        (backend_matches['HomeTeam'].str.contains('Arsenal', case=False)) & 
        (backend_matches['AwayTeam'].str.contains('Liverpool', case=False))
    ]
    
    if match.empty:
        # Fallback to any PL match
        match = backend_matches[backend_matches['Div'] == 'E0'].head(1)
        if match.empty:
             print("FAIL: No E0/Arsenal matches found.")
             return
        print(f"Testing with fallback match: {match.iloc[0]['HomeTeam']} vs {match.iloc[0]['AwayTeam']}")
    else:
        print("Found Arsenal vs Liverpool.")

    row = match.iloc[0]
    
    # CHECK ODDS
    b365h = row.get('B365H')
    avgh = row.get('AvgH')
    btts = row.get('B365_BTTS_Yes')
    
    print(f"B365H: {b365h}")
    print(f"AvgH: {avgh}")
    print(f"BTTS: {btts}")
    
    if not b365h:
        print("FAIL: B365H is missing/null.")
    else:
        print("PASS: Real Odds Present.")
        
    if not btts:
        print("FAIL: BTTS is missing.")
    else:
        print("PASS: BTTS Present.")

    # Simulate Strategy Logic
    # Local Dominante
    odd_val = row.get('B365H') or row.get('AvgH')
    print(f"Strategy 'Local Dominante' would show: {odd_val}")
    
    # Ambos Marcan
    odd_btts = row.get('B365_BTTS_Yes') or row.get('B365GG')
    print(f"Strategy 'Ambos Marcan' would show: {odd_btts}")
    
    # Verify values are floats (or convertible)
    try:
        if b365h: float(b365h)
        if btts: float(btts)
        print("PASS: Odds are valid numbers.")
    except:
        print("FAIL: Odds are not valid numbers.")

if __name__ == "__main__":
    test_home_data_loading()
