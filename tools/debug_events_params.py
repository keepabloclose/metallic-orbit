
import requests
import json

API_KEY = "e9be0a4fb2370fa9a2b574fccd726c50da0aae8acfd94a4b6c286a92b62345a2"
BASE_URL = "https://api.odds-api.io/v3"

def debug_events():
    slug = "england-premier-league"
    print(f"Testing Events for {slug}...")
    
    # Variation 1: Standard (failed before)
    print("\n1. Standard (status=pre):")
    url = f"{BASE_URL}/events?apiKey={API_KEY}&sport=football&league={slug}&status=pre"
    r1 = requests.get(url)
    print(f"Status: {r1.status_code}, Count: {len(r1.json()) if isinstance(r1.json(), list) else 0}")
    
    # Variation 2: No Status
    print("\n2. No status param:")
    url = f"{BASE_URL}/events?apiKey={API_KEY}&sport=football&league={slug}"
    r2 = requests.get(url)
    print(f"Status: {r2.status_code}, Count: {len(r2.json()) if isinstance(r2.json(), list) else 0}")

    # Variation 3: Status = upcoming?
    print("\n3. Status = upcoming:")
    url = f"{BASE_URL}/events?apiKey={API_KEY}&sport=football&league={slug}&status=upcoming"
    r3 = requests.get(url)
    print(f"Status: {r3.status_code}, Count: {len(r3.json()) if isinstance(r3.json(), list) else 0}")

if __name__ == "__main__":
    debug_events()
