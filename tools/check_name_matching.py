
import json
import os
import pandas as pd
import sys

# Mocking the load to avoid importing src which triggers init
def load_events(league_code):
    path = f"data_cache/odds_api/events_{league_code}.json"
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    print(f"No cache for {league_code}")
    return []

def check_names():
    print("=== Name Matching Check ===")
    
    # 1. Load API Events for E0
    events = load_events('E0')
    if not events: return
    
    api_teams = set()
    for e in events:
        api_teams.add(e['home']) # or 'home_team' depending on saved structure
        api_teams.add(e['away'])
        
    print(f"API Teams (E0, {len(api_teams)}):")
    print(sorted(list(api_teams)))

    # 2. Load Local Fixtures (from FixturesFetcher mock or real if possible)
    # We will simulate the common names or try to run FixturesFetcher
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    try:
        from src.data.upcoming import FixturesFetcher
        fetcher = FixturesFetcher()
        # Ensure we don't trigger API call in fetcher, just CSV
        # fetcher uses existing CSVs or mock
        # We want to see what names strictly from the CSV/Data source
        
        # Hardcoding known problem names for quick check if full fetch is hard
        csv_fixtures = {
            'Manchester United', 'Man City', 'Wolves', 'Nottm Forest', 'Sheffield Utd'
        }
        print("\nChecking specific problem areas:")
        for problem in csv_fixtures:
            match = "❌"
            if problem in api_teams: match = "✅ Exact"
            print(f"{problem}: {match}")
            
    except Exception as e:
        print(f"Error loading fixtures: {e}")

if __name__ == "__main__":
    check_names()
