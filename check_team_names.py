
import pandas as pd
import sys
import os

sys.path.append(os.getcwd())
from src.data.loader import DataLoader

def check_names():
    loader = DataLoader()
    leagues = ['D1', 'F1']
    seasons = ['2425'] # Just current season
    df = loader.fetch_data(leagues, seasons)
    
    print("\n--- D1 (Bundesliga) Teams ---")
    d1_teams = sorted(df[df['Div'] == 'D1']['HomeTeam'].unique())
    print(d1_teams)
    
    print("\n--- F1 (Ligue 1) Teams ---")
    f1_teams = sorted(df[df['Div'] == 'F1']['HomeTeam'].unique())
    print(f1_teams)

if __name__ == "__main__":
    check_names()
