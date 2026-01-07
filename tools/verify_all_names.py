import pandas as pd
import sys
import os

sys.path.append(os.getcwd())

from src.data.loader import DataLoader
from src.data.upcoming import FixturesFetcher
from src.utils.normalization import NameNormalizer

def verify_all():
    print("--- 🌍 GLOBAL NAME VERIFICATION (ALL LEAGUES) ---")
    
    leagues = ['E0', 'E1', 'SP1', 'SP2', 'D1', 'I1', 'F1', 'P1', 'N1']
    seasons = ['2425', '2324', '2223'] # Check recent history
    
    print("1. Loading History DB (The Source of Truth)...")
    loader = DataLoader() # Caches automatically
    history = loader.fetch_data(leagues, seasons)
    
    if history.empty:
        print("❌ CRITICAL: No History Data Loaded.")
        return

    # Normalize History
    history['HomeTeam'] = history['HomeTeam'].apply(NameNormalizer.normalize)
    history['AwayTeam'] = history['AwayTeam'].apply(NameNormalizer.normalize)
    
    # Create Set of Known Teams
    known_teams = set(history['HomeTeam'].unique()) | set(history['AwayTeam'].unique())
    print(f"✅ History Know {len(known_teams)} unique teams.")
    
    print("\n2. Fetching Upcoming Fixtures (Live/Scraped)...")
    fetcher = FixturesFetcher()
    upcoming = fetcher.fetch_upcoming(leagues)
    
    if upcoming.empty:
        print("❌ No Upcoming Matches found.")
        return
        
    print(f"✅ Found {len(upcoming)} upcoming matches.")
    
    print("\n3. Auditing Names...")
    mismatches = []
    
    for idx, row in upcoming.iterrows():
        # Raw from feed
        raw_home = row['HomeTeam']
        raw_away = row['AwayTeam']
        
        # Apply normalization (Simulating App logic)
        norm_home = NameNormalizer.normalize(raw_home)
        norm_away = NameNormalizer.normalize(raw_away)
        
        # Check against DB
        h_ok = norm_home in known_teams
        a_ok = norm_away in known_teams
        
        if not h_ok:
            mismatches.append(f"[{row['Div']}] {raw_home} -> {norm_home} (Not in DB)")
        if not a_ok:
            mismatches.append(f"[{row['Div']}] {raw_away} -> {norm_away} (Not in DB)")
            
    if mismatches:
        print(f"\n⚠️ FOUND {len(mismatches)} MISMATCHES:")
        # Dedup
        for m in sorted(list(set(mismatches))):
            print(f"  - {m}")
    else:
        print("\n🎉 SUCCESS: 100% of Upcoming Teams are Normalized & Found in History DB!")
        print("   The system is ROBUST.")

if __name__ == "__main__":
    verify_all()
