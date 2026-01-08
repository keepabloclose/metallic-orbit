import requests
import json

API_KEY = "5f34945e265a8fc0de7e377864ba8870e229ec45f0e6338e53998f6dcbba7a89"
BASE_URL = "https://api.the-odds-api.com/v3"

# ... inside verify function ...
    try:
        # Standard V3 Endpoint per docs
        # Note: v4 is vastly superior, but client uses v3 logic. let's check v3 first.
        # But wait, to get alternate totals (+1.5 etc), we usually need V4.
        # Let's try V4 first with the new key.
        url_matches = f"https://api.the-odds-api.com/v4/sports/soccer_spain_la_liga/odds?apiKey={API_KEY}&regions=eu&markets=h2h,totals,btts,alternate_totals&oddsFormat=decimal"
        print(f"Trying Standard V4 API with NEW KEY: {url_matches}")
# Client code used: https://api2.odds-api.io/v3
# But standard The Odds API is api.the-odds-api.com
# Let's assume the code in the project is correct for the user's subscription.

# 1. Fetch Fixtures to get an Event ID
print("Fetching fixtures...")
url_fixtures = f"https://api.the-odds-api.com/v4/sports/soccer_spain_la_liga/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals,btts&oddsFormat=decimal"
# WAIT, the code in OddsApiClient uses `api2.odds-api.io`? 
# Let's check the file content I saw earlier.
# Line 10: API_KEY = "e9be..."
# Line 11: BASE_URL = "https://api2.odds-api.io/v3"
# This looks like a specific/custom endpoint or I misremembered the standard one.
# Let's try to trace exactly what the current `odds_api_client.py` does.

# RE-READing the code from previous turns:
# url = f"{self.BASE_URL}/odds/multi?apiKey={self.API_KEY}&eventIds={batch_str}&bookmakers=Bet365&markets=h2h,totals,btts"

# I will replicate THAT exact logic but print raw output.

import sys
import os
sys.path.append(os.getcwd())
from src.data.odds_api_client import OddsApiClient

def inspect_raw():
    client = OddsApiClient()
    # We need a valid LEAGUE to fetch.
    league_slug = 'spain-laliga' 
    
    # The client usually does: 
    # 1. Fetch fixtures (internally?) or it takes event IDs.
    # The `get_upcoming_odds` method seems to call `upcoming` endpoint first?
    # Let's just use the `get_upcoming_odds` method but insert a print in the class? 
    # Or better, replicate the requests here.
    
    # 1. Get Events (Matches)
    # Endpoints might vary. Let's try standard V4 structure first if the V3 failed? 
    # No, stick to what's in the client.
    
    # It seems the client is using a specific provider.
    # Let's Try to fetch 'upcoming' matches first.
    # url = f"{client.BASE_URL}/upcoming/matches?apiKey={client.API_KEY}&sport={league_slug}&days=2"
    # Actually, let's reverse engineer the `get_upcoming_odds` method from the file view.
    
    # It fetches matches, then batches them for odds.
    # Let's force it to run and print the raw response from the `odds/multi` call.
    
    # I will monkey-patch the request mechanism or just copy the URL construction.
    
    # Step 1: Get Matches
    url_matches = f"{client.BASE_URL}/upcoming/matches?apiKey={client.API_KEY}&sport={league_slug}&days=7"
    print(f"Requesting Matches: {url_matches}")
    try:
        # Try api.odds-api.io (removed 2)
        url_matches = f"https://api.odds-api.io/v3/events?apiKey={client.API_KEY}&sport=football&league={league_slug}"
        print(f"Trying api.odds-api.io (No '2'): {url_matches}")
        r = requests.get(url_matches)
        try:
            matches = r.json() # This usually returns {'data': [...]} or list
        except Exception:
            print(f"FAILED TO PARSE JSON. RAW TEXT: {r.text[:500]}")
            return

        if not matches or 'data' not in matches:
            print(f"Failed to get matches: {matches}")
            # Try alternate URL standard
            url_matches = f"https://api.the-odds-api.com/v4/sports/soccer_spain_la_liga/odds?apiKey={client.API_KEY}&regions=eu&markets=h2h,totals,btts"
            print(f"Trying Standard API: {url_matches}")
            r = requests.get(url_matches)
            print(r.text[:500])
            return
            
        print(f"Found {len(matches.get('data', []))} matches.")
        if len(matches['data']) == 0: return

        first_match = matches['data'][0]
        event_id = first_match['id']
        print(f"Inspecting Event: {first_match['homeTeam']} vs {first_match['awayTeam']} (ID: {event_id})")
        
        # Step 2: Get Odds
        # Add 'alternate_totals' to see if it helps
        markets = "h2h,totals,btts,alternate_totals" 
        url_odds = f"{client.BASE_URL}/odds/multi?apiKey={client.API_KEY}&eventIds={event_id}&bookmakers=Bet365&markets={markets}"
        print(f"Requesting Odds: {url_odds}")
        
        r_odds = requests.get(url_odds)
        data = r_odds.json()
        
        print("\n--- RAW ODDS RESPONSE ---")
        print(json.dumps(data, indent=2))
        print("-------------------------")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_raw()
