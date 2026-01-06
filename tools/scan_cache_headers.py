
import pandas as pd
import os
import glob

def scan_cache():
    print("Scanning data_cache for corrupted files...")
    files = glob.glob("data_cache/*.csv")
    for f in files:
        try:
            # Read just header/first row to check shape
            df = pd.read_csv(f, nrows=1) 
            # Note: nrows=1 reads header + 1 row. Columns = same.
            cols = len(df.columns)
            status = "✅"
            if cols > 200:
                status = "❌ CORRUPT"
            print(f"{f}: {cols} cols {status}")
        except Exception as e:
            print(f"{f}: Error {e}")

if __name__ == "__main__":
    scan_cache()
