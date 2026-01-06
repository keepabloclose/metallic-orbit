
import requests
import json
import sys
import os

API_KEY = "e9be0a4fb2370fa9a2b574fccd726c50da0aae8acfd94a4b6c286a92b62345a2"
BASE_URL = "https://api.odds-api.io/v3"

def diagnose_markets():
    print("Fetching E0 Events...")
    url = f"{BASE_URL}/events?apiKey={API_KEY}&sport=football&league=england-premier-league"
    res = requests.get(url)  # <--- Restored
    if res.status_code != 200:
        print(f"Failed events: {res.status_code} {res.text}")
        return
        
    events = res.json()
    if isinstance(events, dict): events = events.get('data', [])
    
    if not events:
        print("No events.")
        return
        
    # Take first 3 events
    print(f"Found {len(events)} events. Inspecting first 3...")
    
    target_ids = [str(e['id']) for e in events[:3]]
    ids_str = ",".join(target_ids)
    
    # 2. Fetch Odds
    print("Fetching Odds (Bet365, 10Bet)...")
    o_url = f"{BASE_URL}/odds?apiKey={API_KEY}&eventId={ids_str}&bookmakers=bet365,10bet,unibet"
    o_res = requests.get(o_url)
    
    if o_res.status_code != 200:
        print(f"Odds failed: {o_res.text}")
        return
        
    data = o_res.json()
    if isinstance(data, dict): data = [data]
    
    for item in data:
        print(f"\nMatch: {item.get('home')} vs {item.get('away')}")
        bookmakers = item.get('bookmakers', {})
        
        for bk, markets in bookmakers.items():
            print(f"  Bookmaker: {bk}")
            # markets is a list of objects {name: '...', odds: ...}
            for m in markets:
                print(f"    - Market: '{m.get('name')}'")
                # Print first odd to see format
                odds = m.get('odds', [])
                if odds:
                    print(f"      Sample Odd: {odds[0]}")

if __name__ == "__main__":
    diagnose_markets()
