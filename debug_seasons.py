
import requests

seasons = ['2425', '2526']
leagues = ['SP1', 'E0']
base_url = "https://www.football-data.co.uk/mmz4281"

print("Checking Season Data Availability...")
headers = {'User-Agent': 'Mozilla/5.0'}

for s in seasons:
    for l in leagues:
        url = f"{base_url}/{s}/{l}.csv"
        try:
            r = requests.head(url, headers=headers)
            print(f"[{r.status_code}] {url}")
        except Exception as e:
            print(f"[ERR] {url}: {e}")
