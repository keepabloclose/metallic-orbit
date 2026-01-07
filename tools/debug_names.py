import pandas as pd
import sys
import os

sys.path.append(os.getcwd())

from src.data.loader import DataLoader
from src.data.upcoming import FixturesFetcher
from src.utils.normalization import NameNormalizer

def debug_names():
    print("--- Debugging Team Name Normalization ---")
    
    # 1. Load History (The Source of Truth for Stats)
    print("Loading History...")
    loader = DataLoader() # Caches automatically
    history = loader.fetch_data(['E0', 'SP1', 'SP2', 'E1'], ['2425']) # Check 4 major leagues
    
    if history.empty:
        print("CRITICAL: No History Loaded")
        return

    # Normalize History Names (Simulating what app.py does)
    history['HomeTeam'] = history['HomeTeam'].apply(NameNormalizer.normalize)
    history['AwayTeam'] = history['AwayTeam'].apply(NameNormalizer.normalize)
    
    known_teams = set(history['HomeTeam'].unique()) | set(history['AwayTeam'].unique())
    print(f"Loaded {len(known_teams)} unique teams from History.")
    # print("Sample Spanish Teams:", [t for t in known_teams if 'Es' in t or 'Gir' in t or 'Bar' in t])
    
    # 2. Fetch Upcoming (The Target to Match)
    print("Fetching Upcoming Fixtures...")
    fetcher = FixturesFetcher()
    upcoming = fetcher.fetch_upcoming(['E0', 'SP1'])
    
    if upcoming.empty:
        print("CRITICAL: No Upcoming Matches found.")
        return
        
    print(f"Found {len(upcoming)} upcoming matches.")
    
    # 3. Check Matches
    mismatches = []
    
    print("\n[Checking Matchup Validation]")
    for idx, row in upcoming.iterrows():
        # Upcoming names might need normalization too!
        # App.py logic:
        # h_norm = predictor.normalize_name(m_row['HomeTeam'])
        
        raw_home = row['HomeTeam']
        raw_away = row['AwayTeam']
        
        norm_home = NameNormalizer.normalize(raw_home)
        norm_away = NameNormalizer.normalize(raw_away)
        
        h_found = norm_home in known_teams
        a_found = norm_away in known_teams
        
        status = "✅" if (h_found and a_found) else "❌"
        
        if not (h_found and a_found):
            mismatches.append((raw_home, norm_home, h_found, raw_away, norm_away, a_found))
            print(f"{status} {raw_home} (-> {norm_home}) vs {raw_away} (-> {norm_away})")
            if not h_found: print(f"    ⚠️ Home Team '{norm_home}' NOT found in History DB")
            if not a_found: print(f"    ⚠️ Away Team '{norm_away}' NOT found in History DB")
            
    if not mismatches:
        print("\n🎉 ALL Names Match! The issue is likely elsewhere (Logic/Thresholds).")
    else:
        print(f"\nFound {len(mismatches)} name mismatches. This prevents stats loading.")

if __name__ == "__main__":
    debug_names()
