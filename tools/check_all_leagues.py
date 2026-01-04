
import sys
import os
import pandas as pd
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.upcoming import FixturesFetcher

def check_all():
    fetcher = FixturesFetcher()
    leagues = ['E0', 'E1', 'SP1', 'SP2', 'D1', 'I1', 'F1']
    
    print("=== Checking All Leagues ===")
    df = fetcher.fetch_upcoming(leagues)
    
    if df.empty:
        print("[FAIL] No matches returned for ANY league.")
        return

    print(f"\nTotal Matches Found: {len(df)}")
    
    for league in leagues:
        league_df = df[df['Div'] == league]
        print(f"\nLeague {league}: {len(league_df)} matches")
        if not league_df.empty:
            print(league_df[['Date', 'Time', 'HomeTeam', 'AwayTeam']].head(3).to_string(index=False))
        else:
            print(f"[WARN] No matches for {league}")

if __name__ == "__main__":
    check_all()
