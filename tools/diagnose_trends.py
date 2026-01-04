
import sys
import os
import pandas as pd
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.upcoming import FixturesFetcher
from src.data.loader import DataLoader
from src.engine.trends_scanner import TrendScanner
from src.engine.predictor import Predictor

def diagnose():
    print("=== Diagnosing Trends & Strategies ===")
    
    # 1. Fetch Upcoming
    print("Fetching upcoming...")
    fetcher = FixturesFetcher()
    upcoming_df = fetcher.fetch_upcoming(['SP2']) # Focus on the problematic league
    
    if upcoming_df.empty:
        print("No upcoming matches found.")
        return

    print(f"Found {len(upcoming_df)} matches.")
    
    # 2. Load History
    print("Loading history...")
    loader = DataLoader()
    # Mocking what app.py does roughly
    historical_df = loader.fetch_data(leagues=['SP2'], seasons=['2425', '2526']) # Load recent
    
    # Normalize history (important step usually done in Predictor or App)
    pred_dummy = Predictor(historical_df) 
    historical_df = pred_dummy.history 
    
    scanner = TrendScanner()
    
    # 3. Test Trends Scanner
    print("\nScanning Trends for upcoming matches...")
    for idx, row in upcoming_df.iterrows():
        home_team = row['HomeTeam']
        away_team = row['AwayTeam']
        
        # Normalize names (Predictor logic)
        norm_home = pred_dummy.normalize_name(home_team)
        norm_away = pred_dummy.normalize_name(away_team)
        
        print(f"Match: {home_team} ({norm_home}) vs {away_team} ({norm_away})")
        
        try:
            trends = scanner.scan(norm_home, historical_df)
            print(f"  Trends (Home): {len(trends)} found.")
        except Exception as e:
            print(f"  [ERROR] Trend Scan Failed for {norm_home}: {e}")
            
    # 4. Test Strategies (Features + Conditions)
    # This involves calculating features which might fail if history is empty
    print("\nChecking AI Strategies prerequisites (Feature Calculation)...")
    from src.engine.features import FeatureEngineer
    try:
        # Check constructor logic
        engineer = FeatureEngineer(historical_df) 
    except TypeError:
        # Fallback if it doesnt take args (older version?)
        engineer = FeatureEngineer()
    
    try:
        # Just try one calculation
        if not historical_df.empty:
            # engineer.calculate_features(historical_df) # Method doesnt exist, calling steps manually
            df = engineer.add_rest_days()
            df = engineer.add_rolling_stats()
            df = engineer.add_recent_form()
            engineer.df = df # Update state
            print("  Feature calculation successful.")
        else:
            print("  Historical DF is empty!")
    except Exception as e:
        print(f"  [ERROR] Feature Calculation Failed: {e}")

if __name__ == "__main__":
    diagnose()
