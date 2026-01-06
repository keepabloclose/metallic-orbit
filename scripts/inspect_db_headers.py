
import pandas as pd
import os

db_path = "data_cache/odds_database.csv"
if os.path.exists(db_path):
    df = pd.read_csv(db_path)
    print("Columns found:")
    print(df.columns.tolist())
    print("\nFirst 3 rows:")
    print(df.head(3))
else:
    print("DB file not found.")
