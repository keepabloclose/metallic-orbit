
import sys
import os
import pandas as pd

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.odds_api_client import OddsApiClient

def diagnose():
    print("=== Diagnosing Odds API Live ===")
    client = OddsApiClient()
    
    # Test Premier League (E0)
    league_code = 'E0' 
    print(f"Fetching {league_code}...")
    
    # Force clear cache for this test?
    # os.remove("data_cache/odds_api/events_E0.json") 
    # Let's see what's in cache first or fetch fresh if needed.
    
    try:
        df = client.get_upcoming_odds(league_code)
        
        if df.empty:
            print("❌ No odds returned for E0.")
        else:
            print(f"✅ returned {len(df)} rows.")
            print("\nSample Data:")
            print(df.head(10).to_string())
            
            print("\nChecking for Nulls in Odds:")
            print(df[['B365H', 'B365D', 'B365A']].isna().sum())
            
            # Check specific names
            print("\nTeam Names found in API:")
            print(sorted(df['HomeTeam'].unique()))
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    diagnose()
