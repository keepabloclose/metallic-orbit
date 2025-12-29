import pandas as pd
import requests
import io
from datetime import datetime

# URL for Premier League 25/26 (Current Season)
url = "https://www.football-data.co.uk/mmz4281/2526/E0.csv"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

try:
    print(f"Downloading {url}...")
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    
    # Read CSV
    df = pd.read_csv(io.StringIO(r.text))
    
    print(f"Total rows: {len(df)}")
    print("Columns:", df.columns.tolist()[:10])
    
    # Check for rows with no Result (FTHG is NaN or empty) representing upcoming?
    # Usually football-data.co.uk removes upcoming matches or doesn't have them.
    # But let's verify.
    
    upcoming = df[df['FTHG'].isna()]
    print(f"Rows with NaN FTHG: {len(upcoming)}")
    
    if not upcoming.empty:
        print("Sample upcoming:")
        print(upcoming[['Date', 'HomeTeam', 'AwayTeam', 'B365H', 'B365D', 'B365A']].head())
    else:
        # Check last few rows anyway, maybe they have FTHG but it's empty string?
        print("Tail of dataset:")
        print(df[['Date', 'HomeTeam', 'B365H']].tail())
        
except Exception as e:
    print(f"Error: {e}")
