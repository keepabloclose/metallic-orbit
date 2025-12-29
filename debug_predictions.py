import pandas as pd
from src.data.loader import DataLoader
from src.data.upcoming import FixturesFetcher
from src.engine.predictor import Predictor

# Load data
print("Loading data...")
loader = DataLoader()
df = loader.fetch_data(['SP1', 'E0', 'I1'], ['2324', '2425', '2526'])
print(f"Loaded {len(df)} historical matches")

# Fetch upcoming
print("Fetching upcoming...")
fetcher = FixturesFetcher()
upcoming = fetcher.fetch_upcoming(['SP1', 'E0', 'I1'])
print(f"Found {len(upcoming)} upcoming matches")

if not upcoming.empty and not df.empty:
    predictor = Predictor(df)
    
    print("\n--- Inspecting First 5 Matches ---")
    for idx, match in upcoming.head(5).iterrows():
        print(f"\n{match['HomeTeam']} vs {match['AwayTeam']}")
        try:
            row = predictor.predict_match(match['HomeTeam'], match['AwayTeam'])
            if row:
                print(f"  Rest: Home={row.get('HomeRestDays')}, Away={row.get('AwayRestDays')}")
                print(f"  Goals: H_AvgFor={row.get('HomeAvgGoalsFor')}, A_AvgAgainst={row.get('AwayAvgGoalsAgainst')}")
                
                # Check conditions
                cond1 = row['HomeRestDays'] > 7 and row['AwayRestDays'] < 4
                cond2 = row['HomeAvgGoalsFor'] > 2.0 and row['AwayAvgGoalsAgainst'] > 1.5
                print(f"  > Cond Rest (>7 vs <4): {cond1}")
                print(f"  > Cond Goals (>2.0 vs >1.5): {cond2}")
            else:
                print("  No prediction row generated (Insufficient history?)")
        except Exception as e:
            print(f"  Error: {e}")
else:
    print("Data missing")
