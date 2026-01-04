
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

import pandas as pd
import numpy as np
from src.engine.strategies import PREMATCH_PATTERNS
from src.data.loader import DataLoader
import streamlit as st

# Mock Streamlit for CLI usage if needed, or just standard script
# We can run this via "python src/utils/backtester_strategies.py"

def run_strategy_backtest():
    print("Loading Data...")
    loader = DataLoader()
    # Mock streamlit cache doesn't exist here, so just call fetch
    # We load major leagues for testing
    leagues = ["E0", "SP1", "D1", "I1", "F1", "SP2", "E1"] 
    seasons = ["2324", "2425"]
    data = loader.fetch_data(leagues, seasons)
    
    if data.empty:
        print("No data found.")
        return

    print(f"Data Loaded: {len(data)} matches.")
    
    # Pre-process Data
    data['Date'] = pd.to_datetime(data['Date'], dayfirst=True)
    data = data.sort_values('Date')
    
    results = []
    
    # Tracking History
    # Structure: {Team: [matches...]}
    team_history = {}
    # Ref History: {Ref: [cards...]}
    ref_history = {}
    
    print("Running Event-Driven Backtest (Splits + Referee)...")
    
    for idx, row in data.iterrows():
        home = row['HomeTeam']
        away = row['AwayTeam']
        match_date = row['Date']
        ref = row.get('Referee', None)
        
        # Helper to get stats
        def get_team_stats(team, venue_filter=None, n=5):
            hist = team_history.get(team, [])
            if not hist: return None
            if venue_filter:
                hist = [m for m in hist if m['Venue'] == venue_filter]
            if len(hist) < 3: return None
            recent = hist[-n:]
            # Avg Checks
            avg_gf = sum(m['GF'] for m in recent) / len(recent)
            avg_ga = sum(m['GA'] for m in recent) / len(recent)
            avg_pts = sum(m['Pts'] for m in recent) / len(recent)
            avg_shots = sum(m.get('Shots', 0) for m in recent) / len(recent)
            
            # Momentum / Form Details (Wins/Losses count in last n)
            wins = sum(1 for m in recent if m['Pts'] == 3)
            losses = sum(1 for m in recent if m['Pts'] == 0)
            
            # Frequency Metrics (New)
            # BTTS: Both scored > 0
            btts_count = sum(1 for m in recent if m['GF'] > 0 and m['GA'] > 0)
            btts_rate = btts_count / len(recent) if recent else 0
            
            # Over 2.5
            over25_count = sum(1 for m in recent if (m['GF'] + m['GA']) > 2.5)
            over25_rate = over25_count / len(recent) if recent else 0
            
            # Clean Sheet (GA == 0)
            cs_count = sum(1 for m in recent if m['GA'] == 0)
            cs_rate = cs_count / len(recent) if recent else 0
            
            # Failed Score
            failed_score_rate = sum(1 for m in recent if m['GF'] == 0) / len(recent) if recent else 0
            
            # PRO METRICS (StdDev, ZeroZero)
            avg_fouls = 0 # Placeholder if no fouls data
            
            # StdDev Goals (Volatility)
            import numpy as np
            if recent:
                goals_list = [m['GF'] + m['GA'] for m in recent]
                std_dev_goals = np.std(goals_list, ddof=1) if len(goals_list) > 1 else 0
                zero_zeros = sum(1 for m in recent if m['GF'] == 0 and m['GA'] == 0)
            else:
                std_dev_goals = 0
                zero_zeros = 0

            last_match_date = hist[-1]['Date']
            rest_days = (match_date - last_match_date).days
            return {
                'AvgGoalsFor': avg_gf,
                'AvgGoalsAgainst': avg_ga,
                'PPG': avg_pts,
                'AvgShots': avg_shots,
                'WinsLast5': wins,
                'LossesLast5': losses,
                'RestDays': rest_days,
                'BTTS_Rate': btts_rate,
                'Over25_Rate': over25_rate,
                'CleanSheet_Rate': cs_rate,
                'FailedScore_Rate': failed_score_rate,
                
                'StdDev_Goals': std_dev_goals,
                'ZeroZero_Count': zero_zeros,
                'AvgFouls': avg_fouls # Hard to get from minimal hist unless we store HF/AF
            }

        # Helper Ref Stats
        def get_ref_avg(ref_name):
            if not ref_name or ref_name not in ref_history: return 4.0 # Default fallback
            cards = ref_history[ref_name]
            if len(cards) < 3: return 4.0
            return sum(cards) / len(cards)

        h_stats = get_team_stats(home, venue_filter='H') 
        a_stats = get_team_stats(away, venue_filter='A')
        
        # Mocking Ref Avg
        ref_avg = get_ref_avg(ref)
        
        if h_stats and a_stats:
            analysis_row = {
                'HomeAvgGoalsFor': h_stats['AvgGoalsFor'],
                'HomeAvgGoalsAgainst': h_stats['AvgGoalsAgainst'],
                'AwayAvgGoalsFor': a_stats['AvgGoalsFor'],
                'AwayAvgGoalsAgainst': a_stats['AvgGoalsAgainst'],
                'HomePPG': h_stats['PPG'], 
                'AwayPPG': a_stats['PPG'],
                'HomeAvgShotsTargetFor': h_stats['AvgShots'],
                
                # Momentum
                'HomeWinsLast5': h_stats['WinsLast5'],
                'HomeLossesLast5': h_stats['LossesLast5'],
                'AwayWinsLast5': a_stats['WinsLast5'],
                'AwayLossesLast5': a_stats['LossesLast5'],
                
                'RestDays': h_stats['RestDays'],
                'RefAvgCards': ref_avg, # New Feature
                'FTHG': row['FTHG'],
                'FTAG': row['FTAG'],
                
                # Consistency (New)
                'HomeBTTS_Rate': h_stats['BTTS_Rate'],
                'AwayBTTS_Rate': a_stats['BTTS_Rate'],
                'HomeOver25_Rate': h_stats['Over25_Rate'],
                'AwayOver25_Rate': a_stats['Over25_Rate'],
                'HomeCleanSheet_Rate': h_stats['CleanSheet_Rate'],
                'AwayCleanSheet_Rate': a_stats['CleanSheet_Rate'],
                
                # PRO Metrics
                'HomeStdDevGoals': h_stats['StdDev_Goals'],
                'AwayStdDevGoals': a_stats['StdDev_Goals'],
                'HomeZeroZero_Count': h_stats['ZeroZero_Count'],
                'AwayZeroZero_Count': a_stats['ZeroZero_Count'],
                'HomeAvgFouls': h_stats['AvgFouls'],
                'AwayAvgFouls': a_stats['AvgFouls'],
                
                # xG Proxy
                'AwayAvgShotsTargetFor': a_stats['AvgShots'],
            }
            
            # Apply Strategies
            for strat_name, cond_func, target_func, odd_key in PREMATCH_PATTERNS:
                try:
                    # IMPORTANT: For "Tarjetas", we verify strictly Ref > 4.5
                    # I can hardcode this optimization HERE to test it
                    if "Tarjetas" in strat_name:
                         if ref_avg < 4.5: continue # Skip if Ref is lenient
                    
                    if cond_func(analysis_row):
                        is_win = target_func(row)
                        
                        # Get Odds with Fallback
                        odd = row.get(odd_key, 0)
                        if pd.isna(odd) or odd == 0:
                            # ESTIMATION for backtest verification
                            if ">1.5" in odd_key: odd = 1.30
                            elif ">3.5" in odd_key: odd = 2.10 # Cards/Goals
                            elif ">2.5" in odd_key: odd = 1.80
                            elif odd_key == "B365GG": odd = 1.75 # BTTS Avg
                            elif odd_key == "B365H": odd = row.get('B365H', 1.80) # should allow if missing?
                            
                            # If still 0, default to 1.0 (No PnL change)
                            if odd == 0: odd = 1.0 
                        
                        pnl = (odd - 1) if is_win else -1
                        if odd <= 1.0: pnl = 0 # Safety for no-odd estimate

                        results.append({
                            'Strategy': strat_name,
                            'Match': f"{home} vs {away}",
                            'Result': 'Win' if is_win else 'Loss',
                            'Win': 1 if is_win else 0,
                            'PnL': pnl,
                            'Odds': odd
                        })
                except Exception:
                    pass
        
        # 2. Update History
        # Home Update
        home_cards = row.get('HY', 0) + row.get('HR', 0) # Home Yellow + Red? Usually HY, HR columns
        # Check columns existence
        if 'HY' not in row: home_cards = 0 # Safety
        
        if home not in team_history: team_history[home] = []
        team_history[home].append({
            'Date': match_date, 'Venue': 'H', 'GF': row['FTHG'], 'GA': row['FTAG'],
            'Pts': 3 if row['FTR'] == 'H' else (1 if row['FTR'] == 'D' else 0),
            'Shots': row.get('HST', 0)
        })
        
        # Away Update
        away_cards = row.get('AY', 0) + row.get('AR', 0)
        if 'AY' not in row: away_cards = 0
        
        if away not in team_history: team_history[away] = []
        team_history[away].append({
            'Date': match_date, 'Venue': 'A', 'GF': row['FTAG'], 'GA': row['FTHG'],
            'Pts': 3 if row['FTR'] == 'A' else (1 if row['FTR'] == 'D' else 0),
            'Shots': row.get('AST', 0)
        })
        
        # Ref Update
        if ref:
            total_cards = home_cards + away_cards
            if ref not in ref_history: ref_history[ref] = []
            ref_history[ref].append(total_cards)

    # Summary
    res_df = pd.DataFrame(results)
    if res_df.empty:
        print("No trades generated.")
        return

    print("\n--- Strategy Performance (Optimized: Splits + Ref Check) ---")
    summary = res_df.groupby('Strategy').agg({
        'PnL': 'sum',
        'Win': 'mean',
        'Match': 'count'
    }).rename(columns={'Win': 'WinRate', 'Match': 'Trades'})
    
    summary['ROI'] = (summary['PnL'] / summary['Trades']) * 100
    
    # Format for display
    print(summary.to_string(formatters={
        'WinRate': '{:.1%}'.format, 
        'ROI': '{:.1f}%'.format,
        'PnL': '{:.2f}'.format
    })) # Full Table

    # Summary
    res_df = pd.DataFrame(results)
    if res_df.empty:
        print("No trades generated.")
        return

    print("\n--- Strategy Performance (Baseline) ---")
    summary = res_df.groupby('Strategy').agg({
        'PnL': 'sum',
        'Win': 'mean',
        'Match': 'count'
    }).rename(columns={'Win': 'WinRate', 'Match': 'Trades'})
    
    summary['ROI'] = summary['PnL'] / summary['Trades']
    
    print(summary)
    
if __name__ == "__main__":
    run_strategy_backtest()
