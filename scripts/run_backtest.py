import sys
import os
import pandas as pd

# Add project root to path
sys.path.append(os.getcwd())

from src.data.loader import DataLoader
from src.engine.features import FeatureEngineer
from src.engine.patterns import PatternAnalyzer
from src.engine.strategies import PREMATCH_PATTERNS
from src.data.cups import CupLoader

def run_backtest():
    print(">>> Iniciando Backtest CLI...")
    
    # 1. Load Data
    loader = DataLoader()
    leagues = ['SP1', 'E0', 'D1', 'I1', 'F1', 'P1']
    seasons = ['2425', '2324', '2223', '2122']
    print(f"Loading data for {leagues} ({seasons})...")
    df = loader.fetch_data(leagues, seasons)
    
    # 2. Add Features
    print("Engineering features...")
    engineer = FeatureEngineer(df)
    
    # Try loading cups
    try:
        cup_loader = CupLoader()
        cup_schedule = cup_loader.fetch_all_cups()
        df = engineer.add_rest_days(cup_schedule=cup_schedule)
    except:
        df = engineer.add_rest_days()
        
    df = engineer.add_rolling_stats(window=5)
    df = engineer.add_recent_form(window=5)
    df = engineer.add_opponent_difficulty(window=5)
    df = engineer.add_relative_strength()
    
    print(f"Data ready: {len(df)} matches.")
    
    # 3. Define Patterns (from strategies.py)
    # The dataframe has features like 'HomeAvgGoalsFor' calculated by FeatureEngineer.
    # Note: FeatureEngineer calculates stats *entering* the match (shifted), which is CORRECT for backtesting historical data.
    # Our Predictor fix (calculating on fly) is for PREDICTING FUTURE matches where rows don't exist yet.
    # For backtesting existing rows, the columns in DF are already correct (shifted).
    
    analyzer = PatternAnalyzer(df)
    
    print("Running Pattern Analysis...")
    summary, details = analyzer.scan_patterns(PREMATCH_PATTERNS)
    
    print("\nRESULTADOS DE BACKTESTING:")
    print("="*60)
    
    # Format for display
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    
    # Select cols to show
    cols = ['pattern_name', 'matches', 'probability', 'roi', 'EV']
    print(summary[cols].to_string(index=False))
    
    print("\n[OK] Backtest finalizado.")

if __name__ == "__main__":
    run_backtest()
