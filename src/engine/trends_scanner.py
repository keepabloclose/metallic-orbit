
import pandas as pd
import numpy as np

class TrendScanner:
    def __init__(self):
        # Define atomic conditions to check
        # Label: (Function(row) -> bool, Threshold %)
        self.conditions = {
            'Over 1.5 Goles': (lambda r: (r['FTHG'] + r['FTAG']) > 1.5, 0.75),
            'Over 2.5 Goles': (lambda r: (r['FTHG'] + r['FTAG']) > 2.5, 0.65),
            'Under 2.5 Goles': (lambda r: (r['FTHG'] + r['FTAG']) < 2.5, 0.65),
            'Under 3.5 Goles': (lambda r: (r['FTHG'] + r['FTAG']) < 3.5, 0.75),
            'BTTS (Ambos Marcan)': (lambda r: (r['FTHG'] > 0) and (r['FTAG'] > 0), 0.65),
            'Clean Sheet (Portería a 0)': (lambda r, team: (r['HomeTeam'] == team and r['FTAG'] == 0) or (r['AwayTeam'] == team and r['FTHG'] == 0), 0.5),
            'Gana Partido': (lambda r, team: (r['HomeTeam'] == team and r['FTR'] == 'H') or (r['AwayTeam'] == team and r['FTR'] == 'A'), 0.7),
            'No Pierde (1X/X2)': (lambda r, team: not ((r['HomeTeam'] == team and r['FTR'] == 'A') or (r['AwayTeam'] == team and r['FTR'] == 'H')), 0.80)
        }
        
    def scan(self, team, historical_df, context='global', last_n=10):
        """
        Scans for trends for a specific team in a specific context (Home/Away/Global).
        Returns a list of trend strings, e.g. ["Over 1.5 L8/10", "BTTS L7/10"]
        """
        if historical_df.empty:
            return []
            
        # Filter games involving the team
        if context == 'home':
             df = historical_df[historical_df['HomeTeam'] == team].copy()
             suffix = "local"
        elif context == 'away':
             df = historical_df[historical_df['AwayTeam'] == team].copy()
             suffix = "visitante"
        else: # global
             df = historical_df[(historical_df['HomeTeam'] == team) | (historical_df['AwayTeam'] == team)].copy()
             suffix = "global"
             
        # Sort by date descending and take last N
        if 'Date' in df.columns:
            df = df.sort_values('Date', ascending=False)
            
        recent_games = df.head(last_n)
        if len(recent_games) < 3: # Min sample size
            return []
            
        found_trends = []
        
        # Check each condition
        for name, (func, threshold) in self.conditions.items():
            hits = 0
            total = len(recent_games)
            
            for _, row in recent_games.iterrows():
                # Some funcs need 'team' argument
                try:
                    # Introspect lambda arguments count is hard, try/except is easier
                    if 'team' in func.__code__.co_varnames:
                        res = func(row, team)
                    else:
                        res = func(row)
                        
                    if res: hits += 1
                except:
                    pass
            
            rate = hits / total
            if rate >= threshold:
                # Format: "Over 1.5 Goles L8/10 local"
                trend_str = f"{name} L{hits}/{total} {suffix}"
                found_trends.append({
                    'text': trend_str,
                    'rate': rate,
                    'type': 'good' if 'Under' not in name and 'Pierde' not in name else 'neutral' 
                    # Logic for color coding could be improved
                })
                
        # Sort by rate desc
        found_trends.sort(key=lambda x: x['rate'], reverse=True)
        return found_trends

