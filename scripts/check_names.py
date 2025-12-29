
import sys
import os
sys.path.append(os.getcwd())

from src.data.loader import DataLoader
import pandas as pd

def check_names():
    print(">>> CARGANDO NOMBRES DE EQUIPOS...", flush=True)
    loader = DataLoader()
    # Fetch recent seasons
    df = loader.fetch_data(leagues=['E0', 'SP1'], seasons=['2425', '2324'])
    
    if df.empty:
        print("ERROR: No se cargaron datos.", flush=True)
        return

    print(f"Datos Cargados: {len(df)} filas.", flush=True)
    
    if 'Div' not in df.columns:
        print("ERROR: Columna 'Div' falta.", flush=True)
        return

    # Check Premier League (E0)
    e0_teams = sorted(df[df['Div'] == 'E0']['HomeTeam'].unique())
    print(f"\n--- PREMIER LEAGUE (E0) TEAMS ---")
    for t in e0_teams:
        print(f"'{t}'")
        
    # Check La Liga (SP1)
    sp1_teams = sorted(df[df['Div'] == 'SP1']['HomeTeam'].unique())
    print(f"\n--- LA LIGA (SP1) TEAMS ---")
    for t in sp1_teams:
        print(f"'{t}'")

if __name__ == "__main__":
    check_names()
