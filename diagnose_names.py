import pandas as pd
import sys
import os

sys.path.append(os.getcwd())
from src.data.loader import DataLoader

def diagnose():
    print("--- DIAGNOSING TEAM NAMES ---")
    loader = DataLoader()
    # Fetch E0 (Premier League) and SP1 (La Liga)
    df = loader.fetch_data(['E0', 'SP1'], ['2425'])
    
    print(f"Loaded {len(df)} rows.")
    
    e0_teams = sorted(df[df['Div'] == 'E0']['HomeTeam'].unique())
    print("\nPremier League (E0) Teams found in CSV:")
    for t in e0_teams:
        print(f"  '{t}'")
        
    sp1_teams = sorted(df[df['Div'] == 'SP1']['HomeTeam'].unique())
    print("\nLa Liga (SP1) Teams found in CSV:")
    for t in sp1_teams:
        print(f"  '{t}'")

if __name__ == "__main__":
    diagnose()
