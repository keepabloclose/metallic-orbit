
import requests
import json

API_KEY = "e9be0a4fb2370fa9a2b574fccd726c50da0aae8acfd94a4b6c286a92b62345a2"
BASE_URL = "https://api2.odds-api.io/v3/events"
ODDS_URL = "https://api2.odds-api.io/v3/odds/multi"

# 1. Fetch one event ID from La Liga
events_url = f"{BASE_URL}?apiKey={API_KEY}&sport=football&league=spain-laliga"
print(f"Fetching events from {events_url}...")
res = requests.get(events_url)
json_data = res.json()
events = json_data.get('data', []) if isinstance(json_data, dict) else json_data

if not events:
    print("No events found.")
    exit()

import datetime

# Filter for non-settled events (Scheduled or Live)
active_events = [e for e in events if e.get('status') != 'settled']

if not active_events:
    print("No active (scheduled/live) events found.")
    # Try filtering by date manually just in case status is unreliable
    active_events = [e for e in events if e.get('commence_time') and e.get('commence_time') > datetime.datetime.utcnow().isoformat()]

if not active_events:
    print("No active events found by date either. Exiting.")
    exit()
    
print(f"Found {len(active_events)} active events.")
# Fetch for first 5 active events
batch_ids = [str(e['id']) for e in active_events[:5]]
eid_str = ",".join(batch_ids)

print(f"Fetching odds for batch of {len(batch_ids)} IDs...")
odds_url = f"{ODDS_URL}?apiKey={API_KEY}&eventIds={eid_str}&bookmakers=Bet365&markets=h2h,totals,alternate_totals,btts,team_totals,alternate_team_totals"

odds_res = requests.get(odds_url)

if odds_res.status_code == 200:
    data = odds_res.json()
    found_good = False
    
    for item in data:
        bookies = item.get('bookmakers', {})
        b365 = None
        for k, v in bookies.items():
            if 'bet365' in k.lower():
                b365 = v
                break
        
        if b365: # List is not empty
            print(f"\n--- FOUND RICH ODDS for ID {item['id']} ({item['home']} vs {item['away']}) ---")
            # Print specifically the keys inside Bet365 to see markets
            print("Bet365 Markets found:")
            for m in b365:
                print(f" - Key: {m.get('key')} | Outcomes: {len(m.get('outcomes', []))}")
            
            # Print One Market fully
            print(json.dumps(b365, indent=2))
            found_good = True
            break
            
    if not found_good:
        print("Fetched odds but Bet365 was empty/missing for all 20 events.")

else:
    print(f"Error fetching odds: {odds_res.status_code} {odds_res.text}")

