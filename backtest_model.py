
import pandas as pd
import numpy as np
import sys
import os
from sklearn.metrics import accuracy_score, mean_absolute_error

# Add root to path
sys.path.append(os.getcwd())

from src.data.loader import DataLoader
from src.engine.features import FeatureEngineer
from src.engine.ml_engine import MLEngine

def run_backtest():
    print("--- 1. LOADING DATA FOR BACKTEST ---")
    loader = DataLoader() 
    # Load enough history for training + testing
    leagues = ['SP1', 'E0', 'E1', 'D1', 'I1', 'F1', 'P1']
    seasons = ['2425', '2324', '2223', '2122'] 
    df = loader.fetch_data(leagues, seasons)
    
    # from src.engine.predictor import Predictor
    
    def normalize_name_local(name):
        if not isinstance(name, str): return str(name)
        name = name.strip()
        mapping = {
            'Rayo Vallecano': 'Vallecano',
            'CA Osasuna': 'Osasuna',
            'RCD Mallorca': 'Mallorca',
            'Athletic Club': 'Ath Bilbao',
            'Real Betis': 'Betis',
            'Real Sociedad': 'Sociedad',
            'RC Celta': 'Celta',
            'Celta de Vigo': 'Celta',
            'Deportivo Alaves': 'Alaves',
            'Spurs': 'Tottenham',
            'Tottenham Hotspur': 'Tottenham',
            'Man Utd': 'Man United',
            'Manchester United': 'Man United',
            'Man City': 'Man City',
            'Manchester City': 'Man City',
            'Wolves': 'Wolves',
            'Wolverhampton': 'Wolves',
            'Nottm Forest': "Nott'm Forest",
            'Nottingham Forest': "Nott'm Forest",
            'Sheffield Utd': 'Sheffield United',
            'VfB Stuttgart': 'Stuttgart',
            'Bayer Leverkusen': 'Leverkusen',
            'Eintracht Frankfurt': 'Ein Frankfurt',
            'Borussia Dortmund': 'Dortmund',
            'Borussia Monchengladbach': 'M\'gladbach',
            'Mainz 05': 'Mainz',
            'Espanyol': 'Espanol',
            'RCD Espanyol': 'Espanol',
            'Inter Milan': 'Inter',
            'Internazionale': 'Inter',
            'AC Milan': 'Milan',
            'AS Roma': 'Roma',
            'SS Lazio': 'Lazio',
            'Atalanta BC': 'Atalanta',
            'Hellas Verona': 'Verona',
            'Verona': 'Verona',
            'Paris Saint Germain': 'Paris SG',
            'Paris SG': 'Paris SG',
        }
        return mapping.get(name, name)

    # Apply normalization to the ACTUAL loaded dataframe
    df['HomeTeam'] = df['HomeTeam'].apply(normalize_name_local)
    df['AwayTeam'] = df['AwayTeam'].apply(normalize_name_local)
    
    print(f"Loaded {len(df)} matches.")

    # Feature Engineering
    engineer = FeatureEngineer(df)
    
    # Use standard methods (Robust and Consistent with App)
    # Pass empty cup schedule or None for basic check
    df = engineer.add_rest_days(cup_schedule=None) 
    df = engineer.add_rolling_stats(window=5)
    df = engineer.add_recent_form(window=5)
    df = engineer.add_relative_strength() # Adds HomeAttackStrength etc.
    
    # Fill N/A locally to be safe before dropping
    # Some older matches might still have NaNs in 'HomeAttackStrength' etc. if stats missing
    # But add_rolling_stats already fills main metrics.
    
    # Just drop rows where critical inputs are missing (e.g. RollingAvg == 0 might be valid, but NaN is not)
    # The engineer fills NaNs so dropna shouldn't kill everything unless something big is wrong.

    # Relaxed Cleaning: Do not dropna globally as it kills everything if one column like 'HomeAttackStrength' is missing in early rows
    # df = df.dropna().copy()
    
    # Just fill generic
    df = df.fillna(0)
    print(f"Data available: {len(df)} matches.")

    # Split into Train (older) and Test (newest season/matches)
    # Let's say we test on the last 20% of matches sorted by date
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]
    
    print(f"Training Set: {len(train_df)} | Test Set: {len(test_df)}")

    print("\n--- 3. TRAINING FRESH MODEL ---")
    engine = MLEngine()
    # Force fresh training
    # engine.train_models(train_df) # Assuming train_models handles its own feature recalc or we pass engineered df?
    # Actually MLEngine usually takes Raw DF and calculates features internally in _calculate_expanding_stats
    # BUT here we passed pre-calculated DF.
    # This explains the issue! passing FeatureEngineered data to train_models which expects raw data.
    
    # FIX: Pass RAW data to train_models, but we already modified df.
    # We should reload or just pass the raw columns.
    # Actually, let's just let MLEngine do its thing on the raw columns present in train_df.
    scores = engine.train_models(train_df)
    print("Training Scores (R2/Accuracy on Train):", scores)

    print("\n--- 4. RUNNING PREDICTIONS ON TEST SET ---")
    
    correct_scores = 0
    correct_results = 0 # W/D/L
    total = 0
    
    predictions_log = []

    print(f"Predictions check: {len(test_df)} rows to test.")
    
    for idx, row in test_df.iterrows():
        # Prepare row for prediction
        # MLEngine.predict_row expects a DICT of FEATURES (HomePPG, etc.)
        # Since we ran FeatureEngineer on df, 'HomePPG' etc are present.
        # So row.to_dict() works.
        pred_dict = engine.predict_row(row.to_dict())
        
        # Ground Truth
        if 'FTHG' not in row: continue
        
        actual_h = row['FTHG']
        actual_a = row['FTAG']
        
        if row['FTHG'] > row['FTAG']: actual_res = 'H'
        elif row['FTAG'] > row['FTHG']: actual_res = 'A'
        else: actual_res = 'D'
        
        # Prediction
        pred_h = pred_dict.get('REG_HomeGoals', 0)
        pred_a = pred_dict.get('REG_AwayGoals', 0)
        
        # Determine Predicted Result (W/D/L) from Goals
        if pred_h > pred_a: pred_res_derived = 'H'
        elif pred_a > pred_h: pred_res_derived = 'A'
        else: pred_res_derived = 'D'
        
        # Check Exact Score
        if round(pred_h) == actual_h and round(pred_a) == actual_a:
            correct_scores += 1
            
        # Check W/D/L (derived from goals)
        if pred_res_derived == actual_res:
             correct_results += 1
             
        total += 1
        
        if idx % 500 == 0:
            print(f"Processed {total} matches...")

    print("\n--- 5. RESULTS ANALYSIS ---")
    print(f"Total Matches Tested: {total}")
    
    if total > 0:
        print(f"Exact Score Accuracy: {correct_scores} / {total} ({correct_scores/total*100:.2f}%)")
        print(f"1X2 (Result) Accuracy (via Goals): {correct_results} / {total} ({correct_results/total*100:.2f}%)")
        
        # Analyze 0-0 bias
        zeros = 0
        for idx, row in test_df.iterrows():
            pred_dict = engine.predict_row(row.to_dict())
            if pred_dict.get('REG_HomeGoals') == 0 and pred_dict.get('REG_AwayGoals') == 0:
                zeros += 1
                
        print(f"Predictions that were exactly 0-0: {zeros} ({zeros/total*100:.2f}%)")
    else:
        print("No matches tested (Total=0). Check data loading.")

if __name__ == "__main__":
    run_backtest()
