
import pandas as pd
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from src.data.loader import DataLoader
from src.data.cups import CupLoader
from src.engine.features import FeatureEngineer
from src.engine.patterns import PatternAnalyzer

def load_data():
    print("Loading Data...")
    leagues = ['SP1', 'E0', 'D1', 'I1', 'F1', 'P1']
    seasons = ['2526', '2425', '2324', '2223', '2122', '2021'] # Last 5-6 years
    loader = DataLoader(cache_dir="data_cache")
    df = loader.fetch_data(leagues, seasons)
    
    # Cup data
    try:
        cup_loader = CupLoader()
        cup_schedule = cup_loader.fetch_all_cups()
    except:
        cup_schedule = None

    print("Engineering Features...")
    engineer = FeatureEngineer(df)
    df = engineer.add_rest_days(cup_schedule=cup_schedule)
    df = engineer.add_rolling_stats(window=5)
    df = engineer.add_recent_form(window=5)
    df = engineer.add_opponent_difficulty(window=5)
    df = engineer.add_relative_strength()
    
    # Fill NA odds for calculation (though we need real odds for ROI)
    # Assuming columns like B365H, B365D, B365A exist
    return df

def run_grid_search(df):
    results = []
    
    analyzer = PatternAnalyzer(df)
    
    # Grid Search for "Local Dominante"
    print("Optimizing 'Local Dominante'...")
    for goal_thresh in [1.5, 1.8, 2.0, 2.2]:
        for sot_thresh in [4.0, 4.5, 5.0, 5.5]:
            for opp_goal_thresh in [0.8, 1.0, 1.2]:
                
                def cond(row):
                    return (row['HomeAvgGoalsFor'] > goal_thresh and 
                            row['HomeAvgGoalsAgainst'] < 1.2 and
                            row['HomeAvgShotsTargetFor'] > sot_thresh and
                            row['AwayAvgGoalsFor'] < opp_goal_thresh)
                
                def target(row): return row['FTHG'] > row['FTAG']
                
                pat_name = f"LocalDom_G{goal_thresh}_SOT{sot_thresh}_OppG{opp_goal_thresh}"
                # Evaluate manually to get ROI
                mask = df.apply(cond, axis=1)
                matches = df[mask]
                
                if len(matches) > 50:
                    roi = 0.0
                    if "B365H" in matches.columns:
                        odds = matches["B365H"]
                        wins = matches.apply(target, axis=1)
                        # Filter to valid odds
                        valid_mask = odds.notna()
                        if valid_mask.sum() > 0:
                            profit = (odds[valid_mask] * wins[valid_mask]).sum() - len(odds[valid_mask])
                            roi = profit / len(odds[valid_mask])
                    
                    if roi > 0.05:
                        results.append({'Pattern': 'Local Dominante', 'Params': pat_name, 'ROI': roi, 'Matches': len(matches)})

    # Grid Search for "Over 2.5" (Goal Fest)
    print("Optimizing 'Festival de Goles'...")
    for combined_goals in [3.0, 3.2, 3.5, 3.8]:
        for combined_leak in [3.0, 3.5]:
             def cond(row):
                 return ((row['HomeAvgGoalsFor'] + row['AwayAvgGoalsFor'] > combined_goals) or 
                         (row['HomeAvgGoalsAgainst'] + row['AwayAvgGoalsAgainst'] > combined_leak))
             
             def target(row): return (row['FTHG'] + row['FTAG']) > 2.5
             
             pat_name = f"Fest_CombG{combined_goals}_Leak{combined_leak}"
             mask = df.apply(cond, axis=1)
             matches = df[mask]
             
             if len(matches) > 50:
                 roi = 0.0
                 if "B365>2.5" in matches.columns:
                     odds = matches["B365>2.5"]
                     wins = matches.apply(target, axis=1)
                     valid_mask = odds.notna()
                     if valid_mask.sum() > 0:
                         profit = (odds[valid_mask] * wins[valid_mask]).sum() - len(odds[valid_mask])
                         roi = profit / len(odds[valid_mask])

                 if roi > 0.04: # Accept 4%
                     results.append({'Pattern': 'Goal Fest', 'Params': pat_name, 'ROI': roi, 'Matches': len(matches)})

    # Grid Search for "Under 2.5" (Walls)
    print("Optimizing 'Muralla Defensiva'...")
    for goal_limit in [0.8, 1.0, 1.1, 1.2]:
             def cond(row):
                 return (row['HomeAvgGoalsFor'] < goal_limit and row['AwayAvgGoalsFor'] < goal_limit)
             
             def target(row): return (row['FTHG'] + row['FTAG']) < 2.5
             
             pat_name = f"Wall_G{goal_limit}"
             mask = df.apply(cond, axis=1)
             matches = df[mask]
             
             if len(matches) > 50:
                roi = 0.0
                if "B365<2.5" in matches.columns:
                     odds = matches["B365<2.5"]
                     wins = matches.apply(target, axis=1)
                     valid_mask = odds.notna()
                     if valid_mask.sum() > 0:
                         profit = (odds[valid_mask] * wins[valid_mask]).sum() - len(odds[valid_mask])
                         roi = profit / len(odds[valid_mask])

                if roi > 0.05:
                    results.append({'Pattern': 'Under 2.5', 'Params': pat_name, 'ROI': roi, 'Matches': len(matches)})

    # Print Top Results
    print("\n--- OPTIMIZATION RESULTS (>5% ROI) ---")
    results_df = pd.DataFrame(results)
    if not results_df.empty:
        print(results_df.sort_values('ROI', ascending=False).head(10).to_string())
    else:
        print("No param sets found with >5% ROI >50 matches.")

if __name__ == "__main__":
    df = load_data()
    run_grid_search(df)
