
import requests
import datetime

API_KEY = "e9be0a4fb2370fa9a2b574fccd726c50da0aae8acfd94a4b6c286a92b62345a2"
URL = "https://api2.odds-api.io/v3/events"

print(f"Checking API limit at {datetime.datetime.now()}")

try:
    response = requests.get(f"{URL}?apiKey={API_KEY}")
    
    print(f"Status Code: {response.status_code}")
    print("Headers relevant to limit:")
    for k, v in response.headers.items():
        if 'limit' in k.lower() or 'remaining' in k.lower() or 'reset' in k.lower():
            print(f"{k}: {v}")
            
    if response.status_code == 429:
        print(f"Body: {response.text}")
    elif response.status_code == 200:
        print("API is ALLOWING requests.")
    else:
        print(f"Unexpected status: {response.status_code}")

except Exception as e:
    print(f"Error: {e}")
