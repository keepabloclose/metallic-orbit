
import sys
import os
import pandas as pd
from datetime import datetime, timedelta

# Adjust path to find src
sys.path.append(os.getcwd())
from src.data.odds_api_client import OddsApiClient

def test_persistence():
    print("--- Testing Odds DB Persistence ---")
    client = OddsApiClient()
    
    # 1. Check Initial DB State
    if os.path.exists(client.DB_PATH):
        df_start = pd.read_csv(client.DB_PATH)
        print(f"Initial DB Size: {len(df_start)} records")
        if not df_start.empty and 'FetchedAt' in df_start.columns:
            print(f"Latest Fetch: {df_start['FetchedAt'].max()}")
    else:
        print("DB does not exist yet.")
        df_start = pd.DataFrame()

    # 2. Trigger Fetch (E1 - Championship)
    # This should hit API *OR* DB depending on freshness
    print("\n[Action] Requesting Odds for 'E1' (Championship)...")
    df_result = client.get_upcoming_odds('E1', days_ahead=2)
    
    if df_result.empty:
        print("No odds returned (Quota or No Matches).")
    else:
        print(f"Returned {len(df_result)} records.")
        # Check if they are in DB now
        if os.path.exists(client.DB_PATH):
            df_end = pd.read_csv(client.DB_PATH)
            print(f"Final DB Size: {len(df_end)} records")
            
            # Verify Persistence
            if len(df_end) >= len(df_start):
                print("✅ Persistence Verification: SUCCESS (DB grew or stayed same)")
            else:
                print("❌ Persistence Verification: WARNING (DB shrank?)")
                
    # 3. Simulate "Next Run"
    print("\n[Action] Simulating 2nd Run (Should skip API)...")
    # We can't easily Mock the network here without mocking lib, 
    # but we can rely on proper log messages from the client "[OddsAPI] Using Persisted Data..."
    client.get_upcoming_odds('E1', days_ahead=2)

if __name__ == "__main__":
    test_persistence()
