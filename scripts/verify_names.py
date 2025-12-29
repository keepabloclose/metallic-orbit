import pandas as pd
import sys
import os
import difflib

# Add project root to path
sys.path.append(os.getcwd())

from src.data.loader import DataLoader
from src.data.upcoming import FixturesFetcher

def verify_names():
    print(">>> Diagnosticando Nombres de Equipos...")
    
    # 1. Load History (Reference)
    loader = DataLoader()
    leagues = ['SP1', 'E0']
    seasons = ['2324'] # Just need recent season for names
    print("Cargando Histórico (SP1, E0)...")
    history = loader.fetch_data(leagues, seasons)
    
    if history.empty:
        print("ERROR: No historical data loaded.")
        return

    hist_teams_sp1 = set(history[history['League'] == 'SP1']['HomeTeam'].unique())
    hist_teams_e0 = set(history[history['League'] == 'E0']['HomeTeam'].unique())
    
    print(f"Equipos Históricos SP1: {len(hist_teams_sp1)}")
    print(f"Equipos Históricos E0: {len(hist_teams_e0)}")
    
    # 2. Load Upcoming
    fetcher = FixturesFetcher()
    print("Cargando Fixtures (SP1, E0)...")
    upcoming = fetcher.fetch_upcoming(['SP1', 'E0'])
    
    if upcoming.empty:
        print("ERROR: No upcoming fixtures found.")
        return
        
    upc_teams_sp1 = set(upcoming[upcoming['Div'] == 'SP1']['HomeTeam'].unique())
    upc_teams_e0 = set(upcoming[upcoming['Div'] == 'E0']['HomeTeam'].unique())
    
    print(f"Equipos Upcoming SP1: {len(upc_teams_sp1)}")
    print(f"Equipos Upcoming E0: {len(upc_teams_e0)}")
    
    # 3. Compare and find Mismatches
    def check_mismatch(hist_set, upc_set, label):
        print(f"\n--- {label} Analysis ---")
        common = hist_set.intersection(upc_set)
        missing_in_hist = upc_set - hist_set
        
        print(f"Coincidencias Exactas: {len(common)}")
        print(f"Faltan en Histórico (Mismatches): {len(missing_in_hist)}")
        
        if missing_in_hist:
            print("Detalle de discrepancias y sugerencias:")
            for team in missing_in_hist:
                # Find closest match
                matches = difflib.get_close_matches(team, hist_set, n=1, cutoff=0.6)
                candidate = matches[0] if matches else "???"
                print(f"   '{team}'  --> Sugerencia: '{candidate}'")

    check_mismatch(hist_teams_sp1, upc_teams_sp1, "La Liga (SP1)")
    check_mismatch(hist_teams_e0, upc_teams_e0, "Premier League (E0)")

if __name__ == "__main__":
    verify_names()
