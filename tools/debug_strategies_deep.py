
import sys
import os
import pandas as pd
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.loader import DataLoader
from src.data.upcoming import FixturesFetcher
from src.engine.predictor import Predictor
from src.engine.patterns import PatternAnalyzer
from src.engine.strategies import PREMATCH_PATTERNS

def debug_deep():
    print("=== Deep Debug Strategies ===")
    
    # 1. Setup Same Environment
    fetcher = FixturesFetcher()
    upcoming_df = fetcher.fetch_upcoming(['E0']) # Premier League usually has data
    if upcoming_df.empty:
        print("No matches to debug.")
        return
        
    loader = DataLoader()
    historical_df = loader.fetch_data(['E0'], ['2425', '2526'])
    predictor = Predictor(historical_df)
    analyzer = PatternAnalyzer(historical_df) # This df is for backtest, unused for upcoming check?
    
    # 2. Pick a likely match
    target_match = None
    for idx, row in upcoming_df.iterrows():
        # Pick a match with strong teams if possible
        if row['HomeTeam'] in ['Liverpool', 'Arsenal', 'Man City', 'Aston Villa']:
            target_match = row
            break
            
    if target_match is None:
        target_match = upcoming_df.iloc[0]
        
    print(f"\nAnalyzing Target Match: {target_match['HomeTeam']} vs {target_match['AwayTeam']}")
    
    # 3. Predict & Enrich
    home = target_match['HomeTeam']
    away = target_match['AwayTeam']
    enriched = predictor.predict_match_safe(home, away)
    
    print("\n--- Enriched Features (Probe) ---")
    keys_to_check = ['HomePPG', 'HomeAvgGoalsFor', 'HomeWinsLast5', 'HomeZScore_Goals', 'AwayCleanSheet_Rate', 'HomeRestDays']
    for k in keys_to_check:
        print(f"  {k}: {enriched.get(k, 'MISSING')}")
        
    # 4. Manually Evaluate 'Local Dominante'
    print("\n--- Manual Condition Check: Local Dominante ---")
    
    # Define condition logic locally to debug
    row = enriched
    
    # Feature Extraction
    h_avg_goals = row.get('HomeAvgGoalsFor', 0)
    h_ppg = row.get('HomePPG', 0)
    h_wins = row.get('HomeWinsLast5', 0)
    a_cs = row.get('AwayCleanSheet_Rate', 1.0)
    h_z = row.get('HomeZScore_Goals', 0)
    
    print(f"  FEATURES:")
    print(f"    HomeAvgGoalsFor: {h_avg_goals} (Req: > 1.6)")
    print(f"    HomePPG:         {h_ppg} (Req: > 1.6)")
    print(f"    HomeWinsLast5:   {h_wins} (Req: >= 3)")
    print(f"    AwayCleanSheet:  {a_cs} (Req: <= 0.2)")
    print(f"    HomeZScore:      {h_z} (Req: <= 2.5)")
    
    c1 = h_avg_goals > 1.6
    c2 = h_ppg > 1.6
    c3 = h_wins >= 3
    c4 = a_cs <= 0.2
    c5 = not (h_z > 2.5) # Not validation risk
    
    print(f"  CONDITIONS: Goals={c1}, PPG={c2}, Wins={c3}, Defense={c4}, Z-Risk={c5}")
    
    if c1 and c2 and c3 and c4 and c5:
        print("  RESULT: PASS")
    else:
        print("  RESULT: FAIL")

    # 5. Check Analyzer Method Existence
    if hasattr(analyzer, 'check_patterns'):
        print("\nAnalyzer has 'check_patterns'. Running...")
        pats = analyzer.check_patterns(enriched)
        print(f"  Found: {pats}")
    else:
        print("\n[CRITICAL] PatternAnalyzer missing 'check_patterns' method!")

if __name__ == "__main__":
    debug_deep()
