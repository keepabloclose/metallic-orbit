import pandas as pd
import numpy as np

class StreakAnalyzer:
    def __init__(self, df):
        self.df = df.copy()
        
    def _get_team_matches(self):
        """
        Transforms the main dataframe into a long format where each row is a team-match.
        Includes Goals, Corners, and Cards.
        """
        # Define available columns to fetch if they exist
        cols = ['Date', 'Div', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR']
        extra_cols = ['HC', 'AC', 'HY', 'AY', 'HR', 'AR']
        cols_to_use = cols + [c for c in extra_cols if c in self.df.columns]
        
        df = self.df[cols_to_use].copy()
        
        # Prepare Map
        home_renames = {
            'HomeTeam': 'Team', 'FTHG': 'GoalsFor', 'FTAG': 'GoalsAgainst',
            'HC': 'CornersFor', 'AC': 'CornersAgainst',
            'HY': 'YellowsFor', 'AY': 'YellowsAgainst',
            'HR': 'RedsFor', 'AR': 'RedsAgainst'
        }
        away_renames = {
            'AwayTeam': 'Team', 'FTAG': 'GoalsFor', 'FTHG': 'GoalsAgainst',
            'AC': 'CornersFor', 'HC': 'CornersAgainst',
            'AY': 'YellowsFor', 'HY': 'YellowsAgainst',
            'AR': 'RedsFor', 'HR': 'RedsAgainst'
        }
        
        # HOME transform
        home = df.copy()
        home = home.rename(columns={k:v for k,v in home_renames.items() if k in home.columns})
        home['Opponent'] = df['AwayTeam']
        home['Venue'] = 'Home'
        home['Result'] = home['FTR'].map({'H': 'W', 'D': 'D', 'A': 'L'})
        
        # AWAY transform
        away = df.copy()
        away = away.rename(columns={k:v for k,v in away_renames.items() if k in away.columns})
        away['Opponent'] = df['HomeTeam']
        away['Venue'] = 'Away'
        away['Result'] = away['FTR'].map({'H': 'L', 'D': 'D', 'A': 'W'})
        
        matches = pd.concat([home, away], ignore_index=True).sort_values(['Team', 'Date'], ascending=[True, False])
        return matches

    def get_active_streaks(self):
        """
        Calculates active streaks for all teams.
        Returns a DataFrame with Team, StreakType, Count.
        """
        matches = self._get_team_matches()
        if matches.empty:
            return pd.DataFrame()

        streaks = []
        
        for team, group in matches.groupby('Team'):
            group = group.sort_values('Date', ascending=False) # Newest first
            
            # Helper to count streak
            def count_streak(condition_series):
                count = 0
                for val in condition_series:
                    if val:
                        count += 1
                    else:
                        break
                return count

            # Define conditions
            # 1. Winning Streak
            win_streak = count_streak(group['Result'] == 'W')
            if win_streak >= 3:
                streaks.append({'Team': team, 'Liga': group.iloc[0]['Div'], 'Tipo': 'Victorias Consecutivas', 'Cantidad': win_streak, 'Fecha Ultimo': group.iloc[0]['Date']})
                
            # 2. Unbeaten Streak (Not Loss)
            unbeaten_streak = count_streak(group['Result'] != 'L')
            if unbeaten_streak >= 5:
                 streaks.append({'Team': team, 'Liga': group.iloc[0]['Div'], 'Tipo': 'Partidos Sin Perder', 'Cantidad': unbeaten_streak, 'Fecha Ultimo': group.iloc[0]['Date']})
                 
            # 3. Losing Streak
            lose_streak = count_streak(group['Result'] == 'L')
            if lose_streak >= 3:
                streaks.append({'Team': team, 'Liga': group.iloc[0]['Div'], 'Tipo': 'Derrotas Consecutivas', 'Cantidad': lose_streak, 'Fecha Ultimo': group.iloc[0]['Date']})

            # 4. No Win Streak
            no_win_streak = count_streak(group['Result'] != 'W')
            if no_win_streak >= 5:
                streaks.append({'Team': team, 'Liga': group.iloc[0]['Div'], 'Tipo': 'Partidos Sin Ganar', 'Cantidad': no_win_streak, 'Fecha Ultimo': group.iloc[0]['Date']})

            # 5. Scoring Streak (GoalsFor > 0)
            scoring_streak = count_streak(group['GoalsFor'] > 0)
            if scoring_streak >= 5:
                streaks.append({'Team': team, 'Liga': group.iloc[0]['Div'], 'Tipo': 'Partidos Marcando', 'Cantidad': scoring_streak, 'Fecha Ultimo': group.iloc[0]['Date']})
                
            # 6. Conceding Streak (GoalsAgainst > 0)
            conceding_streak = count_streak(group['GoalsAgainst'] > 0)
            if conceding_streak >= 5:
                 streaks.append({'Team': team, 'Liga': group.iloc[0]['Div'], 'Tipo': 'Partidos Encajando', 'Cantidad': conceding_streak, 'Fecha Ultimo': group.iloc[0]['Date']})
                 
            # 7. Goal Streaks Loop (Total Over/Under)
            # Thresholds: 1.5, 2.5, 3.5
            for threshold in [1.5, 2.5, 3.5]:
                # Over Total
                streak_over = count_streak((group['GoalsFor'] + group['GoalsAgainst']) > threshold)
                if streak_over >= 4:
                     streaks.append({'Team': team, 'Liga': group.iloc[0]['Div'], 'Tipo': f'Más de {threshold} Goles (Total)', 'Cantidad': streak_over, 'Fecha Ultimo': group.iloc[0]['Date']})
                
                # Under Total
                streak_under = count_streak((group['GoalsFor'] + group['GoalsAgainst']) < threshold)
                if streak_under >= 5:
                     streaks.append({'Team': team, 'Liga': group.iloc[0]['Div'], 'Tipo': f'Menos de {threshold} Goles (Total)', 'Cantidad': streak_under, 'Fecha Ultimo': group.iloc[0]['Date']})

                # Team Scored Over
                streak_team_over = count_streak(group['GoalsFor'] > threshold)
                if streak_team_over >= 3:
                     streaks.append({'Team': team, 'Liga': group.iloc[0]['Div'], 'Tipo': f'Equipo Marca > {threshold}', 'Cantidad': streak_team_over, 'Fecha Ultimo': group.iloc[0]['Date']})
        
        return pd.DataFrame(streaks).sort_values(['Tipo', 'Cantidad'], ascending=[True, False])

    def get_detailed_trends(self, team, n=6, context=None):
        """
        Generates detailed trend strings for a specific team.
        analyzes BOTH Global form (last n) AND Context form (last n Home/Away).
        
        context: 'Home' or 'Away' (optional, to filter venue specific trends)
        """
        all_matches = self._get_team_matches()
        
        # 1. Global Form
        global_matches = all_matches[all_matches['Team'] == team].sort_values('Date', ascending=False).head(n)
        
        # 2. Context Form (Home/Away)
        context_matches = pd.DataFrame()
        if context:
            context_matches = all_matches[(all_matches['Team'] == team) & (all_matches['Venue'] == context)].sort_values('Date', ascending=False).head(n)
            
        trends = []
        
        def analyze_subset(df, label_suffix):
            if len(df) < 3: return
            count = len(df)
            
            def check(mask, text):
                hits = mask.sum()
                if hits >= (count - 1) and hits > 0: # Max 1 miss
                    # Format: "+2.5 Goles L5/6 (Local)"
                    trends.append(f"{text} L{hits}/{count} {label_suffix}")

            # --- GOALS ---
            total_goals = df['GoalsFor'] + df['GoalsAgainst']
            check(total_goals > 1.5, "+1.5 Goles")
            check(total_goals > 2.5, "+2.5 Goles")
            check(total_goals < 3.5, "-3.5 Goles")
            check((df['GoalsFor'] > 0) & (df['GoalsAgainst'] > 0), "Ambos Marcan")
            check((df['GoalsFor'] == 0) | (df['GoalsAgainst'] == 0), "No Ambos Marcan")
            
            # --- TEAM GOALS ---
            check(df['GoalsFor'] >= 1, "Marca gol")
            check(df['GoalsFor'] >= 2, "Marca +1.5 goles")
            check(df['GoalsAgainst'] >= 1, "Encaja gol")
            check(df['GoalsAgainst'] == 0, "Portería a cero")
            
            # --- RESULTS ---
            check(df['Result'] != 'L', "Sin Perder")
            check(df['Result'] == 'W', "Gana")
            
            # --- CORNERS (Check existence) ---
            if 'CornersFor' in df.columns:
                total_corn = df['CornersFor'] + df['CornersAgainst']
                check(total_corn >= 9, "+8.5 Córners")
                check(total_corn >= 10, "+9.5 Córners")
                check(df['CornersFor'] >= 4, "Saca +3.5 Córners")
                check(df['CornersFor'] > df['CornersAgainst'], "Más Córners que rival")
                
            # --- CARDS ---
            if 'YellowsFor' in df.columns:
                total_cards = df['YellowsFor'] + df['YellowsAgainst'] # Approx
                check(total_cards >= 4, "+3.5 Tarjetas")
                check(df['YellowsFor'] >= 2, "Recibe +1.5 Tarjetas")
        
        # Analyze Global
        analyze_subset(global_matches, "(Global)")
        
        # Analyze Venue Specific (if significant)
        if not context_matches.empty:
            analyze_subset(context_matches, f"({context})")
            
        # Deduplicate: If Global covers it, prefer Global? Or show both?
        # Simple dedupe by text content
        unique_trends = sorted(list(set(trends)), key=lambda x: len(x), reverse=True) # Longest first? 
        # Actually default sort is fine.
        
        return unique_trends[:10] # Return top 10 relevant
