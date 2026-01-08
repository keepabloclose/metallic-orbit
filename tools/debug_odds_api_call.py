
import requests
import json

API_KEY = "e9be0a4fb2370fa9a2b574fccd726c50da0aae8acfd94a4b6c286a92b62345a2"
BASE_URL = "https://api2.odds-api.io/v3"
# Taking a common slug
SLUG = "spain-laliga"

def test_fetch(markets=None):
    url = f"{BASE_URL}/odds?apiKey={API_KEY}&sport=football&league={SLUG}&bookmakers=Bet365"
    if markets:
        url += f"&markets={markets}"
        
    print(f"Fetching: {url}")
    try:
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            # print(json.dumps(data, indent=2))
            
            # INSPECT FIRST EVENT
            if isinstance(data, list) and len(data) > 0:
                ev = data[0]
                print(f"\nEvent: {ev.get('home_team')} vs {ev.get('away_team')}")
                bookies = ev.get('bookmakers', {})
                
                # Find Bet365
                b365 = None
                for k, v in bookies.items():
                   if 'bet365' in k.lower():
                       b365 = v
                       break
                
                if b365:
                    print(f"Bet365 Markets Found: {len(b365)}")
                    for m in b365:
                        print(f" - Key: {m.get('key')} | Name: {m.get('name')}")
                else:
                    print("No Bet365 found.")
            else:
                 print("No events found or different structure.")
        else:
            print(f"Error: {res.status_code} {res.text}")
    except Exception as e:
        print(f"Exception: {e}")

print("--- TEST 1: Default (No markets param) ---")
test_fetch()

print("\n--- TEST 2: Valid Markets Param (h2h,totals,btts) ---")
# "h2h,totals,btts" might be V4. V3 might be "h2h,totals"? Let's try known ones.
# Actually, if this is truly V3, usually it returns all. If it's V4 wrapped in V3 URL...
# Let's try the key used in code: 'h2h,totals,btts`
test_fetch("h2h,totals,btts")
