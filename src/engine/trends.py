
import pandas as pd

class TrendsAnalyzer:
    def __init__(self, history_df):
        self.history = history_df.sort_values('Date', ascending=True)

    def analyze_trends(self, team, opponent=None):
        """
        Analyzes trends for a specific team.
        Returns a list of trend strings or dictionaries.
        """
        trends = []
        
        # Filter matches for the team
        team_matches = self.history[
            (self.history['HomeTeam'] == team) | 
            (self.history['AwayTeam'] == team)
        ].copy()
        
        if team_matches.empty:
            return []

        # Determine stats for the specific team in each match
        # We create a 'TeamStats' view
        stats = []
        for _, row in team_matches.iterrows():
            is_home = row['HomeTeam'] == team
            
            goals_for = row['FTHG'] if is_home else row['FTAG']
            goals_against = row['FTAG'] if is_home else row['FTHG']
            total_goals = goals_for + goals_against
            
            # Safe access for corners/cards
            corners_for = row.get('HC', 0) if is_home else row.get('AC', 0)
            corners_against = row.get('AC', 0) if is_home else row.get('HC', 0)
            total_corners = corners_for + corners_against
            
            cards = (row.get('HY', 0) + row.get('HR', 0)) if is_home else (row.get('AY', 0) + row.get('AR', 0))
            
            btts = (goals_for > 0) and (goals_against > 0)
            
            stats.append({
                'Date': row['Date'],
                'IsHome': is_home,
                'GoalsFor': goals_for,
                'GoalsAgainst': goals_against,
                'TotalGoals': total_goals,
                'Corners': total_corners,
                'Cards': cards,
                'BTTS': btts,
                'Result': 'W' if goals_for > goals_against else ('D' if goals_for == goals_against else 'L'),
                'Opponent': row['AwayTeam'] if is_home else row['HomeTeam'],
                'Venue': 'Home' if is_home else 'Away'
            })
            
        df_stats = pd.DataFrame(stats).sort_values('Date', ascending=False) # Newest first
        
        # Helper to check formatted fraction
        def check_frequency(series, condition_func, label, n_matches=[10, 8], min_ratio=0.75):
            found_trends = []
            n_matches = sorted(n_matches, reverse=True)
            
            for n in n_matches:
                subset = series.head(n)
                if len(subset) < n: continue
                
                count = subset.apply(condition_func).sum()
                ratio = count / n
                
                if ratio >= min_ratio:
                    found_trends.append(f"{label} L{count}/{n}")
                    break 
            return found_trends

        # 1. Goals Trends
        t = check_frequency(df_stats['TotalGoals'], lambda x: x > 1.5, "+1.5 Goles Global")
        if t: trends.extend(t)
        
        t = check_frequency(df_stats['TotalGoals'], lambda x: x > 2.5, "+2.5 Goles Global")
        if t: trends.extend(t)
        
        t = check_frequency(df_stats['TotalGoals'], lambda x: x < 2.5, "-2.5 Goles Global")
        if t: trends.extend(t)

        # Team Goals (Scored)
        t = check_frequency(df_stats['GoalsFor'], lambda x: x >= 1, f"{team} marca Global")
        if t: trends.extend(t)
        
        # BTTS Trends
        t = check_frequency(df_stats['BTTS'], lambda x: x == True, "BTTS (Ambos Marcan) Global")
        if t: trends.extend(t)
        
        # Result Trends
        t = check_frequency(df_stats['Result'], lambda x: x in ['W', 'D'], f"{team} Invicto Global")
        if t: trends.extend(t)

        return trends

    def get_match_trends(self, home_team, away_team):
        """
        Returns trends for both teams relevant to the matchup.
        """
        home_trends = self.analyze_trends(home_team)
        away_trends = self.analyze_trends(away_team)
        
        return {
            'Home': home_trends,
            'Away': away_trends
        }

    def get_recent_form(self, team, n=5):
        """
        Returns a string representing recent form, e.g. "W-D-L-W-W".
        """
        # Simplification: Reuse internal logic or just raw parsing
        # Re-implementing lightly to avoid circular deps or complex calls
        team_matches = self.history[
            (self.history['HomeTeam'] == team) | 
            (self.history['AwayTeam'] == team)
        ].copy()
        
        if team_matches.empty:
            return "N/A"
            
        # Sort desc
        team_matches['DateObj'] = pd.to_datetime(team_matches['Date'], dayfirst=True)
        team_matches = team_matches.sort_values('DateObj', ascending=False)
        
        results = []
        for _, row in team_matches.head(n).iterrows():
            is_home = row['HomeTeam'] == team
            goals_for = row['FTHG'] if is_home else row['FTAG']
            goals_against = row['FTAG'] if is_home else row['FTHG']
            
            if goals_for > goals_against:
                results.append('W')
            elif goals_for == goals_against:
                results.append('D')
            else:
                results.append('L')
                
        return "-".join(results)


