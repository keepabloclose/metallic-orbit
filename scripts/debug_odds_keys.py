
import sys
import os
import requests
import json

# Direct API check
API_KEY = "e9be0a4fb2370fa9a2b574fccd726c50da0aae8acfd94a4b6c286a92b62345a2"
slug = "england-championship"
url = f"https://api2.odds-api.io/v3/events?apiKey={API_KEY}&sport=football&league={slug}"

print(f"Fetching {url}")
res = requests.get(url)
try:
    data = res.json()
    events = data.get('data', []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    
    print(f"Found {len(events)} events.")
    
    if events:
        print("Keys of first event:")
        print(events[0].keys())
        print("Sample Event:")
        print(json.dumps(events[0], indent=2)[:500]) # First 500 chars

except Exception as e:
    print(f"Error: {e}")
