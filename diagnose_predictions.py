
import pandas as pd
import sys
import os
import datetime

# Add root to path
sys.path.append(os.getcwd())

from src.data.loader import DataLoader
from src.data.upcoming import FixturesFetcher
from src.engine.predictor import Predictor
from src.engine.features import FeatureEngineer

def diagnose_all_predictions():
    print("--- DIAGNOSTIC: LOADING DATA ---")
    loader = DataLoader()
    # Load ALL supported leagues to catch any missing data issues
    leagues = ['SP1', 'E0', 'E1', 'D1', 'I1', 'F1', 'P1', 'N1', 'B1'] 
    seasons = ['2425', '2324', '2223'] # Load sufficient history
    
    # 1. Fetch History
    df = loader.fetch_data(leagues, seasons)
    print(f"Loaded {len(df)} historical matches.")
    
    # Replicate app.py feature engineering
    engineer = FeatureEngineer(df)
    df = engineer.add_rolling_stats(window=5)
    df = engineer.add_recent_form(window=5)
    df = engineer.add_relative_strength()

    # Add RestDays (Required by MLEngine)
    long_df = pd.concat([
        df[['Date', 'HomeTeam']].rename(columns={'HomeTeam': 'Team'}),
        df[['Date', 'AwayTeam']].rename(columns={'AwayTeam': 'Team'})
    ])
    long_df = long_df.sort_values(['Team', 'Date'])
    long_df['PrevDate'] = long_df.groupby('Team')['Date'].shift(1)
    long_df['RestDays'] = (long_df['Date'] - long_df['PrevDate']).dt.days.fillna(7)
    rest_map = long_df.set_index(['Date', 'Team'])['RestDays']
    df['HomeRestDays'] = df.apply(lambda x: rest_map.get((x['Date'], x['HomeTeam']), 7), axis=1)
    df['AwayRestDays'] = df.apply(lambda x: rest_map.get((x['Date'], x['AwayTeam']), 7), axis=1)
    
    # 2. Fetch Upcoming Fixtures
    fetcher = FixturesFetcher()
    # Fetch for supported leagues (intersection with what Fetcher supports)
    # The Fetcher might not support all leagues in 'leagues' list, which is fine.
    # It defaults to a list in its run method? 
    # fetch_upcoming takes 'leagues'.
    upcoming = fetcher.fetch_upcoming(leagues)
    print(f"Found {len(upcoming)} upcoming matches.")
    
    if len(upcoming) == 0:
        print("CRITICAL: No upcoming matches found. Check data source.")
        return

    # 3. Initialize Predictor
    print("Initializing Predictor...")
    predictor = Predictor(df)
    # Ensure model is trained/loaded
    # Check if regressors are populated
    if not predictor.ml_engine.regressors.get('REG_HomeGoals'):
         print("Model not loaded/trained. Forcing training...")
         predictor.ml_engine.train_models(predictor.history)

    # 4. Run Predictions
    print("\n--- PREDICTION SCAN ---")
    print(f"{'Date':<12} | {'League':<4} | {'Home Team':<20} | {'Away Team':<20} | {'Pred':<10} | {'Status'}")
    print("-" * 90)
    
    zero_count = 0
    fail_count = 0
    ok_count = 0
    
    for _, match in upcoming.sort_values('Date').iterrows():
        try:
            home = match['HomeTeam']
            away = match['AwayTeam']
            date = match['Date']
            div = match.get('Div', '??')
            
            # Predict
            pred = predictor.predict_match(home, away)
            
            if not pred:
                status = "FAILED (No Stats)"
                pred_str = "N/A"
                fail_count += 1
            else:
                ph = pred.get('REG_HomeGoals', 0)
                pa = pred.get('REG_AwayGoals', 0)
                pred_str = f"{ph:.2f} - {pa:.2f}"
                
                if ph == 0 and pa == 0:
                    status = "ZERO_BUG"
                    zero_count += 1
                elif ph < 0.1 and pa < 0.1:
                    status = "NEAR_ZERO" # Suspiciously low
                    zero_count += 1
                else:
                    status = "OK"
                    ok_count += 1
            
            print(f"{date.strftime('%Y-%m-%d'):<12} | {div:<4} | {home:<20} | {away:<20} | {pred_str:<10} | {status}")
            
            # Deep dive diagnostics for FIRST failure
            if (status == "FAILED (No Stats)" or status == "ZERO_BUG") and fail_count + zero_count == 1:
                print(f"\n[DEBUG FAILURE] Analyzing {home} vs {away}...")
                print(f"  Normalized Home: {predictor.normalize_name(home)}")
                print(f"  Normalized Away: {predictor.normalize_name(away)}")
                # Check history presence
                h_norm = predictor.normalize_name(home)
                a_norm = predictor.normalize_name(away)
                h_hist = predictor.history[(predictor.history['HomeTeam'] == h_norm) | (predictor.history['AwayTeam'] == h_norm)]
                a_hist = predictor.history[(predictor.history['HomeTeam'] == a_norm) | (predictor.history['AwayTeam'] == a_norm)]
                print(f"  History matches for {h_norm}: {len(h_hist)}")
                print(f"  History matches for {a_norm}: {len(a_hist)}")
                
        except Exception as e:
            print(f"CRASH: {home} vs {away} - {e}")
            fail_count += 1

    print("-" * 90)
    print(f"Summary: OK={ok_count}, ZERO/LOW={zero_count}, FAILED={fail_count}, Total={len(upcoming)}")

if __name__ == "__main__":
    diagnose_all_predictions()
