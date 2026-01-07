import pandas as pd
import os

DB_PATH = "data_cache/odds_database.csv"

if not os.path.exists(DB_PATH):
    print("No DB")
else:
    df = pd.read_csv(DB_PATH)
    over_cols = [c for c in df.columns if "Over" in c and "1.5" in c]
    print(f"Over 1.5 related columns: {over_cols}")
    
    # Check for Cadiz
    cadiz = df[df['HomeTeam'].str.contains("Cadiz", case=False)]
    if not cadiz.empty:
        print("\nCadiz Values:")
        for c in over_cols:
            print(f"  {c}: {cadiz.iloc[0].get(c)}")
            
    # List all over columns
    all_over = [c for c in df.columns if "Over" in c]
    print(f"\nAll Over Cols count: {len(all_over)}")
    # Print sample
    print(all_over[:10])
