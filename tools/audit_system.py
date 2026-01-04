
import sys
import os
import pandas as pd
import urllib3

# Suppress warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.upcoming import FixturesFetcher
from src.engine.predictor import Predictor

def audit_system():
    print("=== STARTING SYSTEM AUDIT ===")
    
    # 1. Test FixturesFetcher for SP2
    print("\n[Audit 1] Fetching Upcoming Matches for SP2...")
    fetcher = FixturesFetcher()
    
    # Force fetch SP2 only
    try:
        df = fetcher.fetch_upcoming(['SP2'])
        if df.empty:
            print("[FAIL] No upcoming matches found for SP2.")
        else:
            print(f"[PASS] Found {len(df)} matches.")
            print(df[['Date', 'Time', 'HomeTeam', 'AwayTeam']].head(10))
            
            # Check for Eibar
            mask = df['HomeTeam'].str.contains('Eibar', case=False) | df['AwayTeam'].str.contains('Eibar', case=False)
            eibar = df[mask]
            if not eibar.empty:
                print(f"\n[PASS] Found Eibar match:\n{eibar[['Date', 'HomeTeam', 'AwayTeam']]}")
            else:
                print("\n[WARN] Eibar match NOT found in next 15/30 matches.")

    except Exception as e:
        print(f"[FAIL] Error fetching SP2: {e}")
        return

    # 2. Test Normalization
    print("\n[Audit 2] Checking Team Name Normalization...")
    # Mock predictor (empty history is fine for this test)
    pred = Predictor(pd.DataFrame(columns=['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']))
    
    test_names = [
        'SD Eibar', 'Eibar', 
        'CD Mirandes', 'Mirandes', 'Mirandés',
        'Real Zaragoza', 'Zaragoza',
        'Levante UD', 'Levante'
    ]
    
    for name in test_names:
        norm = pred.normalize_name(name)
        print(f"'{name}' -> '{norm}'")

if __name__ == "__main__":
    audit_system()
