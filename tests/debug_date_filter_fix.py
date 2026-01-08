
import json
import pandas as pd
import datetime

def test_filter_fix():
    # 1. Load Data
    with open('data_cache/dashboard_data.json', 'r', encoding='utf-8') as f:
        bk_data = json.load(f)
    upcoming = pd.DataFrame(bk_data['matches'])
    
    print(f"Loaded {len(upcoming)} matches.")
    
    # 2. Simulate Filter Inputs (Today = 2026-01-09)
    today = datetime.date(2026, 1, 9)
    # Target String
    target_str = today.strftime("%Y-%m-%d")
    print(f"Target String: {target_str}")
    
    # 3. Apply String Logic
    try:
        # Convert to datetime first to handle various inputs, then format
        # dashboard_data.json is ISO (YYYY-MM-DD), so dayfirst=True causes erroneous YYYY-DD-MM parsing!
        upcoming['DateObj'] = pd.to_datetime(upcoming['Date'], errors='coerce') # Let pandas infer (usually correct for ISO)
        upcoming['DateStr'] = upcoming['DateObj'].dt.strftime('%Y-%m-%d')
        
        print("\n--- SAMPLE DATE STRINGS ---")
        print(upcoming[['Date', 'DateStr']].head())
        
        # Filter
        res = upcoming[upcoming['DateStr'] == target_str]
        
        print(f"\nMatches Found (String Method): {len(res)}")
        if len(res) > 0:
            print(res[['HomeTeam', 'DateStr']].head())
        else:
             print("FAIL: No matches found.")
             
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_filter_fix()
