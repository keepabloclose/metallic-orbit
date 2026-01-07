import pandas as pd
import sys
import os

sys.path.append(os.getcwd())
from src.data.upcoming import FixturesFetcher

def check_odds():
    print("--- Checking Odds Availability (Direct API) ---")
    from src.data.odds_api_client import OddsApiClient
    client = OddsApiClient()
    
    # Force refresh "E0" (Premiership)
    # The client takes the league CODE ('E0') and maps it internally if using get_upcoming_odds?
    # No, get_upcoming_odds takes 'league_code' but uses LEAGUE_SLUGS internally?
    # Let's check init. Yes lines 15-29 define slugs.
    # But line 97 define get_upcoming_odds(league_code...)
    
    # We use 'E0'
    print("Fetching E0 with force_refresh=True...")
    df = client.get_upcoming_odds('E0', force_refresh=True)
    
    if df.empty:
        print("No matches returned from API.")
        return

    print(f"\nFound {len(df)} matches.")
    
    # Check Columns
    odds_cols = [c for c in df.columns if 'B365' in c]
    print(f"Odds Columns Found: {len(odds_cols)}")
    print(sorted(odds_cols))
    
    # Check Over 1.5
    if 'B365_Over1.5' in df.columns:
        print(f"Over 1.5 Fill Rate: {df['B365_Over1.5'].notna().mean():.2%}")
    else:
        print("❌ B365_Over1.5 column MISSING")

    # Check BTTS
    if 'B365_BTTS_Yes' in df.columns:
        print(f"BTTS_Yes Fill Rate: {df['B365_BTTS_Yes'].notna().mean():.2%}")
        # Print sample
        print("Sample BTTS:", df['B365_BTTS_Yes'].dropna().head(3).tolist())
    else:
        print("❌ B365_BTTS_Yes column MISSING")

if __name__ == "__main__":
    check_odds()
