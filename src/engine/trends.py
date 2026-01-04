

import pandas as pd

class TrendsAnalyzer:
    def __init__(self, history_df):
        self.history = history_df.sort_values('Date', ascending=True)

    def analyze_trends(self, team, context='global'):
        """
        Analyzes trends for a specific team with context (home/away/global).
        Returns a list of trend strings.
        """
        trends = []
        
        # 1. Get Global Matches
        global_matches = self.history[
            (self.history['HomeTeam'] == team) | 
            (self.history['AwayTeam'] == team)
        ].copy()
        
        if global_matches.empty: return []

        # 2. Extract Data Helper
        def extract_stats(matches, context_label):
            stats = []
            for _, row in matches.iterrows():
                is_home = row['HomeTeam'] == team
                
                # Basic Goals
                gf = row['FTHG'] if is_home else row['FTAG']
                ga = row['FTAG'] if is_home else row['FTHG']
                total_goals = gf + ga
                
                # Corners
                hc = row.get('HC', 0); ac = row.get('AC', 0)
                cf = hc if is_home else ac
                ca = ac if is_home else hc
                total_corners = cf + ca
                
                # Cards
                hy = row.get('HY', 0); ay = row.get('AY', 0)
                hr = row.get('HR', 0); ar = row.get('AR', 0)
                cards_f = (hy + hr) if is_home else (ay + ar)
                cards_a = (ay + ar) if is_home else (hy + hr)
                total_cards = cards_f + cards_a
                
                # Comparisons
                more_corners = cf > ca
                more_cards = cards_f > cards_a
                
                stats.append({
                    'TotalGoals': total_goals,
                    'GoalsFor': gf,
                    'GoalsAgainst': ga,
                    'TotalCorners': total_corners,
                    'CornersFor': cf,
                    'TotalCards': total_cards,
                    'CardsFor': cards_f,
                    'MoreCorners': more_corners,
                    'MoreCards': more_cards,
                    'BTTS': (gf > 0 and ga > 0)
                })
            return pd.DataFrame(stats)

        # 3. Analyze Global
        df_global = extract_stats(global_matches, "global")
        trends.extend(self._check_all_streaks(df_global, "global"))
        
        # 4. Analyze Context (Home/Away)
        if context == 'home':
            home_matches = global_matches[global_matches['HomeTeam'] == team]
            if not home_matches.empty:
                df_home = extract_stats(home_matches, "local")
                # Prioritize Local streaks by putting them first
                local_trends = self._check_all_streaks(df_home, "local")
                trends = local_trends + trends
                
        elif context == 'away':
            away_matches = global_matches[global_matches['AwayTeam'] == team]
            if not away_matches.empty:
                df_away = extract_stats(away_matches, "visitante")
                visit_trends = self._check_all_streaks(df_away, "visitante")
                trends = visit_trends + trends

        # Deduplicate preservation of order? 
        # Sets lose order. Let's keep list but dedup.
        seen = set()
        deduped = []
        for t in trends:
            if t not in seen:
                deduped.append(t)
                seen.add(t)
                
        return deduped

    def _check_all_streaks(self, df, label_suffix):
        """
        Runs adaptive streak checks on all relevant columns.
        """
        file_trends = []
        
        # Helper to format suffix
        suffix = f" {label_suffix}" if label_suffix != "global" else " global" # Always show context if user wants specific info
        if label_suffix == "global": suffix = " global"
        
        # 1. Goals
        file_trends.extend(self.check_adaptive_streak(df['TotalGoals'], "Goles", min_val_limit=1.5, suffix=suffix))
        file_trends.extend(self.check_adaptive_streak(df['GoalsFor'], "Goles Equipo", min_val_limit=0.5, suffix=suffix)) # e.g. Team Over 0.5
        
        # 2. Corners
        file_trends.extend(self.check_adaptive_streak(df['TotalCorners'], "Córners", min_val_limit=7.5, suffix=suffix))
        file_trends.extend(self.check_adaptive_streak(df['CornersFor'], "Córners Equipo", min_val_limit=3.5, suffix=suffix))
        
        # 3. Cards
        file_trends.extend(self.check_adaptive_streak(df['TotalCards'], "Tarjetas", min_val_limit=2.5, suffix=suffix))
        file_trends.extend(self.check_adaptive_streak(df['CardsFor'], "Tarjetas Equipo", min_val_limit=1.5, suffix=suffix))
        
        # 4. Comparisons (Boolean Streaks)
        # "Más córners que el rival" -> column 'MoreCorners' is boolean
        def check_bool_streak(col, desc):
            # Check L5, L6...
            for n in [5, 6, 7, 8, 9, 10]:
                subset = df[col].head(n)
                if len(subset) < n: continue
                hits = subset.sum()
                # 80% threshold
                if hits / n >= 0.8:
                    return [f"{desc} L{hits}/{n}{suffix}"]
            return []

        file_trends.extend(check_bool_streak('MoreCorners', "Más córners que el rival"))
        file_trends.extend(check_bool_streak('MoreCards', "Más tarjetas que el rival"))
        file_trends.extend(check_bool_streak('BTTS', "Ambos Marcan"))
        
        return file_trends

    def check_adaptive_streak(self, series, label_base, min_val_limit=1.5, suffix="", n_matches=[10, 8, 5]):
        """
        Refined Adaptive Streak: Checks Over X.
        """
        candidates = []
        for n in n_matches:
            subset = series.head(n)
            if len(subset) < n: continue
            
            min_v = subset.min() # Pure 100% streak
            
            # If 100% streak
            if min_v > min_val_limit:
                thresh = min_v - 0.5
                # Verify it's a "clean" number (e.g. 1.5, 2.5) if data is integer-like
                # But threshold is implicitly .5 for Over markets
                candidates.append({
                    'priority': thresh * n, # Score
                    'desc': f"+{thresh} {label_base} L{n}/{n}{suffix}"
                })
                
            # Allow 1 fail? (e.g. 9/10).
            # If n >= 8, allow 1 miss.
            if n >= 8:
                sorted_vals = sorted(subset.values)
                # Drop lowest
                min_v_partial = sorted_vals[1] # 2nd lowest
                if min_v_partial > min_val_limit:
                    thresh = min_v_partial - 0.5
                    candidates.append({
                         'priority': (thresh * n) - 5, # Penalty
                         'desc': f"+{thresh} {label_base} L{n-1}/{n}{suffix}"
                    })

        if not candidates: return []
        
        # Sort by priority
        candidates.sort(key=lambda x: x['priority'], reverse=True)
        return [candidates[0]['desc']]

    def get_match_trends(self, home_team, away_team):
        """
        Returns trends for both teams relevant to the matchup.
        """
        home_trends = self.analyze_trends(home_team, context='home')
        away_trends = self.analyze_trends(away_team, context='away')
        
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
        
        for team in self.teams:
            # Get Team Matches
            team_matches = self.data[
                (self.data['HomeTeam'] == team) | 
                (self.data['AwayTeam'] == team)
            ].copy()
            
            if len(team_matches) < last_n_matches:
                continue
                
            # Filter last N (Ensure Date sort)
            if 'Date' in team_matches.columns:
                 team_matches['DateSort'] = pd.to_datetime(team_matches['Date'], dayfirst=True, errors='coerce')
                 team_matches = team_matches.sort_values('DateSort', ascending=False)
            
            recent = team_matches.head(last_n_matches)
            
            # Calculate Metric
            values_list = []
            matches_details = []
            
            for _, row in recent.iterrows():
                is_home = row['HomeTeam'] == team
                
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
                    val = hc if is_home else ac 
                elif stat_type == 'Tiros':
                    hs = row.get('HS', 0); as_ = row.get('AS', 0)
                    val = hs if is_home else as_
                
                values_list.append(val)
                
                matches_details.append({
                    'Date': row['Date'],
                    'Opponent': row['AwayTeam'] if is_home else row['HomeTeam'],
                    'Result': 'W' if gf > ga else ('D' if gf == ga else 'L'),
                    'Venue': 'Home' if is_home else 'Away',
                    'Value': val
                })
            
            calculated_value = 0.0
            
            if 'Over' in stat_type or 'BTTS' in stat_type:
                # Percentage
                calculated_value = sum(values_list) / len(values_list)
            else:
                # Average
                calculated_value = sum(values_list) / len(values_list)
            
            match_found = False
            if 'Over' in stat_type or 'BTTS' in stat_type:
                 # Boolean metric -> Avg = Probability
                 # Logic for user intent > 1.5
                 # If user asks for Over 2.5 > 0.8 (Probability > 80%) ?
                 # Or if they ask for Over 2.5 > 1.5 (Impossible?)
                 # Assume they mean Probability > Value/100 or Value if Value < 1?
                 # Let's fix this interpretation: The UI asks for "Valor (Umbral)".
                 # If user puts 0.8, it fits probability.
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
