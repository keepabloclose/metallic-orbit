
import sys
import os
import requests
from datetime import datetime
import json

# Direct API check
API_KEY = "e9be0a4fb2370fa9a2b574fccd726c50da0aae8acfd94a4b6c286a92b62345a2"
slug = "england-championship"
url = f"https://api2.odds-api.io/v3/events?apiKey={API_KEY}&sport=football&league={slug}"

print(f"Fetching {url}")
res = requests.get(url)
try:
    data = res.json()
    print(f"Response Type: {type(data)}")
    
    events = []
    if isinstance(data, list):
        events = data
    elif isinstance(data, dict):
        events = data.get('data', [])
        
    print(f"Found {len(events)} events.")
    now = datetime.utcnow()
    print(f"Current UTC: {now}")

    for e in events[:5]:
        start = e.get('commence_time') or e.get('commence')
        print(f"Event: {start} | {e.get('home_team')} vs {e.get('away_team')}")

    # Check Leicester specifically
    # Handle string rep for robustness
    leicester = [e for e in events if 'Leicester' in str(e)]
    print("\nLeicester Matches:")
    for e in leicester:
        start = e.get('commence_time') or e.get('commence')
        print(f"  {start} | {e.get('home_team')} vs {e.get('away_team')}")
        
except Exception as e:
    print(f"Error parsing JSON: {e}")
    print(res.text[:500])
