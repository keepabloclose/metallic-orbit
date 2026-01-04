
import sys
import os
import pandas as pd
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.loader import DataLoader
from src.data.upcoming import FixturesFetcher
from src.engine.features import FeatureEngineer
from src.engine.predictor import Predictor

def check_strategies():
    print("=== Checking Strategies Data Flow ===")
    
    # 1. Load History & Features
    print("Loading history & calculating features...")
    loader = DataLoader()
    historical_df = loader.fetch_data(['E0', 'SP1', 'SP2'], ['2425', '2526'])
    
    engineer = FeatureEngineer(historical_df)
    # engineer.calculate_features(historical_df) # Broken interface in previous turn, fixed in class?
    # Let's check which method is correct or if I should call individual ones
    # Based on features.py content, I should call individual methods or add_recent_form etc.
    if hasattr(engineer, 'calculate_features'):
        historical_df = engineer.calculate_features(historical_df)
    else:
        historical_df = engineer.add_rest_days()
        historical_df = engineer.add_rolling_stats()
        historical_df = engineer.add_recent_form()
    
    print(f"Features calculated. Columns: {len(historical_df.columns)}")
    
    # 2. Fetch Upcoming
    print("Fetching upcoming...")
    fetcher = FixturesFetcher()
    upcoming_df = fetcher.fetch_upcoming(['E0', 'SP1', 'SP2'])
    
    if upcoming_df.empty:
        print("No upcoming matches.")
        return

    # 3. Predictor Merge Logic (Simulating what App/PatternAnalyzer might do)
    # Usually Predictor or PatternAnalyzer merges features based on Team Name
    # BUT, FeatureEngineer attaches rolling stats to the *historical* rows.
    # We need to get the "latest" stats for each team and attach to upcoming.
    
    print("\n--- Simulating Feature Merge ---")
    
    # Get latest stats per team
    latest_stats = historical_df.sort_values('Date').groupby('HomeTeam').last().reset_index()
    # Note: 'HomeTeam' in grouping relies on the row being a home game? 
    # Actually features.py adds 'HomeAvgGoalsFor' etc to every row. 
    # Yes, we need the last row where the team played (either Home or Away).
    
    # Simplified check: Look at a team we know exists
    target_team = "Real Madrid" 
    print(f"Checking features for {target_team}...")
    
    team_stats = historical_df[(historical_df['HomeTeam'] == target_team) | (historical_df['AwayTeam'] == target_team)].sort_values('Date').tail(1)
    
    if not team_stats.empty:
        print("Latest Historical Row Found:")
        cols = ['Date', 'HomeTeam', 'AwayTeam', 'HomeAvgGoalsFor', 'HomePPG']
        for c in cols:
            if c in team_stats.columns:
                print(f"  {c}: {team_stats[c].values[0]}")
            else:
                print(f"  {c}: MISSING")
    else:
        print(f"Team {target_team} not found in history.")

    # Check Upcoming Merge
    # How does the app merge?
    # Usually via Predictor using `get_latest_stats(team)`
    
    pred = Predictor(historical_df)
    
    for idx, row in upcoming_df.head(5).iterrows():
        home = row['HomeTeam']
        norm_home = pred.normalize_name(home)
        
        # Check if Predictor can find stats
        # (This depends on Predictor implementation details not fully visible in snippet, but we can infer)
        
        print(f"\nMatch: {home} vs {row['AwayTeam']}")
        
        # Try to pull a feature manually
        # In `strategies.py`, it expects `row['HomeAvgGoalsFor']`.
        # This implies `upcoming_df` MUST have these columns.
        
        # If `upcoming_df` is raw from fetcher, it lacks these.
        # Check if `ml_engine` or `PatternAnalyzer` adds them.
        
        # Let's inspect ONE row processed by `_calculate_expanding_stats` in ml_engine if possible?
        # No, `Strategies` usually runs on Upcoming matches enriched with stats.
        
        pass

if __name__ == "__main__":
    check_strategies()
