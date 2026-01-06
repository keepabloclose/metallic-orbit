import pandas as pd
from src.data.loader import DataLoader
from src.data.upcoming import FixturesFetcher
from src.engine.predictor import Predictor

# Load data
print("Loading data...")
loader = DataLoader()
# Load historical data (Current Seasons)
target_leagues = ['SP1', 'E1', 'E0', 'I1', 'D1', 'F1', 'SP2']
df = loader.fetch_data(target_leagues, ['2324', '2425', '2526'])
print(f"Loaded {len(df)} historical matches")

# Fetch upcoming
print("Fetching upcoming...")
fetcher = FixturesFetcher()
upcoming = fetcher.fetch_upcoming(target_leagues)
print(f"Found {len(upcoming)} upcoming matches")

if not upcoming.empty and not df.empty:
    predictor = Predictor(df)
    
    print("\n--- Inspecting First 5 Matches ---")
    for idx, match in upcoming.head(5).iterrows():
        print(f"\n{match['HomeTeam']} vs {match['AwayTeam']}")
        try:
            # Construct known_odds from match row
            k_odds = {}
            if 'B365H' in match and pd.notna(match['B365H']):
                k_odds = {
                    'B365H': match['B365H'], 'B365D': match.get('B365D'), 'B365A': match.get('B365A'),
                    'B365_Over2.5': match.get('B365_Over2.5'), 'B365_BTTS_Yes': match.get('B365_BTTS_Yes')
                }
            
            row = predictor.predict_match_safe(match['HomeTeam'], match['AwayTeam'], known_odds=k_odds)
            if row:
                print(f"  Rest: Home={row.get('HomeRestDays')}, Away={row.get('AwayRestDays')}")
                print(f"  Goals: H_AvgFor={row.get('HomeAvgGoalsFor')}, A_AvgAgainst={row.get('AwayAvgGoalsAgainst')}")
                print(f"  Odds (H/D/A): {row.get('B365H')} / {row.get('B365D')} / {row.get('B365A')}")
                print(f"  Odds (Over2.5): {row.get('B365_Over2.5')} | BTTS(Yes): {row.get('B365_BTTS_Yes')}")
                
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
