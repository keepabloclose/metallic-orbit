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
            
            corners_for = row['HC'] if is_home and 'HC' in row else (row['AC'] if 'AC' in row else 0)
            corners_against = row['AC'] if is_home and 'AC' in row else (row['HC'] if 'HC' in row else 0)
            total_corners = corners_for + corners_against
            
            cards = row['HY'] + row['HR'] if is_home and 'HY' in row else (row['AY'] + row['AR'] if 'AY' in row else 0)
            
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
                'Result': 'W' if goals_for > goals_against else ('D' if goals_for == goals_against else 'L')
            })
            
        df_stats = pd.DataFrame(stats).sort_values('Date', ascending=False) # Newest first
        
        # Helper to check formatted fraction
        def check_frequency(series, condition_func, label, n_matches=[10, 8, 7, 6, 5], min_ratio=0.7):
            found_trends = []
            # Sort N descending to prioritize longer streaks (User Request)
            n_matches = sorted(n_matches, reverse=True)
            
            for n in n_matches:
                subset = series.head(n)
                if len(subset) < n: continue
                
                count = subset.apply(condition_func).sum()
                ratio = count / n
                
                if ratio >= min_ratio:
                    found_trends.append(f"{label} L{count}/{n}")
                    break # Only take the smallest N that satisfies or largest? Usually largest N is more impressive if high ratio, but smallest N shows recent 'streak'.
                    # User example: "L7/8". Let's stick to checking if it holds for N.
                    
            return found_trends

        # 1. Goals Trends
        # Over 1.5
        t = check_frequency(df_stats['TotalGoals'], lambda x: x > 1.5, "+1.5 Goles Global")
        if t: trends.extend(t)
        
        # Over 2.5
        t = check_frequency(df_stats['TotalGoals'], lambda x: x > 2.5, "+2.5 Goles Global")
        if t: trends.extend(t)
        
        # Under 2.5
        t = check_frequency(df_stats['TotalGoals'], lambda x: x < 2.5, "-2.5 Goles Global")
        if t: trends.extend(t)

        # Team Goals (Scored)
        t = check_frequency(df_stats['GoalsFor'], lambda x: x >= 1, f"{team} marca Global")
        if t: trends.extend(t)
        
        # Team Goals (Conceded) - "Clean Sheet No" equivalent
        t = check_frequency(df_stats['GoalsAgainst'], lambda x: x >= 1, f"{team} encaja Global")
        if t: trends.extend(t)

        # 2. BTTS Trends
        t = check_frequency(df_stats['BTTS'], lambda x: x == True, "BTTS (Ambos Marcan) Global")
        if t: trends.extend(t)
        
        # 3. Corners Trends
        t = check_frequency(df_stats['Corners'], lambda x: x > 8.5, "+8.5 Córners Global")
        if t: trends.extend(t)
        
        t = check_frequency(df_stats['Corners'], lambda x: x > 9.5, "+9.5 Córners Global")
        if t: trends.extend(t)
        
        # 4. Result Trends
        # Unbeaten
        t = check_frequency(df_stats['Result'], lambda x: x in ['W', 'D'], f"{team} Invicto Global")
        if t: trends.extend(t)

        # 5. Side Specific (Home or Away)
        # We need to know if we want Home or Away trends. 
        # Usually we show Home trends if team is Home, Away if Away.
        # But we can also check the last N Home games irrespective of current.
        
        return trends

    def get_match_trends(self, home_team, away_team):
        """
        Returns trends for both teams relevant to the matchup.
        """
        home_trends = self.analyze_trends(home_team)
        away_trends = self.analyze_trends(away_team)
        
        # Filter/Format specifically?
        # For now return raw list
        return {
            'Home': home_trends,
            'Away': away_trends
        }

    def get_recent_form(self, team, n=5):
        """
        Returns a string representing recent form, e.g. "W-D-L-W-W".
        """
        team_matches = self.history[
            (self.history['HomeTeam'] == team) | 
            (self.history['AwayTeam'] == team)
        ].copy()
        
        if team_matches.empty:
            return "N/A"
            
        results = []
        for _, row in team_matches.iterrows():
            is_home = row['HomeTeam'] == team
            goals_for = row['FTHG'] if is_home else row['FTAG']
            goals_against = row['FTAG'] if is_home else row['FTHG']
            
            if goals_for > goals_against:
                results.append('W')
            elif goals_for == goals_against:
                results.append('D')
            else:
                results.append('L')
                
        # Sort by date desc (newest first)
        # Note: history is sorted asc in init, so team_matches is asc.
        # We want newest first for the string usually? Or oldest -> newest?
        # Usually form is read L5: Left=Oldest or Left=Newest?
        # Standard is often Left=Newest or specific notation. 
        # Let's do Newest -> Oldest (Left to Right) for "Recent Form" usually?
        # Actually standard can vary. Let's do Newest First (Left).
        
        results.reverse() 
        return "-".join(results[:n])