class TrendSearcher:
    """
    Search engine for finding teams matching specific statistical criteria.
    Used in 'Buscador de Estadisticas' tab.
    """
    def __init__(self, data):
        self.data = data
        self.teams = pd.concat([data['HomeTeam'], data['AwayTeam']]).unique()
        
    def search_teams(self, stat_type, operator, value, last_n_matches=5, period="Full"):
        """
        Searches for teams matching the condition.
        Returns DataFrame with [Team, Div, Value, LastMatches]
        """
        results = []
        
        # Map stat_type to specific logic
        # 'Over25' -> Calculate % occurences
        # 'Goles' -> Calculate Average
        
        for team in self.teams:
            # Get Team Matches
            team_matches = self.data[
                (self.data['HomeTeam'] == team) | 
                (self.data['AwayTeam'] == team)
            ].copy()
            
            if len(team_matches) < last_n_matches:
                continue
                
            # Filter last N (Ensure Date sort)
            # Assumption: data might be partially sorted, strict sort here
            if 'Date' in team_matches.columns:
                 # Check if Date is datetime or string. Convert safely.
                 # Optimization: Do this conversion once globally if possible, but safe here.
                 team_matches['DateSort'] = pd.to_datetime(team_matches['Date'], dayfirst=True, errors='coerce')
                 team_matches = team_matches.sort_values('DateSort', ascending=False)
            
            recent = team_matches.head(last_n_matches)
            
            # Calculate Metric
            calculated_value = 0.0
            matches_details = [] # Store mini details
            
            values_list = []
            
            for _, row in recent.iterrows():
                is_home = row['HomeTeam'] == team
                
                # Fetch raw values based on Period and Type
                # Example: period='1H' -> Use HTHG/HTAG
                # For now, simplistic implementation assuming Full Time usually
                
                gf = row['FTHG'] if is_home else row['FTAG']
                ga = row['FTAG'] if is_home else row['FTHG']
                total = gf + ga
                
                val = 0
                if stat_type == 'Goles': val = gf
                elif stat_type == 'Goles Recibidos': val = ga
                elif stat_type == 'Over05': val = 1 if total > 0.5 else 0
                elif stat_type == 'Over15': val = 1 if total > 1.5 else 0
                elif stat_type == 'Over25': val = 1 if total > 2.5 else 0
                elif stat_type == 'BTTS': val = 1 if (gf > 0 and ga > 0) else 0
                elif stat_type == 'Córners': 
                    hc = row.get('HC', 0); ac = row.get('AC', 0)
                    val = hc if is_home else ac # Corners For
                
                values_list.append(val)
                
                matches_details.append({
                    'Date': row['Date'],
                    'Opponent': row['AwayTeam'] if is_home else row['HomeTeam'],
                    'Result': 'W' if gf > ga else ('D' if gf == ga else 'L'),
                    'Venue': 'Home' if is_home else 'Away',
                    'Value': val
                })
            
            # Aggregate
            if 'Over' in stat_type or 'BTTS' in stat_type:
                # Percentage
                calculated_value = sum(values_list) / len(values_list) * 100 # stored as 0-100? Or 0-1?
                # Threadhold in UI usually 60, 70 etc? 
                # Wait, UI input default is 1.5. If user selects Over25, threshold 1.5 makes no sense.
                # UI has "Valor (Umbral)". If searching Over25 > 80%?
                # Re-reading UI: Operator is >,<. Threshold is Number.
                # If Stat is "Over 2.5", and Threshold is "0.8" (80%)?
                # Or implies "Average Goals > 2.5"?
                pass
            else:
                # Average
                calculated_value = sum(values_list) / len(values_list)
            
            # Check Condition (handling % vs raw)
            # If Over/BTTS, calculated_value is 0.0-1.0. Threshold user input might be 1.5?
            # Adjust logic: If Stat is Boolean-like (Over/BTTS), we return Probability (0-1)
            # But user threshold is 1.5?
            # If user selects "Over 2.5", they likely mean "Team involved in > 2.5 goals" matches?
            # The tool calculates "Avg Goals" usually.
            # Let's handle 'Goles' (Avg) vs 'Over...' (%) differently.
            
            match_found = False
            if 'Over' in stat_type or 'BTTS' in stat_type:
                 # Boolean metric -> Avg = Probability
                 # If user puts threshold 1.5 for "Over 2.5", it's invalid. 
                 # Assume user knows: "Over 2.5" > 0.8 (80%)
                 if operator == '>': match_found = calculated_value > value
                 elif operator == '>=': match_found = calculated_value >= value
                 elif operator == '<': match_found = calculated_value < value
            else:
                 # Count metric (Goals, Corners)
                 if operator == '>': match_found = calculated_value > value
                 elif operator == '>=': match_found = calculated_value >= value
                 elif operator == '<': match_found = calculated_value < value

            if match_found:
                results.append({
                    'Team': team,
                    'Div': recent.iloc[0]['Div'] if 'Div' in recent.columns else 'Unk',
                    'Value': round(calculated_value, 2),
                    'LastMatches': matches_details
                })
                
        return pd.DataFrame(results)
