
import sys
import os
import pandas as pd

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)

from src.data.loader import DataLoader
from src.engine.predictor import Predictor

def debug_newcastle():
    print(">>> DEBUGGING NEWCASTLE DATA...", flush=True)
    loader = DataLoader()
    # Ensure we load 24/25
    df = loader.fetch_data(leagues=['E0', 'SP1'], seasons=['2425', '2324'])
    print(f"Data Loaded: {len(df)} rows. Columns: {df.columns.tolist()}", flush=True)
    
    # 1. Find Newcastle in HomeTeam
    # Fuzzy match 'Newc'
    newc_rows = df[df['HomeTeam'].astype(str).str.contains("Newc", case=False)]
    print(f"\n--- FUZZY SEARCH 'Newc' (HOME) ---")
    print(newc_rows[['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'HST', 'AST']].head(5).to_string())
    
    # 2. Check exact string list
    teams = df['HomeTeam'].unique()
    nc_teams = [t for t in teams if 'Newc' in str(t)]
    print(f"\nExact matches in Unique Teams: {nc_teams}")
    
    if not nc_teams:
        print("CRITICAL: Newcastle not found in HomeTeam list!")
        return

    target_team = nc_teams[0] 
    print(f"Targeting: '{target_team}'")
    
    # 3. Test Predictor Logic
    pred = Predictor(df)
    # Using 'Newcastle' (common name)
    print(f"\n--- PREDICTOR QUERY: 'Newcastle' ---")
    stats = pred.get_latest_stats('Newcastle')
    if stats is None:
        print("❌ get_latest_stats('Newcastle') returned None")
    else:
        print("✅ get_latest_stats('Newcastle') SUCCESSS!")
        print(stats)

    # 4. Test Predictor Query: 'Newcastle United'
    print(f"\n--- PREDICTOR QUERY: 'Newcastle United' ---")
    stats2 = pred.get_latest_stats('Newcastle United')
    if stats2 is None:
        print("❌ get_latest_stats('Newcastle United') returned None")
    else:
        print("✅ get_latest_stats('Newcastle United') SUCCESSS!")
        
    # 5. Check Away matches
    print(f"\n--- AWARD SEARCH ---")
    away_rows = df[df['AwayTeam'].astype(str).str.contains("Newc", case=False)]
    print(away_rows[['Date', 'HomeTeam', 'AwayTeam']].head(5).to_string())

if __name__ == "__main__":
    debug_newcastle()
