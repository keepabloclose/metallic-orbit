
import sys
import os
import pandas as pd
sys.path.append(os.getcwd())

from src.data.upcoming import FixturesFetcher

def check():
    fetcher = FixturesFetcher()
    # Fetch all leagues to replicate "170 matches"
    leagues = ['SP1', 'SP2', 'E0', 'E1', 'D1', 'I1', 'F1', 'P1', 'N1']
    df = fetcher.fetch_upcoming(leagues)
    
    print(f"Total Matches: {len(df)}")
    print("\nSample Dates (Raw):")
    print(df['Date'].head(10))
    
    # Simulate Filter
    today = pd.Timestamp.now().normalize() - pd.Timedelta(days=1) # Adjust if timezone differs
    # Actually user says Today is Jan 8.
    
    # Try Filter
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    df['DateNorm'] = df['Date'].dt.normalize()
    
    print("\nSample Dates (Norm):")
    print(df['DateNorm'].head(10))
    
    search_date = pd.Timestamp("2026-01-08").normalize()
    filtered = df[df['DateNorm'] == search_date]
    
    print(f"\nMatches for {search_date.date()}: {len(filtered)}")
    if not filtered.empty:
        print(filtered[['Date', 'HomeTeam', 'AwayTeam']])
        
    # Check Jan 9
    search_date_9 = pd.Timestamp("2026-01-09").normalize()
    filtered_9 = df[df['DateNorm'] == search_date_9]
    print(f"\nMatches for {search_date_9.date()}: {len(filtered_9)}")
    if not filtered_9.empty:
        print(filtered_9[['Div', 'Date', 'HomeTeam', 'AwayTeam']])

if __name__ == "__main__":
    check()
