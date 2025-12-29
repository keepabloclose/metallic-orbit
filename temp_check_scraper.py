import requests
from bs4 import BeautifulSoup

url = "https://www.betexplorer.com/next/soccer/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

try:
    print(f"Fetching {url}...")
    r = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'html.parser')
        # Look for match rows
        matches = soup.find_all('tr')
        print(f"Found {len(matches)} rows.")
        
        found_odds = False
        for i, row in enumerate(matches[:20]):
            text = row.get_text(strip=True)
            print(f"Row {i}: {text[:100]}...")
            if any(x in text for x in ['.', ',']): # simple check for numbers
                found_odds = True
        
        if found_odds:
            print("SUCCESS: Odds appearing in text.")
        else:
            print("WARNING: HTML might be empty/JS-rendered.")
            
except Exception as e:
    print(f"Error: {e}")
