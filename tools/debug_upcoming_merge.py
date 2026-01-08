import sys
import os
import pandas as pd

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))
sys.path.append(os.getcwd())

from src.data.upcoming import FixturesFetcher

print("🧪 DEBUG: Testing FixturesFetcher Merge Logic...")

fetcher = FixturesFetcher()
# Fetch E0 (Premier League) as per user screenshot
df = fetcher.fetch_upcoming(leagues=['E0'])

if df.empty:
    print("❌ No matches returned!")
    sys.exit(1)

print(f"\n📊 Final DataFrame Shape: {df.shape}")
print(f"📋 Columns: {df.columns.tolist()}")

# Check for Arsenal
arsenal = df[df['HomeTeam'].str.contains('Arsenal', case=False, na=False)]

if not arsenal.empty:
    print("\n🔴 Arsenal Match Found:")
    cols = ['HomeTeam', 'AwayTeam', 'B365H', 'B365_BTTS_Yes', 'B365_Over1.5']
    # Filter valid cols
    valid_cols = [c for c in cols if c in df.columns]
    print(arsenal[valid_cols].to_string())
    
    if 'B365_BTTS_Yes' not in df.columns:
        print("\n❌ CRITICAL: B365_BTTS_Yes column is COMPLETELY MISSING!")
    elif arsenal['B365_BTTS_Yes'].isna().all():
        print("\n❌ CRITICAL: B365_BTTS_Yes column exists but is NaN for Arsenal!")
    else:
        print("\n✅ B365_BTTS_Yes is present and populated.")
else:
    print("\n❌ Arsenal match not found in upcoming fixtures.")
