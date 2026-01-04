
import sys
import os
import pandas as pd
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.upcoming import FixturesFetcher

def show_games():
    fetcher = FixturesFetcher()
    print("Fetching La Liga 2 (SP2) games...")
    df = fetcher.fetch_upcoming(['SP2'])
    
    if not df.empty:
        # Filter for future just in case, though fetch_upcoming does it
        # Sort by date
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        
        print(f"\nNext 10 Games for La Liga 2:")
        print(df[['Date', 'Time', 'HomeTeam', 'AwayTeam']].head(10).to_string(index=False))
    else:
        print("No matches found.")

if __name__ == "__main__":
    show_games()
