
import sys
import os
import requests
import pandas as pd
import io

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.upcoming import FixturesFetcher

def diagnose_sp2():
    fetcher = FixturesFetcher()
    candidates = [
        'segunda-division-2025', 
        'segunda-division-2024',
        'la-liga-2-2025',
        'la-liga-2-2024',
        'spain-segunda-2025',
        'spain-segunda-2024',
        'segunda-division-2024-2025'
    ]
    
    found_slug = None
    csv_content = None
    
    print("--- STARTING BRUTE FORCE DIAGNOSTIC ---")
    
    for slug in candidates:
        url = f"{fetcher.BASE_URL}/{slug}-GMTStandardTime.csv"
        print(f"Testing: {slug}...")
        try:
            # We use verify=False to ignore SSL errors if any
            response = requests.get(url, verify=False, timeout=5)
            
            if response.status_code == 200:
                # Check for 404 text disguised as 200
                if b"Page not found" in response.content:
                    print(f"[FAIL] {slug} returned 200 but content is 404 page.")
                    continue
                    
                print(f"[SUCCESS] Found valid slug: {slug}")
                found_slug = slug
                csv_content = response.content.decode('utf-8')
                break
            else:
                 print(f"[FAIL] {slug} status {response.status_code}")
                 
        except Exception as e:
            print(f"[ERROR] {slug} connection failed: {e}")

    if found_slug and csv_content:
        print(f"\n--- PARSING DATA for {found_slug} ---")
        try:
            df = pd.read_csv(io.StringIO(csv_content))
            print("Columns found:", df.columns.tolist())
            
            if 'Date' in df.columns:
                df['DateObj'] = pd.to_datetime(df['Date'], dayfirst=True)
                today = pd.Timestamp.now().normalize()
                print(f"Today (Normalized): {today}")
                
                future = df[df['DateObj'] >= today].sort_values('DateObj')
                print(f"Found {len(future)} matches from today onwards.")
                
                if not future.empty:
                    print("Next 5 matches:")
                    print(future[['Date', 'Time', 'Home Team', 'Away Team']].head(5))
                else:
                    print("WARNING: No future matches found in CSV.")
            else:
                print("CRITICAL: 'Date' column not found in CSV.")
        except Exception as e:
            print(f"Parsing error: {e}")
    else:
        print("\nFAILURE: Could not find any working URL for La Liga 2.")

if __name__ == "__main__":
    diagnose_sp2()
