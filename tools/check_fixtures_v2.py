
import sys
import os
import pandas as pd
# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.upcoming import FixturesFetcher

def check():
    print("Initializing Fetcher...")
    fetcher = FixturesFetcher()
    
    print("Fetching SP2 (La Liga 2)...")
    # We force fetch only SP2 if possible, but the class usually fetches all in list.
    # Let's inspect the LEAGUE_URLS in the instance
    print(f"URLs: {fetcher.LEAGUE_URLS.get('SP2')}")
    
    df = fetcher.fetch_upcoming(['SP2', 'E1'])
    
    if df is not None and not df.empty:
        print(f"Found {len(df)} matches.")
        print(df[['Date', 'Time', 'HomeTeam', 'AwayTeam', 'Div']].head())
        
        # Check today's date
        today = pd.Timestamp.now().normalize()
        print(f"Today is: {today}")
        
        today_matches = df[pd.to_datetime(df['Date'], dayfirst=True).dt.normalize() == today]
        print(f"Matches for Today ({today.date()}):")
        if not today_matches.empty:
            print(today_matches[['Time', 'HomeTeam', 'AwayTeam']])
        else:
            print("No matches for today in fetched data.")
    else:
        print("No data fetched.")

if __name__ == "__main__":
    check()
