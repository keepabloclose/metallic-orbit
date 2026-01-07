import requests
import json

API_KEY = "e9be0a4fb2370fa9a2b574fccd726c50da0aae8acfd94a4b6c286a92b62345a2"
BASE_URL = "https://api.the-odds-api.com/v4"
SPORT = "soccer_epl"

def test_v4():
    print(f"Testing V4 API for {SPORT}...")
    url = f"{BASE_URL}/sports/{SPORT}/odds"
    params = {
        'apiKey': API_KEY,
        'regions': 'eu,uk', # Bet365 is usually EU/UK
        'markets': 'h2h,totals,alternate_totals,btts',
        'oddsFormat': 'decimal',
        'bookmakers': 'bet365'
    }
    
    try:
        res = requests.get(url, params=params)
        print(f"Status Code: {res.status_code}")
        
        if res.status_code == 200:
            data = res.json()
            print(f"Received {len(data)} matches.")
            if data:
                print("First Match Bookmakers:")
                item = data[0]
                print(f"Match: {item.get('home_team')} vs {item.get('away_team')}")
                bookmakers = item.get('bookmakers', [])
                for b in bookmakers:
                    print(f"  - {b['title']}")
                    for m in b.get('markets', []):
                        print(f"    - Market: {m['key']} (Outcome count: {len(m['outcomes'])})")
                        if m['key'] == 'alternate_totals':
                            print(f"      -> Found Alternate Totals! Sample: {m['outcomes'][:3]}")
            return True
        else:
            print(f"Error: {res.text}")
            return False
            
    except Exception as e:
        print(f"Exception: {e}")
        return False

if __name__ == "__main__":
    test_v4()
