import requests

urls = [
    "https://www.football-data.co.uk/fixtures.csv",
    "https://www.football-data.co.uk/mmz4281/2526/Fixtures.csv",
    "https://www.football-data.co.uk/mmz4281/2425/Fixtures.csv"
]
headers = {"User-Agent": "Mozilla/5.0"}

for u in urls:
    try:
        r = requests.head(u, headers=headers)
        print(f"{u}: {r.status_code}")
    except Exception as e:
        print(f"{u}: Error {e}")
