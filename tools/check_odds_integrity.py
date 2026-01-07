import pandas as pd
import os

DB_PATH = "data_cache/odds_database.csv"

if not os.path.exists(DB_PATH):
    print(f"No DB found at {DB_PATH}")
else:
    df = pd.read_csv(DB_PATH)
    print(f"Total Rows: {len(df)}")
    print("Columns:", df.columns.tolist())
    
    # Check for Cadiz or Las Palmas
    cadiz = df[df['HomeTeam'].str.contains("Cadiz", case=False) | df['AwayTeam'].str.contains("Cadiz", case=False)]
    
    if not cadiz.empty:
        print("\n--- Cadiz Match Data ---")
        cols_to_show = ['HomeTeam', 'AwayTeam', 'League'] + [c for c in df.columns if 'Over1.5' in c]
        print(cadiz[cols_to_show].to_string())
    else:
        print("\nCadiz not found in Odds DB.")

    # Check for Las Palmas
    palmas = df[df['HomeTeam'].str.contains("Las Palmas", case=False) | df['AwayTeam'].str.contains("Las Palmas", case=False)]
    if not palmas.empty:
        print("\n--- Las Palmas Match Data ---")
        cols_to_show = ['HomeTeam', 'AwayTeam', 'League'] + [c for c in df.columns if 'Over1.5' in c]
        print(palmas[cols_to_show].to_string())
