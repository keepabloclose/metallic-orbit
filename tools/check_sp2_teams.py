
import sys
import os
import pandas as pd
import requests
import io
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# URLs for SP2
URL_2425 = "https://www.football-data.co.uk/mmz4281/2425/SP2.csv"
URL_2526 = "https://www.football-data.co.uk/mmz4281/2526/SP2.csv"

def get_teams(url):
    print(f"Checking {url}...")
    try:
        r = requests.get(url, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
        if r.status_code == 200:
            df = pd.read_csv(io.StringIO(r.content.decode('latin-1')))
            teams = set(df['HomeTeam'].dropna().unique()) | set(df['AwayTeam'].dropna().unique())
            return sorted(list(teams))
        else:
            print(f"Failed to fetch {url}: {r.status_code}")
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []

def check_teams():
    teams_2425 = get_teams(URL_2425)
    teams_2526 = get_teams(URL_2526)
    
    all_teams = sorted(list(set(teams_2425 + teams_2526)))
    
    print("\n=== Teams found in SP2 (24/25 & 25/26) ===")
    for t in all_teams:
        print(f" - {t}")
        
    print("\n=== Checking Target Teams ===")
    targets = ['Cultural Leonesa', 'Sociedad B', 'Andorra', 'Ceuta', 'Deportivo', 'Castellon']
    
    for t in targets:
        # Simple fuzzy check
        curr = "MISSING"
        for avail in all_teams:
            if t.lower() in avail.lower() or avail.lower() in t.lower():
                curr = f"FOUND as '{avail}'"
                break
        print(f"Target '{t}': {curr}")

if __name__ == "__main__":
    check_teams()
