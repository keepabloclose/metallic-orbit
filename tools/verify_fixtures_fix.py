
import sys
import os
import pandas as pd

# Add root to path
sys.path.append(os.getcwd())

from src.data.upcoming import FixturesFetcher
# from src.dashboard.app import fetch_upcoming_cached # Removed to avoid side effects
from src.engine.features import FeatureEngineer

def verify():
    print("Initialize Fetcher...")
    fetcher = FixturesFetcher()
    
    print("Fetching upcoming for ['SP2', 'I1']...")
    df = fetcher.fetch_upcoming(leagues=['SP2', 'I1'])
    
    print(f"Initial Fetch Count: {len(df)}")
    if 'Date' in df.columns:
        print(df[['Date', 'Div', 'HomeTeam', 'AwayTeam']].head())
    
    # Test SP2 Count
    sp2 = df[df['Div'] == 'SP2']
    print(f"\nSP2 Count (Raw): {len(sp2)}")
    
    # Test Feature Engineering (Explosion Check)
    print("\nApplying Feature Engineering...")
    engineer = FeatureEngineer(df)
    enriched_df = engineer.add_rest_days()
    enriched_df = engineer.add_rolling_stats()
    
    sp2_enriched = enriched_df[enriched_df['Div'] == 'SP2']
    print(f"SP2 Count (Enriched): {len(sp2_enriched)}")
    
    if len(sp2_enriched) > 50:
        print("❌ FAILURE: Explosion detected! Count > 50")
        sys.exit(1)
    
    if len(sp2_enriched) < 5:
        print("❌ FAILURE: Too few matches! Count < 5")
        sys.exit(1)
        
    # Check Duplicates
    if sp2_enriched.duplicated(subset=['HomeTeam', 'AwayTeam']).any():
        print("❌ FAILURE: Duplicates found in Enriched DF!")
        print(sp2_enriched[sp2_enriched.duplicated(subset=['HomeTeam', 'AwayTeam'], keep=False)][['HomeTeam', 'AwayTeam']])
        sys.exit(1)
        
    print("✅ SUCCESS: SP2 count valid and no duplicates.")

if __name__ == "__main__":
    verify()
