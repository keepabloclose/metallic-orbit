
import pandas as pd
import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.data.loader import DataLoader
from src.engine.features import FeatureEngineer

def diagnose_columns():
    print("=== Diagnosing Column Explosion ===")
    
    # 1. Load Data (Minimal Test)
    leagues = ['SP1']
    seasons = ['2425']
    
    loader = DataLoader()
    print("Fetching data...")
    df = loader.fetch_data(leagues, seasons)
    print(f"Initial Shape: {df.shape}")
    
    # 2. Add Rest Days
    fe = FeatureEngineer(df)
    try:
        fe.add_rest_days()
        print(f"After Rest Days: {fe.df.shape}")
    except Exception as e:
        print(f"Rest Days Failed: {e}")
        
    # 3. Add Rolling Stats
    try:
        fe.add_rolling_stats(window=5)
        print(f"After Rolling Stats: {fe.df.shape}")
    except Exception as e:
        print(f"Rolling Stats Failed: {e}")
        
    # 4. Add Recent Form
    try:
        fe.add_recent_form(window=5)
        print(f"After Recent Form: {fe.df.shape}")
    except Exception as e:
        print(f"Recent Form Failed: {e}")
        
    # 5. Add Opponent Difficulty
    try:
        fe.add_opponent_difficulty(window=5)
        print(f"After Opp Difficulty: {fe.df.shape}")
    except Exception as e:
        print(f"Opp Difficulty Failed: {e}")
        
    # 6. Add Relative Strength
    try:
        fe.add_relative_strength()
        print(f"After Relative Strength: {fe.df.shape}")
    except Exception as e:
        print(f"Relative Strength Failed: {e}")
        
    # Check for excessive columns
    print("\nSample Columns:")
    print(list(fe.df.columns)[:20])
    
    if fe.df.shape[1] > 1000:
        print("\n!!! HIGH COLUMN COUNT DETECTED !!!")
        print("Last 20 Columns:")
        print(list(fe.df.columns)[-20:])

if __name__ == "__main__":
    diagnose_columns()
