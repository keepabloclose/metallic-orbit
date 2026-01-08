
import json
import pandas as pd
import datetime

def test_filter():
    # 1. Load Data
    with open('data_cache/dashboard_data.json', 'r', encoding='utf-8') as f:
        bk_data = json.load(f)
    upcoming = pd.DataFrame(bk_data['matches'])
    
    print(f"Loaded {len(upcoming)} matches.")
    
    # 2. Simulate Filter Inputs (Today = 2026-01-09)
    today = datetime.date(2026, 1, 9)
    date_range = [today, today]
    start_date, end_date = date_range
    
    print(f"Filtering for: {start_date}")
    
    # 3. Apply Logic
    try:
        upcoming['DateRaw'] = upcoming['Date']
        upcoming['Date'] = pd.to_datetime(upcoming['Date'], dayfirst=True, errors='coerce')
        
        # Check parsing
        jan9_raw = upcoming[upcoming['DateRaw'].astype(str).str.contains('09/01') | upcoming['DateRaw'].astype(str).str.contains('2026-01-09')]
        print("\n--- RAW MATCHES FOR JAN 9 ---")
        print(jan9_raw[['DateRaw', 'Date', 'HomeTeam']].head())
        
        upcoming['DateNorm'] = upcoming['Date'].dt.normalize().dt.tz_localize(None)
        
        ts_start = pd.Timestamp(start_date).normalize().tz_localize(None)
        ts_end = pd.Timestamp(end_date).normalize().tz_localize(None)
        
        print(f"\nTarget Range: {ts_start} to {ts_end}")
        
        # Filter
        res = upcoming[upcoming['DateNorm'] == ts_start]
        print(f"\nMatches Found: {len(res)}")
        if len(res) > 0:
            print(res[['HomeTeam', 'DateNorm']].head())
        else:
             print("FAIL: No matches found.")
             # Debug mismatches
             print("\nUnique Norm Dates in Data:")
             print(upcoming['DateNorm'].unique())
             
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_filter()
