
import pandas as pd
import sys
import os

# Setup path
sys.path.append(os.getcwd())
from src.utils.normalization import NameNormalizer

# 1. Load Odds DB (Mocking what OddsApiClient returns)
odds_db_path = "data_cache/odds_database.csv"
if os.path.exists(odds_db_path):
    enrichment_df = pd.read_csv(odds_db_path)
    print(f"Loaded {len(enrichment_df)} odds from DB.")
    print("Odds Columns:", enrichment_df.columns.tolist())
    
    # Enrichment Key Generation (as in upcoming.py)
    # Note: DB is already normalized by OddsApiClient usually, but let's check
    # CRITICAL FIX: Re-normalize just in case DB is stale or raw
    enrichment_df['HomeTeam'] = enrichment_df['HomeTeam'].apply(NameNormalizer.normalize)
    enrichment_df['AwayTeam'] = enrichment_df['AwayTeam'].apply(NameNormalizer.normalize)
    
    enrichment_df['MergeKey'] = enrichment_df['HomeTeam'] + "_" + enrichment_df['AwayTeam']
    print("Sample Odds Keys:", enrichment_df['MergeKey'].head().tolist())

else:
    print("Odds DB not found")
    enrichment_df = pd.DataFrame()

# 2. Mock Fixture (Sassuolo vs Juventus)
# Simulating what FixturesFetcher gets
data = [{'HomeTeam': 'Sassuolo', 'AwayTeam': 'Juventus', 'Div': 'I1'}, 
        {'HomeTeam': 'West Ham', 'AwayTeam': "Nott'm Forest", 'Div': 'E0'}]
final_df = pd.DataFrame(data)

# Normalize Fixtures (as in upcoming.py)
final_df['HomeTeam'] = final_df['HomeTeam'].apply(NameNormalizer.normalize)
final_df['AwayTeam'] = final_df['AwayTeam'].apply(NameNormalizer.normalize)
final_df['MergeKey'] = final_df['HomeTeam'] + "_" + final_df['AwayTeam']
print("\nSample Fixture Keys:", final_df['MergeKey'].tolist())

# 3. Perform Merge (as in upcoming.py)
odds_cols = [c for c in enrichment_df.columns if c.startswith('B365') and c not in ['MergeKey']]
print(f"\nMerging {len(odds_cols)} columns: {odds_cols}")

if not enrichment_df.empty:
    merged = final_df.merge(enrichment_df[['MergeKey'] + odds_cols], on='MergeKey', how='left', suffixes=('', '_api'))
    
    # Check Result
    print("\nMerged Result:")
    print(merged[['MergeKey'] + odds_cols])
    
    if 'B365_Over1.5' in merged.columns and not merged['B365_Over1.5'].isna().all():
        print("\n✅ SUCCESS: B365_Over1.5 found and populated!")
    else:
        print("\n❌ FAILURE: B365_Over1.5 missing or NaN.")
else:
    print("Skipping merge (no odds)")
