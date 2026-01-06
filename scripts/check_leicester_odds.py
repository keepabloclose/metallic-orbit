
import sys
import os
sys.path.append(os.getcwd())
from src.data.odds_api_client import OddsApiClient
from src.utils.normalization import NameNormalizer

def check():
    client = OddsApiClient()
    # Leicester is in Championship (E1)
    # We force days_ahead=2 to ensure we get it
    print("Fetching E1 Odds...")
    df = client.get_upcoming_odds('E1', days_ahead=2)
    
    if df.empty:
        print("No odds found for E1.")
        return

    # Filter for Leicester
    # Normalize 'Leicester' -> 'Leicester City' check
    # But usually user says 'Leicester'
    match = df[df['HomeTeam'].str.contains('Leicester') | df['AwayTeam'].str.contains('Leicester')]
    
    if match.empty:
        print("Leicester match not found in API response.")
        return
        
    row = match.iloc[0]
    print(f"Match: {row['HomeTeam']} vs {row['AwayTeam']}")
    print(f"B365 Over 1.5: {row.get('B365_Over1.5')}")
    print(f"B365 Over 2.5: {row.get('B365_Over2.5')}")
    print(f"B365 BTTS Yes: {row.get('B365_BTTS_Yes')}")

if __name__ == "__main__":
    check()
