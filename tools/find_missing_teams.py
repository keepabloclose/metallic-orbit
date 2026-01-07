import pandas as pd
import sys
import os

sys.path.append(os.getcwd())
from src.data.loader import DataLoader

def search():
    print("--- Searching History DB ---")
    loader = DataLoader()
    # Ensure we load SP2 explicitly
    history = loader.fetch_data(['SP2'], ['2425', '2324', '2223', '2122', '2021'])
    
    teams = set(history['HomeTeam'].unique()) | set(history['AwayTeam'].unique())
    print(f"Loaded {len(teams)} teams from SP2.")
    print(sorted(list(teams)))

if __name__ == "__main__":
    search()
