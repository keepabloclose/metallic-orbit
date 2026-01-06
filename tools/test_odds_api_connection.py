
import requests
import json
import pandas as pd

API_KEY = "e9be0a4fb2370fa9a2b574fccd726c50da0aae8acfd94a4b6c286a92b62345a2"

# Check https://docs.odds-api.io
# Endpoint might be /v3/leagues (no trailing slash) or different domain.
# User doc link: https://docs.odds-api.io/api-reference/introduction
# Let's try matching the exact docs: https://api.odds-api.io/v3/leagues

BASE_URL = "https://api.odds-api.io/v3" 

def test_connection():
    print("Testing Odds-API Connection (V2)...")
    
    # 1. Get Leagues
    print("1. Fetching Leagues...")
    try:
        url = f"{BASE_URL}/leagues?apiKey={API_KEY}&sport=football" # Added sport
        res = requests.get(url)

        if res.status_code == 200:
            json_response = res.json()
            print(f"   Raw Response Type: {type(json_response)}")
            if isinstance(json_response, list):
                leagues = json_response
            else:
                leagues = json_response.get('data', [])
                
            print(f"   Success! Found {len(leagues)} leagues.")
            if len(leagues) > 0:
                print(f"   Sample: {leagues[0]}")
            
            # Search for our target leagues
            targets = ['Premier League', 'La Liga', 'Bundesliga', 'Serie A']
            for l in leagues:
                # API might return just slugs as strings? Or dicts?
                name = l.get('name', 'Unknown') if isinstance(l, dict) else str(l)
                if any(t in name for t in targets):
                    print(f"   - {name}: {l.get('slug', l)}")  
                    
            # Set target slug dynamically
            target_slug = 'england-premier-league' # Default fallback
        else:
            print(f"   Failed to fetch leagues: {res.status_code} - {res.text}")
            return
    except Exception as e:
        print(f"   Error: {e}")
        return

    # 2. Get Events for a League (e.g. EPL)
    print("\n2. Fetching Premier League Events...")
    try:
        # Assuming slug 'football-england-premier-league' based on typical pattern, 
        # but will verify from step 1 output. Let's guess 'soccer_epl' or similar based on docs
        # The docs said 'sport=soccer_epl' for the-odds-api.com, but this is 'odds-api.io'.
        # Let's try to search specifically for 'England'
        # For now, let's use a broad search if possible or just try 'england-premier-league'
        
        target_slug = 'football-england-premier-league' # Best guess
        
        url = f"{BASE_URL}/events"
        params = {
            'apiKey': API_KEY,
            'sport': 'football', # or soccer?
            'league': target_slug
        }
        res = requests.get(url, params=params)
        
        # If 404/400, strictly rely on step 1 output next time. 
        # But for this test, let's just inspect the response.
        print(f"   Response Code: {res.status_code}")
        if res.status_code == 200:
            data = res.json()['data']
            print(f"   Found {len(data)} events.")
            if data:
                print(f"   Example: {data[0]['home_team']} vs {data[0]['away_team']}")
                # Get Odds for this event
                event_id = data[0]['id']
                print(f"\n3. Fetching Odds for Event {event_id}...")
                odds_url = f"{BASE_URL}/odds?apiKey={API_KEY}&eventId={event_id}"
                odds_res = requests.get(odds_url)
                if odds_res.status_code == 200:
                    odds = odds_res.json()['data']
                    print(f"   Odds Data Found: {json.dumps(odds)[:200]}...")
                else:
                    print(f"   Failed odds: {odds_res.text}")
        else:
            print(f"   Failed to fetch events: {res.text}")

    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_connection()
