
import requests
import json

API_KEY = "e9be0a4fb2370fa9a2b574fccd726c50da0aae8acfd94a4b6c286a92b62345a2"
BASE_URL = "https://api.odds-api.io/v3"

def list_leagues():
    print("Fetching Leagues...")
    url = f"{BASE_URL}/leagues?apiKey={API_KEY}&sport=football"
    res = requests.get(url)
    if res.status_code == 200:
        leagues = res.json()
        print(f"Found {len(leagues)} leagues.")
        
        # Filter for England/Spain
        print("\n--- England ---")
        for l in leagues:
            name = l.get('name', '').lower()
            if 'england' in name:
                print(f"{l.get('name')}: {l.get('slug')}")
                
        print("\n--- Spain ---")
        for l in leagues:
            name = l.get('name', '').lower()
            if 'spain' in name:
                print(f"{l.get('name')}: {l.get('slug')}")
                
    else:
        print(f"Error: {res.text}")

if __name__ == "__main__":
    list_leagues()
