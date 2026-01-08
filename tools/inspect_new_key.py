import requests
import json
import sys

# New Key provided by User
API_KEY = "5f34945e265a8fc0de7e377864ba8870e229ec45f0e6338e53998f6dcbba7a89"

def verify_new_key():
    print(f"🔑 Verifying Key: {API_KEY[:6]}... (V3 EVENTS Endpoint)")
    
    print(f"🔑 Verifying Key: {API_KEY[:6]}... (V3 EVENTS with LEAGUE param)")
    
    # Documentation says: sport="football" AND league="england-premier-league"
    # Let's try league="spain-laliga" (based on my codebase's slugs)
    league_slug = 'spain-laliga' 
    url = f"https://api2.odds-api.io/v3/events?apiKey={API_KEY}&sport=football&league={league_slug}"
    
    print(f"Requesting: {url}...")
    try:
        r = requests.get(url)  # No params dict, query string direct
        
        # Check Headers
        remaining = r.headers.get('x-requests-remaining', 'Unknown')
        used = r.headers.get('x-requests-used', 'Unknown')
        print(f"📊 Quota Status: Used={used}, Remaining={remaining}")
        
        if r.status_code == 200:
            print("✅ Status 200: OK")
            data = r.json()
            if not data:
                print("⚠️  Response Empty (No events?)")
                return

            print(f"found {len(data)} sports. Dumping to debug_sports.json")
            with open("data_cache/debug_sports.json", "w") as f:
                json.dump(data, f, indent=2)
        else:
            print(f"❌ Error {r.status_code}: {r.text}")

    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    verify_new_key()
