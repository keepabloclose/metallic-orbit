
import sys
import os
import pandas as pd

# Path setup
sys.path.append(os.getcwd())

from src.dashboard.app import load_data
from src.engine.trends_scanner import TrendScanner

# load_data in app.py caches, so we might hit cache. 
# It applies NameNormalizer.
print("Loading data for SP1 (2324, 2425)...")
try:
    # app.load_data signature: load_data(leagues, seasons, version=4)
    data = load_data(['SP1'], ['2324', '2425'], version=4)
    print(f"Loaded {len(data)} matches.")
except Exception as e:
    print(f"Error loading data: {e}")
    exit()

# Check Getafe
team = "Getafe" # Normalized expected
print(f"Analyzing team: {team}")

# Filter history manual check
start_date = pd.to_datetime('2024-08-01')
recent_matches = data[
    ((data['HomeTeam'] == team) | (data['AwayTeam'] == team)) &
    (data['Date'] > start_date)
]
print(f"Getafe matches in 24/25 season: {len(recent_matches)}")
if not recent_matches.empty:
    print(recent_matches[['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']].head())

# Check Seasons
if 'Season' in data.columns:
    print(f"Seasons loaded: {data['Season'].unique()}")

# Check Getafe Variants
print("Searching for 'Getafe' in HomeTeam...")
variants = data[data['HomeTeam'].str.contains('Getafe', case=False, na=False)]['HomeTeam'].unique()
print(f"Variants found: {variants}")

# Check Getafe
team = "Getafe" # Normalized expected
print(f"Analyzing team: {team}")

# Filter history manual check
start_date = pd.to_datetime('2024-08-01')
recent_matches = data[
    ((data['HomeTeam'] == team) | (data['AwayTeam'] == team)) &
    (data['Date'] > start_date)
]
print(f"Getafe matches in 24/25 season (normalized 'Getafe'): {len(recent_matches)}")
if not recent_matches.empty:
    print(recent_matches[['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']].head())
    
# EXIT prior to scanner to avoid crash
exit()
