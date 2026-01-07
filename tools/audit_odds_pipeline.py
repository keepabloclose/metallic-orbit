
import sys
import os
import pandas as pd

# Add project root
sys.path.append(os.getcwd())

from src.data.upcoming import FixturesFetcher

def audit():
    print("--- AUDIT START ---")
    fetcher = FixturesFetcher()
    
    # Run logic
    print("Running fetch_upcoming(['E0'])...")
    df = fetcher.fetch_upcoming(['E0'])
    
    # Find Match
    print("\n--- FINDING MATCH: Man City vs Brighton ---")
    # Try text search
    mask = df['HomeTeam'].str.contains('City') & df['AwayTeam'].str.contains('Brighton')
    matches = df[mask]
    
    if matches.empty:
        print("MATCH NOT FOUND IN FINAL DATAFRAME!")
        print("All matches:")
        print(df[['HomeTeam', 'AwayTeam', 'Date']].to_string())
    else:
        row = matches.iloc[0]
        print("Match Found:")
        print(row[['HomeTeam', 'AwayTeam', 'Date', 'Time']])
        print(f"B365H: {row.get('B365H')}")
        print(f"B365D: {row.get('B365D')}")
        print(f"B365A: {row.get('B365A')}")
        
        if 'MergeKey' in row:
            print(f"MergeKey: {row['MergeKey']}")

    # CHECK FALLBACKS
    print("\n--- CHECKING REAL ODDS CSV ---")
    real_path = os.path.join(os.getcwd(), 'src/data/real_odds.csv')
    if os.path.exists(real_path):
        try:
            ro = pd.read_csv(real_path)
            mask_ro = ro['HomeTeam'].str.contains('City') & ro['AwayTeam'].str.contains('Brighton')
            if not ro[mask_ro].empty:
                print("Found match in real_odds.csv:")
                print(ro[mask_ro][['HomeTeam', 'AwayTeam', 'Real_B365H']])
            else:
                print("Match NOT in real_odds.csv")
        except:
             print("Error reading real_odds.csv")
    else:
        print("real_odds.csv does not exist.")

if __name__ == "__main__":
    audit()
