import sys
import os
import pandas as pd
import json
import datetime
import time

# Add src to path
sys.path.append(os.getcwd())

from src.data.loader import DataLoader
from src.data.upcoming import FixturesFetcher
from src.engine.predictor import Predictor
from src.engine.strategies import PREMATCH_PATTERNS
from src.utils.normalization import NameNormalizer

CACHE_FILE = "data_cache/dashboard_data.json"
ALL_LEAGUES = ['SP1', 'SP2', 'E0', 'E1', 'D1', 'I1', 'F1', 'P1', 'N1']

import numpy as np

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date, pd.Timestamp)):
            return obj.isoformat()
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        if isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        return super(DateTimeEncoder, self).default(obj)

def update_data():
    print(f"[{datetime.datetime.now()}] 🚀 Starting Backend Data Update...", flush=True)
    
    # 1. Load History (Needed for Predictor)
    print("1. Loading Historical Data...", flush=True)
    loader = DataLoader()
    # Fetch 2 seasons for robust stats
    data = loader.fetch_data(ALL_LEAGUES, ['2425', '2324'])
    
    if data.empty:
        print("❌ Error: Historical Data is empty. Aborting.", flush=True)
        return

    # Initialize Predictor
    print("   Initializing Predictor...", flush=True)
    predictor = Predictor(data)
    
    # 2. Fetch Upcoming Matches
    print(f"2. Fetching Upcoming Fixtures for {len(ALL_LEAGUES)} leagues...", flush=True)
    fetcher = FixturesFetcher()
    # Fetch for next 7 days
    upcoming_df = fetcher.fetch_upcoming(ALL_LEAGUES)
    
    if upcoming_df.empty:
        print("⚠️ No upcoming matches found.", flush=True)
        save_empty()
        return
        
    print(f"   Found {len(upcoming_df)} upcoming matches.", flush=True)
    
    # 3. Analyze & Enrich (Strategies + Odds)
    # The Predictor.analyze_upcoming method already does:
    # - Feature Engineering
    # - Odds Fetching (via cache or API logic embedded in predict_match_safe helpers?)
    # Wait, Predictor.analyze_upcoming calls predict_match_safe
    # predict_match_safe uses 'known_odds' if passed.
    
    # We need to explicitly FETCH ODDS here and pass them, OR rely on FixturesFetcher?
    # FixturesFetcher.fetch_upcoming calls OddsApiClient internally! 
    # Let's verify FixturesFetcher logic.
    # ... FixturesFetcher DOES merge odds if available.
    
    print("3. Analyzing Matches (Running Strategies)...", flush=True)
    
    # We use a helper to replicate app.py logic
    analyzed_results = []
    
    # Pre-calculate Pattern Docs for frontend
    patterns_info = {name: doc for name, _, doc, _ in PREMATCH_PATTERNS}
    
    # We'll group matches by League for easier frontend consumption
    grouped_data = {}
    
    # Counter
    strat_count = 0
    
    for idx, row in upcoming_df.iterrows():
        try:
            home = row['HomeTeam']
            away = row['AwayTeam']
            league = row.get('Div', 'Unknown')
            
            # Predict & Enrich
            # Pass existing odds columns if present
            current_odds = {k: v for k, v in row.items() if str(k).startswith('B365')}
            
            # Run Prediction
            analysis = predictor.predict_match_safe(home, away, referee=row.get('Referee'), known_odds=current_odds)
            
            # Merge Metadata
            full_match = row.to_dict()
            full_match.update(analysis)
            
            # Check Strategies
            active_strategies = []
            for name, func, _, _ in PREMATCH_PATTERNS:
                if func(analysis):
                    active_strategies.append(name)
            
            full_match['active_strategies'] = active_strategies
            if active_strategies:
                strat_count += 1
                
            analyzed_results.append(full_match)
            
        except Exception as e:
            print(f"   Error analyzing {row.get('HomeTeam')} vs {row.get('AwayTeam')}: {e}")

    print(f"   Analysis Complete. Found {strat_count} matches with active strategies.", flush=True)

    # 4. Structure for Frontend
    output = {
        "metadata": {
            "last_updated": datetime.datetime.now().isoformat(),
            "total_matches": len(upcoming_df),
            "strategies_found": strat_count
        },
        "patterns_info": patterns_info,
        "matches": analyzed_results 
    }
    
    # 5. Save
    print(f"4. Saving to {CACHE_FILE}...", flush=True)
    try:
        if not os.path.exists("data_cache"):
            os.makedirs("data_cache")
            
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(output, f, cls=DateTimeEncoder, indent=2)
        print("✅ Success! Data pipeline finished.", flush=True)
        
    except Exception as e:
        print(f"❌ Error saving file: {e}", flush=True)

def save_empty():
    output = {
        "metadata": {
            "last_updated": datetime.datetime.now().isoformat(),
            "total_matches": 0,
            "strategies_found": 0
        },
        "matches": []
    }
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    update_data()
