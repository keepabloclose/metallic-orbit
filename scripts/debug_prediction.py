import sys
import os
import pandas as pd

sys.path.append(os.getcwd())

from src.data.loader import DataLoader
from src.data.upcoming import FixturesFetcher
from src.engine.predictor import Predictor

def debug():
    print(">>> INICIANDO DEBUG DE PREDICCIÓN...", flush=True)
    
    # 1. Load Historical Data Directly (Skip Fetcher for speed if local exists, but here we assume we need to use DataLoader)
    from src.data.loader import DataLoader
    loader = DataLoader()
    # Fetch all relevant seasons to ensure we find the team
    data = loader.fetch_data(
        leagues=['E0', 'SP1'], 
        seasons=['2425', '2526']
    )
    print(f"Datos Cargados: {len(data)} registros", flush=True)
    if 'Div' in data.columns:
        teams = data[data['Div'] == 'E0']['HomeTeam'].unique()
        man_teams = [t for t in teams if 'Man' in str(t) or 'Utd' in str(t) or 'United' in str(t)]
        print(f"Equipos 'Man/Utd' en Datos: {man_teams}", flush=True)
    else:
        print("ALERT: Div column missing, checking all teams")
        teams = data['HomeTeam'].unique()
        man_teams = [t for t in teams if 'Man' in str(t) or 'Utd' in str(t)]
        print(f"Equipos 'Man/Utd' en TODO: {man_teams}", flush=True)
    
    predictor = Predictor(data)
    # print("Skipping Predictor init to debug data...", flush=True)

    # 3. Test Prediction
    teams_to_check = [
        ('Man Utd', 'Newcastle')
    ]
    
    for h, a in teams_to_check:
        print(f"\n--- Probando: {h} vs {a} ---")
        
        # Check Stats availability
        h_norm = predictor.normalize_name(h)
        a_norm = predictor.normalize_name(a)
        print(f"Normalizados: '{h}' -> '{h_norm}', '{a}' -> '{a_norm}'")
        
        s_h = predictor.get_latest_stats(h_norm)
        s_a = predictor.get_latest_stats(a_norm)
        
        if s_h is None: print(f"❌ Falta Stats LOCAL: {h_norm}")
        else: 
            ppg = s_h.get('PPG', 0)
            gf = s_h.get('AvgGoalsFor', 0)
            print(f"✅ Stats Local OK ({h_norm}): PPG={ppg:.2f}, AvgGoalsFor={gf:.2f}")
        
        if s_a is None: print(f"❌ Falta Stats VISITANTE: {a_norm}")
        else: 
            ppg = s_a.get('PPG', 0)
            gf = s_a.get('AvgGoalsFor', 0)
            print(f"✅ Stats Visitante OK ({a_norm}): PPG={ppg:.2f}, AvgGoalsFor={gf:.2f}")
        
        res = predictor.predict_match_safe(h, a)
        if res:
             print(f"   PRED ROW: HomeAvgGoalsFor={res.get('HomeAvgGoalsFor', 'N/A')}")
             print("✅ PREDICCIÓN ÉXITOSA")
        else:
            print("❌ PREDICCIÓN FALLIDA (Retorno Nulo)")

if __name__ == "__main__":
    try:
        debug()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[FATAL ERROR] {e}")
