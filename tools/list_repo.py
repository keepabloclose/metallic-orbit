
import requests
import json

def get_contents(path="logos"):
    url = f"https://api.github.com/repos/luukhopman/football-logos/contents/{path}"
    print(f"📂 Fetching: {url}")
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            # print names
            for item in data:
                if item['type'] == 'dir':
                    print(f"📁 DIR: {item['name']}")
                else:
                    print(f"📄 FILE: {item['name']}")
                    
            return data
        else:
            print(f"❌ {r.status_code}: {r.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


print("--- FETCHING LEAGUE CONTENTS ---")
leagues = [
    "Italy - Serie A",
]

for l in leagues:
    print(f"\n📁 Listing: {l}")
    get_contents(f"logos/{l}")
