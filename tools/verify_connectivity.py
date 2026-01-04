
import requests

def check_conn():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    tests = [
        "https://www.football-data.co.uk/mmz4281/2324/E0.csv", # Previous season (Should exist)
        "https://www.football-data.co.uk/mmz4281/2425/E0.csv", # Current season PL
        "https://www.football-data.co.uk/mmz4281/2425/SP2.csv", # Current season SP2
    ]
    
    for url in tests:
        print(f"Testing {url}...")
        try:
            r = requests.head(url, headers=headers, verify=False, timeout=5)
            print(f"Status: {r.status_code}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_conn()
