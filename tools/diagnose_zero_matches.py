import pandas as pd
import sys
import os
import time

sys.path.append(os.getcwd())

from src.data.loader import DataLoader
from src.data.upcoming import FixturesFetcher
from src.engine.predictor import Predictor
from src.utils.normalization import NameNormalizer
from src.engine.strategies import PREMATCH_PATTERNS
from src.engine.features import FeatureEngineer

def diagnose():
    print("--- 🕵️ DIAGNOSING ZERO MATCHES ISSUE ---")
    
    # 1. Load History (Source of Truth)
    print("\n[1/4] Loading History DB...")
    loader = DataLoader() # Checks cache
    leagues = ['E0', 'E1', 'SP1', 'SP2', 'D1', 'I1', 'F1', 'P1', 'N1']
    seasons = ['2425', '2324', '2223', '2122']
    
    history = loader.fetch_data(leagues, seasons)
    if history.empty:
        print("❌ CRITICAL: No History Data Loaded.")
        return

    # Normalize History Names immediately (Like App does)
    history['HomeTeam'] = history['HomeTeam'].apply(NameNormalizer.normalize)
    history['AwayTeam'] = history['AwayTeam'].apply(NameNormalizer.normalize)
    
    # Feature Engineering (Crucial for Predictor to work right)
    print("[2/4] Engineering Features...")
    engineer = FeatureEngineer(history)
    history = engineer.add_rest_days()
    history = engineer.add_rolling_stats(window=5)
    history = engineer.add_recent_form(window=5)
    history = engineer.add_relative_strength()
    
    # Initialize Predictor
    predictor = Predictor(history)
    known_teams = set(history['HomeTeam'].unique()) | set(history['AwayTeam'].unique())
    print(f"✅ History Ready. Know {len(known_teams)} unique teams.")
    
    # 2. Fetch Upcoming
    print("\n[3/4] Fetching Upcoming Fixtures...")
    fetcher = FixturesFetcher()
    upcoming = fetcher.fetch_upcoming(leagues)
    
    if upcoming.empty:
        print("❌ No Upcoming Matches found to analyze.")
        return
        
    print(f"✅ Found {len(upcoming)} upcoming matches.")
    
    # 3. Analyze Each Match
    print("\n[4/4] Validating Matching & Strategies...")
    
    mismatch_count = 0
    valid_data_count = 0
    strategy_hits = 0
    
    # Sample logic failures to report
    failure_reasons = {} # {StrategyName: [Reason1, Reason2]}
    
    for idx, row in upcoming.iterrows():
        home = row['HomeTeam']
        away = row['AwayTeam']
        
        # Check Normalization
        norm_home = NameNormalizer.normalize(home)
        norm_away = NameNormalizer.normalize(away)
        
        h_exists = norm_home in known_teams
        a_exists = norm_away in known_teams
        
        if not h_exists or not a_exists:
            mismatch_count += 1
            print(f"⚠️ NAME MISMATCH: {home}->{norm_home} ({h_exists}) vs {away}->{norm_away} ({a_exists})")
            continue
            
        valid_data_count += 1
        
        # Get Stats (Predict)
        try:
            stats_row = predictor.predict_match_safe(norm_home, norm_away, match_date=row.get('Date'))
            
            # Check Strategies
            match_hits = []
            for name, cond_func, _, _ in PREMATCH_PATTERNS:
                try:
                    if cond_func(stats_row):
                        match_hits.append(name)
                        strategy_hits += 1
                    else:
                        # LOG WHY IT FAILED (For the first few matches)
                        if valid_data_count <= 5 and name == "Local Dominante (Estricto)": 
                            # Custom debug for this strategy
                            h_g = stats_row.get('HomeAvgGoalsFor', 0)
                            h_ppg = stats_row.get('HomePPG', 0)
                            a_cs = stats_row.get('AwayCleanSheet_Rate', 0)
                            z = stats_row.get('HomeZScore_Goals', 0)
                            
                            fail_msg = f"HG={h_g:.2f}(Need>1.25), PPG={h_ppg:.2f}(>1.35), ACS={a_cs:.2f}(<0.50), Z={z:.2f}(<3.5)"
                            if name not in failure_reasons: failure_reasons[name] = []
                            failure_reasons[name].append(fail_msg)
                            
                except Exception as e:
                    pass
            
            if match_hits:
                print(f"✅ MATCH: {norm_home} vs {norm_away} -> Matches: {match_hits}")
                
        except Exception as e:
            print(f"Error predicting {norm_home} vs {norm_away}: {e}")

    print("\n--- SUMMARY ---")
    print(f"Total Matches: {len(upcoming)}")
    print(f"Name Mismatches: {mismatch_count} (Data Missing)")
    print(f"Valid Data Matches: {valid_data_count}")
    print(f"Strategy Hits: {strategy_hits}")
    
    if strategy_hits == 0 and valid_data_count > 0:
        print("\n🔎 WHY NO HITS? (Examples from 'Local Dominante')")
        for reason in failure_reasons.get("Local Dominante (Estricto)", [])[:5]:
            print(f"  - Rejection: {reason}")

if __name__ == "__main__":
    diagnose()
