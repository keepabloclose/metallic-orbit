import sys
import os
import pandas as pd

# Add root to path so 'src' module can be found
sys.path.append(os.getcwd())

from src.engine.ml_engine import MLEngine
from src.data.loader import DataLoader

def run_experiment():
    print("--- Starting Model Experiment: Rest Days Impact ---")
    
    # 1. Load Data
    print("Loading historical data via DataLoader...")
    loader = DataLoader()
    # Use standard leagues/seasons
    leagues = ['E0', 'E1', 'SP1', 'SP2', 'D1', 'I1', 'F1']
    seasons = ['2425', '2324', '2223', '2122']
    
    df = loader.fetch_data(leagues, seasons)
    
    if df.empty:
        print("Error: No data loaded.")
        return

    print(f"Loaded {len(df)} matches.")
    
    # Filter for finished games (FTR exists)
    history = df[df['FTR'].notna()].copy()
    print(f"Training on {len(history)} historical matches.")
    
    # Ensure Date is datetime
    if 'Date' in history.columns:
        history['Date'] = pd.to_datetime(history['Date'], dayfirst=True, errors='coerce')
        history = history.dropna(subset=['Date'])
        
    # --- FEATURE ENGINEERING ---
    from src.engine.features import FeatureEngineer
    print("Calculating Features (RestDays, etc)...")
    engineer = FeatureEngineer(history)
    history = engineer.add_rest_days() 
    history = engineer.add_rolling_stats(window=5)
    history = engineer.add_recent_form(window=5)
    history = engineer.add_opponent_difficulty(window=5)
    history = engineer.add_relative_strength()
    
    # 2. Normalize Names (Critical for merge)
    from src.utils.normalization import NameNormalizer
    history['HomeTeam'] = history['HomeTeam'].apply(NameNormalizer.normalize)
    history['AwayTeam'] = history['AwayTeam'].apply(NameNormalizer.normalize)
    
    # --- SCENARIO A: WITH REST DAYS (Baseline) ---
    print("\n[A] Training Baseline Model (WITH Rest Days)...")
    engine_a = MLEngine()
    scores_a = engine_a.train_models(history)
    print("Baseline Scores:", scores_a)
    
    # --- SCENARIO B: WITHOUT REST DAYS ---
    print("\n[B] Training Experimental Model (WITHOUT Rest Days)...")
    engine_b = MLEngine()
    
    # Remove RestDays columns
    cols = [c for c in engine_b.feature_cols if 'RestDays' not in c]
    engine_b.feature_cols = cols
    print(f"Modified Feature Cols: {len(engine_b.feature_cols)} features (removed RestDays)")
    
    scores_b = engine_b.train_models(history)
    print("Experimental Scores:", scores_b)
    
    # --- COMPARISON ---
    print("\n--- RESULTS ---")
    print(f"{'Target':<15} | {'Baseline':<10} | {'No RestDays':<10} | {'Diff':<10}")
    print("-" * 55)
    
    targets = scores_a.keys()
    for t in targets:
        s_a = scores_a.get(t, 0)
        s_b = scores_b.get(t, 0)
        diff = s_b - s_a
        print(f"{t:<15} | {s_a:.4f}     | {s_b:.4f}      | {diff:+.4f}")
        
    print("\nConclusion: Positive Diff means removing RestDays IMPROVED the model.")

if __name__ == "__main__":
    run_experiment()

