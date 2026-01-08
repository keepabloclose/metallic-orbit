import sys
import os
import time

# Ensure src path is in sys.path
sys.path.append(os.getcwd())

from src.data.odds_api_client import OddsApiClient

def verify_rotation():
    client = OddsApiClient()
    print("🧪 Testing OddsApiClient Rotation & Fetch")
    
    # Check if keys are loaded
    print(f"   Current Key Index: {client.current_key_index}")
    
    display_cols = ['HomeTeam', 'AwayTeam', 'B365H', 'B365_Over1.5', 'B365_BTTS_Yes']
    
    # Try fetching odds for ALL Leagues
    leagues = ['E0', 'E1', 'SP1', 'SP2', 'D1', 'I1', 'F1', 'P1', 'N1']
    
    for l in leagues:
        print(f"\nREQUEST: Fetching {l} Odds...")
        # Clean cache hack or use force_refresh
        df = client.get_upcoming_odds(l, days_ahead=7, force_refresh=True)
        
        if not df.empty:
            print(f"✅ Success {l}! Fetched {len(df)} records.")
            # Only show cols that exist
            valid_cols = [c for c in display_cols if c in df.columns]
            print(df[valid_cols].head(3))
        else:
            print(f"❌ Failed to fetch {l} (DF Empty).")

    # Manually check rotation state
    print(f"\n🔑 Key Index after request: {client.current_key_index}")
    
if __name__ == "__main__":
    verify_rotation()
