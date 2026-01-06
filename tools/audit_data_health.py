
import sys
import os
import pandas as pd
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.loader import DataLoader
from src.data.upcoming import FixturesFetcher

# Define Leagues to Check
LEAGUES = ['E0', 'SP1', 'SP2', 'D1', 'I1', 'F1', 'E1', 'P1', 'N1', 'B1', 'G1', 'SCO', 'T1'] 
# Added common request list: 
# E0=Prem, SP1=LaLiga, SP2=Segunda, D1=Bundesliga, I1=Serie A, F1=Ligue 1, 
# E1=Championship, P1=Portugal, N1=Netherlands, B1=Belgium, G1=Greece, SCO=Scotland, T1=Turkey

def audit_leagues():
    print("=== LEAGUE DATA HEALTH AUDIT ===")
    
    loader = DataLoader() # Defaults to use cache, BUT we want to know if cache is stale or empty? 
    # Actually, for audit, we want to see what the system SEES.
    
    fetcher = FixturesFetcher()
    
    results = []
    
    for league in LEAGUES:
        print(f"Checking {league}...")
        report = {'League': league, 'History': 'FAIL', 'Upcoming': 'FAIL', 'Odds': 'FAIL', 'Notes': ''}
        
        # 1. Check History (24/25)
        # Attempt fetch
        try:
            df = loader.fetch_data([league], ['2425'])
            if not df.empty:
                matches = len(df)
                last_date = df['Date'].max()
                report['History'] = f"OK ({matches} matches, Last: {last_date.date()})"
                
                # Check for NaNs in Goals
                nans = df[['FTHG', 'FTAG']].isna().sum().sum()
                if nans > 0:
                    report['Notes'] += f"History has {nans} missing scores. "
            else:
                report['History'] = "EMPTY"
        except Exception as e:
            report['History'] = f"ERROR: {e}"

        # 2. Check Upcoming
        try:
            up_df = fetcher.fetch_upcoming([league])
            if not up_df.empty:
                future_matches = len(up_df)
                report['Upcoming'] = f"OK ({future_matches} matches)"
                
                # Check Odds Presence
                odds_cols = [c for c in up_df.columns if 'B365' in c or 'Avg' in c]
                if not odds_cols:
                    report['Odds'] = "MISSING"
                else:
                    # Check if they are non-null
                    odds_ok = up_df['B365H'].notna().sum()
                    report['Odds'] = f"Partial ({odds_ok}/{future_matches})" if odds_ok < future_matches else "OK"
            else:
                report['Upcoming'] = "EMPTY_OR_FAIL"
                report['Odds'] = "N/A"
        except Exception as e:
            report['Upcoming'] = f"ERROR: {e}"
            
        results.append(report)
        print(f"  -> History: {report['History']} | Upcoming: {report['Upcoming']}")

    print("\n=== AUDIT SUMMARY ===")
    res_df = pd.DataFrame(results)
    print(res_df.to_string())
    
    with open("audit_report.txt", "w") as f:
        f.write(res_df.to_string())
        
if __name__ == "__main__":
    audit_leagues()
