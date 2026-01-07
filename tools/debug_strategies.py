import pandas as pd
import sys
import os

sys.path.append(os.getcwd())

from src.engine.predictor import Predictor
from src.engine.strategies import PREMATCH_PATTERNS
from src.utils.normalization import NameNormalizer
from src.data.loader import DataLoader
from src.data.upcoming import FixturesFetcher

def debug_strat():
    print("--- Debugging AI Strategies ---")
    
    # 1. Load History
    print("Loading History...")
    loader = DataLoader()
    leagues = ['E0', 'E1', 'SP1', 'SP2']
    seasons = ['2425', '2324']
    history = loader.fetch_data(leagues, seasons)
    
    if history.empty:
        print("No History Loaded.")
        return

    # Ensure Date
    if 'Date' in history.columns:
        history['Date'] = pd.to_datetime(history['Date'], dayfirst=True, errors='coerce')
        history = history.dropna(subset=['Date'])
        
    predictor = Predictor(history)
    print("Predictor Initialized.")
    
    # 2. Fetch/Mock Mock Upcoming
    print("Fetching Upcoming...")
    fetcher = FixturesFetcher()
    upcoming = fetcher.fetch_upcoming(leagues)
    
    if upcoming.empty:
        print("No upcoming matches found.")
        # Create a mock match
        print("Creating Mock Match...")
        mock_row = {
            'HomeTeam': 'Manchester City',
            'AwayTeam': 'Everton',
            'Date': pd.Timestamp.now(),
            'Div': 'E0'
        }
        upcoming = pd.DataFrame([mock_row])
    
    # Take first match
    match = upcoming.iloc[0]
    home = match['HomeTeam']
    away = match['AwayTeam']
    
    print(f"\nAnalyzing Match: {home} vs {away}")

    # Predict
    # IMPORTANT: Need to run feature engineering on row locally? 
    # Predictor.predict_match does this internally using history.
    
    row = predictor.predict_match_safe(home, away)
    
    print("\n[Match Stats]")
    keys = ['HomeAvgGoalsFor', 'HomePPG', 'HomeWinsLast5', 'AwayCleanSheet_Rate', 'HomeZScore_Goals', 'Trap_FearError']
    for k in keys:
        print(f"{k}: {row.get(k, 'N/A')}")
        
    # Check Patterns
    print("\n[Strategy Check]")
    for name, cond_func, _, _ in PREMATCH_PATTERNS:
        try:
            res = cond_func(row)
            print(f"Strategy: {name} -> {res}")
        except Exception as e:
            print(f"Strategy {name} Error: {e}")

if __name__ == "__main__":
    debug_strat()

