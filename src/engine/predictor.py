import pandas as pd
import numpy as np
from src.engine.ml_engine import MLEngine

class Predictor:
    def __init__(self, historical_df):
        self.history = historical_df.copy()
        
        # Initialize and Train ML Engine
        self.ml_engine = MLEngine()
        
        # Try to load cached model first
        if not self.ml_engine.load_model():
             if not self.history.empty:
                # Train immediately on load (fast enough for prototype)
                self.ml_engine.train_models(self.history)
                self.ml_engine.save_model() # Cache for next time
        self.history['Date'] = pd.to_datetime(self.history['Date'])
        self.history = self.history.sort_values('Date')
        
        # KEY FIX: Normalize names in the DataFrame itself so lookups match
        self.history['HomeTeam'] = self.history['HomeTeam'].apply(self.normalize_name)
        self.history['AwayTeam'] = self.history['AwayTeam'].apply(self.normalize_name)
        
    def normalize_name(self, name):
        """
        Normalizes team names to match the historical data.
        """
        if not isinstance(name, str):
            return str(name)
            
        name = name.strip()
        
        # Mapping from FixtureDownload/Common names TO Football-Data.co.uk names
        mapping = {
            # Spain
            'Rayo Vallecano': 'Vallecano',
            'CA Osasuna': 'Osasuna',
            'RCD Mallorca': 'Mallorca',
            'Athletic Club': 'Ath Bilbao',
            'Real Betis': 'Betis',
            'Real Sociedad': 'Sociedad',
            'RC Celta': 'Celta',
            'Celta de Vigo': 'Celta',
            'Deportivo Alaves': 'Alaves',
            'Spurs': 'Tottenham',
            'Tottenham Hotspur': 'Tottenham',
            'Man Utd': 'Man United',
            'Manchester United': 'Man United',
            'Man City': 'Man City',
            'Manchester City': 'Man City',
            'Wolves': 'Wolves',
            'Wolverhampton': 'Wolves',
            'Nottm Forest': "Nott'm Forest",
            'Nottingham Forest': "Nott'm Forest",
            'Sheffield Utd': 'Sheffield United',
            # Germany (D1)
            '1. FC Union Berlin': 'Union Berlin',
            '1. FSV Mainz 05': 'Mainz',
            'Mainz 05': 'Mainz',
            'FC St. Pauli': 'St Pauli',
            'St. Pauli': 'St Pauli',
            '1. FC Heidenheim 1846': 'Heidenheim',
            'Heidenheim': 'Heidenheim',
            '1. FC Kln': 'FC Koln',
            '1. FC Köln': 'FC Koln',
            'FC Köln': 'FC Koln',
            '1. FC Koln': 'FC Koln',
            'Bayer 04 Leverkusen': 'Leverkusen',
            'Bayer Leverkusen': 'Leverkusen',
            'Borussia Mönchengladbach': "M'gladbach",
            'Borussia Moenchengladbach': "M'gladbach",
            'Borussia M.Gladbach': "M'gladbach",
            'Borussia Monchengladbach': "M'gladbach",
            'M\'gladbach': "M'gladbach",
            'FC Bayern München': 'Bayern Munich',
            'FC Bayern Munchen': 'Bayern Munich',
            'FC Bayern Munich': 'Bayern Munich',
            'Bayern Munich': 'Bayern Munich',
            'VfL Wolfsburg': 'Wolfsburg',
            'FC Augsburg': 'Augsburg',
            'Eintracht Frankfurt': 'Ein Frankfurt',
            'TSG 1899 Hoffenheim': 'Hoffenheim',
            'VfL Bochum 1848': 'Bochum',
            'VfL Bochum': 'Bochum',
            'SV Werder Bremen': 'Werder Bremen',
            'Holstein Kiel': 'Holstein Kiel',
            'VfB Stuttgart': 'Stuttgart',
            'Borussia Dortmund': 'Dortmund',
            'RB Leipzig': 'RB Leipzig', # Usually matches

            # France (F1)
            'AS Monaco': 'Monaco',
            'FC Lorient': 'Lorient', 
            'Paris Saint-Germain': 'Paris SG',
            'Paris Saint Germain': 'Paris SG',
            'Paris SG': 'Paris SG',
            'Olympique de Marseille': 'Marseille',
            'Olympique Marseille': 'Marseille',
            'Olympique Lyonnais': 'Lyon',
            'Olympique Lyon': 'Lyon',
            'Stade Rennais': 'Rennes',
            'Stade Rennais FC': 'Rennes',
            'OGC Nice': 'Nice',
            'Lille OSC': 'Lille',
            'RC Lens': 'Lens',
            'Stade Brestois 29': 'Brest',
            'Stade de Reims': 'Reims',
            'Montpellier HSC': 'Montpellier',
            'RC Strasbourg Alsace': 'Strasbourg',
            'Toulouse FC': 'Toulouse',
            'FC Nantes': 'Nantes',
            'Le Havre AC': 'Le Havre',
            'AJ Auxerre': 'Auxerre',
            'AS Saint-Étienne': 'St Etienne',
            'AS Saint-Etienne': 'St Etienne',
            'Angers SCO': 'Angers',
            'Paris FC': 'Paris FC', # Check if likely F2
            'FC Metz': 'Metz',
            
            # Spain Encoding/Promoted
            'Deportivo Alavés': 'Alaves',
            'Deportivo AlavÚs': 'Alaves',
            'Alavés': 'Alaves',
            'Atlético de Madrid': 'Ath Madrid',
            'AtlÚtico de Madrid': 'Ath Madrid',
            'Atletico Madrid': 'Ath Madrid',
            'Girona FC': 'Girona',
            'Real Oviedo': 'Oviedo', # Might need SP2 data
            'Real Sociedad': 'Sociedad',
            
            # Germany Misc
            'SV Werder Bremen': 'Werder Bremen',
            'TSG Hoffenheim': 'Hoffenheim',
            'Sport-Club Freiburg': 'Freiburg',
            'SC Freiburg': 'Freiburg',
            'Hamburger SV': 'Hamburg',
        }
        return mapping.get(name, name)

    def get_latest_stats(self, team):
        """
        Finds the most recent match for a team and returns its stats (Rolling avgs, etc).
        """
        team = self.normalize_name(team)
        
        # Search in Home matches
        home_matches = self.history[self.history['HomeTeam'] == team]
        
        if team in ['Man United', 'Man Utd', 'Newcastle', 'Parma']:
            print(f"[DEBUG] get_latest_stats('{team}'): Found {len(home_matches)} home matches.")
            if not home_matches.empty:
                print(f"       Last match: {home_matches.iloc[-1]['Date']} vs {home_matches.iloc[-1]['AwayTeam']}")
            else:
                s_names = self.history['HomeTeam'].unique()
                matches = [x for x in s_names if 'Man' in str(x)]
                print(f"       Zero matches found. Similar teams in history: {matches}")
                # DEBUG REPR
                print(f"       Searching for: {repr(team)}")
                print(f"       Available: {[repr(m) for m in matches]}")
                
        # FALLBACK: If exact match failed, try containing
        if home_matches.empty:
             home_matches = self.history[self.history['HomeTeam'].astype(str).str.contains(team, regex=False, na=False)]
             if not home_matches.empty:
                 print(f"       [RECOVERY] Found {len(home_matches)} matches using fuzzy search for '{team}'")

        latest_home = home_matches.iloc[-1] if not home_matches.empty else None
        
        # Search in Away matches
        away_matches = self.history[self.history['AwayTeam'] == team]
        if away_matches.empty:
             away_matches = self.history[self.history['AwayTeam'].astype(str).str.contains(team, regex=False, na=False)]
             
        latest_away = away_matches.iloc[-1] if not away_matches.empty else None
        
        # We need the "Entry" stats for the NEXT match.
        # The 'HomeAvgGoalsFor' in the dataset is the avg *entering* that match.
        # So taking the last row is a good approximation of current form.
        # Ideally, we should re-calculate the rolling mean including the very last match result.
        # But for 'lo que sugiere el modelo', using the latest available rolling stat is sufficient.
        
        if latest_home is None and latest_away is None:
            return None
            
        # Determine which was more recent to get the true "Last Match Date"
        last_match_date = pd.Timestamp.min
        if latest_home is not None:
            last_match_date = max(last_match_date, latest_home['Date'])
        if latest_away is not None:
            last_match_date = max(last_match_date, latest_away['Date'])
            
        # Helper to get last N matches from history (Raw stats)
        # We need raw stats to calculate the NEW average entering the next game
        # The 'History' DF has 'FTHG', 'FTAG', 'HC', 'AC', etc.
        
        def get_team_rolling_stats(team_name, n=5):
            # Filter all matches for this team
            matches = self.history[(self.history['HomeTeam'] == team_name) | (self.history['AwayTeam'] == team_name)].sort_values('Date')
            
            if matches.empty:
                return {}
            
            # Take last n
            last_n = matches.tail(n)
            
            # Calculate means manually
            # Goals
            goals_for = last_n.apply(lambda x: x['FTHG'] if x['HomeTeam'] == team_name else x['FTAG'], axis=1).mean()
            goals_ag = last_n.apply(lambda x: x['FTAG'] if x['HomeTeam'] == team_name else x['FTHG'], axis=1).mean()
            
            # Shots Target
            st_for = last_n.apply(lambda x: x['HST'] if x['HomeTeam'] == team_name and 'HST' in x else (x['AST'] if 'AST' in x else 0), axis=1).mean()
            st_ag = last_n.apply(lambda x: x['AST'] if x['HomeTeam'] == team_name and 'HST' in x else (x['HST'] if 'HST' in x else 0), axis=1).mean()

            # Corners
            c_for = last_n.apply(lambda x: x['HC'] if x['HomeTeam'] == team_name and 'HC' in x else (x['AC'] if 'AC' in x else 0), axis=1).mean()
            c_ag = last_n.apply(lambda x: x['AC'] if x['HomeTeam'] == team_name and 'HC' in x else (x['HC'] if 'AC' in x else 0), axis=1).mean()
            
            # Cards
            cards_for = last_n.apply(lambda x: (x['HY'] + x['HR']) if x['HomeTeam'] == team_name and 'HY' in x else ((x['AY'] + x['AR']) if 'AY' in x else 0), axis=1).mean()
            
            # PPG (Form)
            pts = last_n.apply(lambda x: 3 if (x['HomeTeam'] == team_name and x['FTR'] == 'H') or (x['AwayTeam'] == team_name and x['FTR'] == 'A') else (1 if x['FTR'] == 'D' else 0), axis=1).mean()
            
            # Form Details (Wins/Losses count)
            wins = last_n.apply(lambda x: 1 if (x['HomeTeam'] == team_name and x['FTR'] == 'H') or (x['AwayTeam'] == team_name and x['FTR'] == 'A') else 0, axis=1).sum()
            losses = last_n.apply(lambda x: 1 if (x['HomeTeam'] == team_name and x['FTR'] == 'A') or (x['AwayTeam'] == team_name and x['FTR'] == 'H') else 0, axis=1).sum()

            # Attack Strength (Take latest known value from history if available)
            att_strength = 1.0
            latest_row = last_n.iloc[-1]
            if 'HomeAttackStrength' in latest_row and 'AwayAttackStrength' in latest_row:
                 if latest_row['HomeTeam'] == team_name:
                     att_strength = latest_row['HomeAttackStrength']
                 else:
                     att_strength = latest_row['AwayAttackStrength']
            
            # If column improperly named or missing, check alternative names or default
            if 'HomeAttackStrength' not in latest_row and 'AttackStrength' in latest_row: 
                 att_strength = latest_row['AttackStrength'] # If singular column

            # Calculate Consistency / Frequency Metrics (User Request)
            # BTTS Rate
            btts_rate = last_n.apply(lambda x: 1 if (x['FTHG'] > 0 and x['FTAG'] > 0) else 0, axis=1).mean()
            
            # Over 2.5 Rate
            over25_rate = last_n.apply(lambda x: 1 if (x['FTHG'] + x['FTAG'] > 2.5) else 0, axis=1).mean()
            
            # Clean Sheet Rate (My GoalsAgainst == 0)
            # If HomeTeam == team_name, GA is FTAG. If AwayTeam == team_name, GA is FTHG.
            cs_count = last_n.apply(lambda x: 1 if ((x['HomeTeam'] == team_name and x['FTAG'] == 0) or 
                                                    (x['AwayTeam'] == team_name and x['FTHG'] == 0)) else 0, axis=1).sum()
            cs_rate = cs_count / len(last_n) if len(last_n) > 0 else 0
            
            # Failed to Score Rate (For Paper Tigers)
            failed_score = last_n.apply(lambda x: 1 if ((x['HomeTeam'] == team_name and x['FTHG'] == 0) or
                                                        (x['AwayTeam'] == team_name and x['FTAG'] == 0)) else 0, axis=1).mean()
                                                        
            # Standard Deviation of Total Goals (Volatility)
            # Goals in match (whether home or away)
            match_goals = last_n.apply(lambda x: x['FTHG'] + x['FTAG'], axis=1)
            std_dev_goals = match_goals.std() if len(match_goals) > 1 else 0
            
            # Avg Fouls (if available) -> HF/AF columns
            # Note: football-data.co.uk usually has HF/AF
            avg_fouls = 0
            if 'HF' in last_n.columns:
                 avg_fouls = last_n.apply(lambda x: x['HF'] if x['HomeTeam'] == team_name else (x['AF'] if 'AF' in x else 0), axis=1).mean()
                 
            # Simple xG Proxy (Shots Target * 0.3) + (Shots * 0.1) ? 
            # Or just use AvgShotsTarget as 'Quality' metric.
            # User wants "Deficiencia Real" -> Low xG.
            # We'll expose 'AttackingQuality' = AvgShotsTarget
            
            # Check 0-0 Frequency (for "Regla del 0-0")
            draw_zeros = last_n.apply(lambda x: 1 if (x['FTHG'] == 0 and x['FTAG'] == 0) else 0, axis=1).sum()

            stats = {
                'AvgGoalsFor': goals_for,
                'AvgGoalsAgainst': goals_ag,
                'AvgShotsTargetFor': st_for,
                'AvgShotsTargetAgainst': st_ag,
                'AvgCornersFor': c_for,
                'AvgCornersAgainst': c_ag,
                'AvgCardsFor': cards_for,
                'AvgFouls': avg_fouls, # New
                'PPG': pts,
                'WinsLast5': wins,
                'LossesLast5': losses,
                'AttackStrength': att_strength,
                
                # Consistency Metrics
                'BTTS_Rate': btts_rate,
                'Over25_Rate': over25_rate,
                'CleanSheet_Rate': cs_rate,
                'FailedToScore_Rate': failed_score,
                'StdDev_Goals': std_dev_goals, # New
                'ZeroZero_Count': draw_zeros # New
            }
            return stats

        stats = get_team_rolling_stats(team)
        
        # Add Rest Days
        stats['RestDays'] = (pd.Timestamp.now() - last_match_date).days
        
        # Add Opp Difficulty Proxy
        last_row_h = self.history[self.history['HomeTeam'] == team].tail(1)
        last_row_a = self.history[self.history['AwayTeam'] == team].tail(1)
        
        last_row = None
        current_opp_diff = 1.35 # default
        
        if not last_row_h.empty and not last_row_a.empty:
            if last_row_h.iloc[-1]['Date'] > last_row_a.iloc[-1]['Date']:
                last_row = last_row_h.iloc[-1]
                current_opp_diff = last_row.get('HomeOppDifficulty', 1.35)
            else:
                last_row = last_row_a.iloc[-1]
                current_opp_diff = last_row.get('AwayOppDifficulty', 1.35)
        elif not last_row_h.empty:
            last_row = last_row_h.iloc[-1]
            current_opp_diff = last_row.get('HomeOppDifficulty', 1.35)
        elif not last_row_a.empty:
            last_row = last_row_a.iloc[-1]
            current_opp_diff = last_row.get('AwayOppDifficulty', 1.35)
            
            stats['OppDifficulty'] = current_opp_diff
        # Removed Placeholder overwrite: stats['AttackStrength'] = 1.0 
        
        return stats

    def get_ref_stats(self, ref_name):
        """
        Calculates rolling stats for a referee.
        """
        if not ref_name: return {'AvgCards': 4.0} # Default
        
        # Filter matches by referee
        # Note: 'Referee' column must exist. Football-Data.co.uk has it.
        if 'Referee' not in self.history.columns:
            return {'AvgCards': 4.0}
            
        ref_matches = self.history[self.history['Referee'] == ref_name]
        
        if ref_matches.empty:
             # Try fuzzy match?
             ref_matches = self.history[self.history['Referee'].astype(str).str.contains(ref_name, na=False, regex=False)]
             
        if ref_matches.empty:
            return {'AvgCards': 4.0}
            
        # Take last 20 matches for robust avg
        recent = ref_matches.tail(20)
        
        # Calculate Cards (HY + AY + HR + AR)
        # Note: HR/AR might be Red Cards, count as 1 or 2? Usually Total Cards = Y + R
        total_cards = 0, 
        count = 0
        
        cards_list = recent.apply(lambda x: x.get('HY',0) + x.get('AY',0) + x.get('HR',0) + x.get('AR',0), axis=1)
        avg_cards = cards_list.mean()
        
        return {'AvgCards': avg_cards, 'Matches': len(recent)}

    def predict_match(self, home_team, away_team, referee=None): # Added referee arg
        home_stats = self.get_latest_stats(home_team)
        away_stats = self.get_latest_stats(away_team)
        
        # Ref Stats
        ref_stats = self.get_ref_stats(referee)
        
        if not home_stats or not away_stats:
             print(f"[PREDICT] Stats missing for {home_team} or {away_team}")
             return {}

        # --- GLOBAL STATS (For Z-Score Baseline) ---
        # Ideally cached, but fast enough for now
        league_avg_hg = self.history['FTHG'].mean() if not self.history.empty else 1.5
        league_avg_ag = self.history['FTAG'].mean() if not self.history.empty else 1.2
        
        # --- Z-SCORE CALCULATION ---
        # Z = (TeamMetric - LeagueMetric) / TeamVolatility
        # Measures how "exceptional" the team is performing relative to valid variance.
        
        # Goals Z-Score
        h_std = home_stats.get('StdDev_Goals', 1.0)
        if h_std < 0.1: h_std = 0.5 # Avoid div/0 or huge spikes
        z_home_goals = (home_stats['AvgGoalsFor'] - league_avg_hg) / h_std
        
        a_std = away_stats.get('StdDev_Goals', 1.0)
        if a_std < 0.1: a_std = 0.5
        z_away_goals = (away_stats['AvgGoalsFor'] - league_avg_ag) / a_std
        
        # Dominance (xG) Z-Score
        # Baseline for Dominance: SOT(4.5)*3 + Cor(5)*1.5 + Shot(12)*0.5 ~ 13.5 + 7.5 + 6 = 27 (Roughly)
        # Check actual dominance means if possible, or use 0 as relative baseline if normalized?
        # Let's use the 'Dominance' values calculated in FeatureEngineer.
        # We need Team's StdDev of Dominance... FeatureEngineer didn't export 'StdDominance'.
        # We will use Goals StdDev as a proxy for volatility or 10.0 constant for now.
        z_home_xg = (home_stats.get('DominanceFor', 0) - 25.0) / 10.0 # Heuristic scaling
        z_away_xg = (away_stats.get('DominanceFor', 0) - 20.0) / 10.0

        # --- TRAP FLAGS ---
        # 1. Late Season & Close Rivals (Fear of Error)
        # Late Season: Month 4, 5 (April, May)
        idx_date = pd.Timestamp.now() # Prediction time
        is_late_season = idx_date.month in [4, 5]
        
        # Close Rivals: PPG Diff is small
        ppg_diff = abs(home_stats['PPG'] - away_stats['PPG'])
        is_close_rivals = ppg_diff < 0.3 # Approx 1 point diff over 3 games
        
        trap_fear_error = 1 if (is_late_season and is_close_rivals) else 0
        
        # 2. Fatigue (Invisible Tiredness)
        # Rest < 3 days (72 hours)
        h_tired = 1 if home_stats.get('RestDays', 7) < 3 else 0
        a_tired = 1 if away_stats.get('RestDays', 7) < 3 else 0
        trap_fatigue = h_tired + a_tired
        
        # 3. Style Clash (Tactical Line)
        # Check if both are "Defensive/Counter" (Low Possession/Shots)
        # Proxy: Low Shots Target For (< 3.5) AND Low Goals Against (< 1.2) = Park the Bus?
        h_defensive = home_stats['AvgShotsTargetFor'] < 3.5
        a_defensive = away_stats['AvgShotsTargetFor'] < 3.5
        trap_style_clash = 1 if (h_defensive and a_defensive) else 0

        # 4. Predict
        # We need to construct the 'row' expected by various strategies
        # AND by the ML Engine
        row = {
            'HomeTeam': home_team,
            'AwayTeam': away_team,
            'HomePPG': home_stats['PPG'],
            'AwayPPG': away_stats['PPG'],
            'HomeAvgGoalsFor': home_stats['AvgGoalsFor'],
            'HomeAvgGoalsAgainst': home_stats['AvgGoalsAgainst'],
            'AwayAvgGoalsFor': away_stats['AvgGoalsFor'],
            'AwayAvgGoalsAgainst': away_stats['AvgGoalsAgainst'],
            
            # Momentum / Form
            'HomeWinsLast5': home_stats['WinsLast5'],
            'HomeLossesLast5': home_stats['LossesLast5'],
            'AwayWinsLast5': away_stats['WinsLast5'],
            'AwayLossesLast5': away_stats['LossesLast5'],
            
            # Context
            'RestDays': home_stats.get('RestDays', 7), # Default
            'RefAvgCards': ref_stats['AvgCards'], # New Feature
            
            # Raw for strategies that might need it
            'HomeAvgCornersFor': home_stats['AvgCornersFor'],
            'AwayAvgCornersFor': away_stats['AvgCornersFor'],
            'HomeAvgShotsTargetFor': home_stats['AvgShotsTargetFor'],
            'AwayAvgShotsTargetFor': away_stats['AvgShotsTargetFor'],
            'HomeRestDays': home_stats['RestDays'],
            'AwayRestDays': away_stats['RestDays'],
            
            'HomeBTTS_Rate': home_stats.get('BTTS_Rate', 0),
            'AwayBTTS_Rate': away_stats.get('BTTS_Rate', 0),
            'HomeOver25_Rate': home_stats.get('Over25_Rate', 0),
            'AwayOver25_Rate': away_stats.get('Over25_Rate', 0),
            'HomeCleanSheet_Rate': home_stats.get('CleanSheet_Rate', 0),
            'AwayCleanSheet_Rate': away_stats.get('CleanSheet_Rate', 0),
            'HomeFailedScore_Rate': home_stats.get('FailedToScore_Rate', 0),
            'AwayFailedScore_Rate': away_stats.get('FailedToScore_Rate', 0),
            
            # PRO METRICS (StdDev, Fouls, ZeroZeros)
            'HomeStdDevGoals': home_stats.get('StdDev_Goals', 0),
            'AwayStdDevGoals': away_stats.get('StdDev_Goals', 0),
            'HomeAvgFouls': home_stats.get('AvgFouls', 0),
            'AwayAvgFouls': away_stats.get('AvgFouls', 0),
            'HomeZeroZero_Count': home_stats.get('ZeroZero_Count', 0),
            'AwayZeroZero_Count': away_stats.get('ZeroZero_Count', 0),
            
            # EVOLUTION 4.0 METRICS
            'HomeZScore_Goals': z_home_goals,
            'AwayZScore_Goals': z_away_goals,
            'HomeZScore_xG': z_home_xg,
            'AwayZScore_xG': z_away_xg,
            'Trap_FearError': trap_fear_error,
            'Trap_Fatigue': trap_fatigue,
            'Trap_StyleClash': trap_style_clash,
            'HomeDominance': home_stats.get('DominanceFor', 0),
            'AwayDominance': away_stats.get('DominanceFor', 0),
            'HomeGoalsCapped': home_stats.get('GoalsCappedFor', 0),
            'AwayGoalsCapped': away_stats.get('GoalsCappedFor', 0)
        }
        
        # Calculate Relative Strength dynamically (as it depends on the pair)
        # Formula: Attack / Opponent Defense (using Shots on Target as proxy)
        eps = 0.01
        row['HomeAttackStrength'] = row['HomeAvgShotsTargetFor'] / (away_stats['AvgShotsTargetAgainst'] + eps)
        row['AwayAttackStrength'] = row['AwayAvgShotsTargetFor'] / (home_stats['AvgShotsTargetAgainst'] + eps)
        
        # --- ML ENGINE PREDICTION ---
        # Now we have the full row with Home and Away stats, we can query the ML model
        ml_preds = self.ml_engine.predict_row(row)
        if ml_preds:
            row.update(ml_preds)
        
        # --- ODDS HANDLING ---
        # Prioritize Real Odds if available (scraped)
        if 'Real_B365H' in row and pd.notna(row['Real_B365H']):
            row['B365H'] = row['Real_B365H']
            row['B365D'] = row['Real_B365D']
            row['B365A'] = row['Real_B365A']
            # Estimate Over odds from Real odds? 
            # Or keep estimation for markets not scraped (Over 2.5 is hard to get sometimes)
            # For now, let's keep estimation for >2.5 but base it on real odds if possible?
            # Complexity: Just keep estimation for >2.5 independent or derived.
        else:
            # --- ESTIMATE ODDS (Fallback) ---
            # IMPROVEMENT: Use ML Probabilities if available, as they are smarter than PPG
            if 'ML_HomeWin' in row:
                # Convert from integer % (0-100) to float (0-1)
                h_prob = row['ML_HomeWin'] / 100.0
                d_prob = row['ML_Draw'] / 100.0
                a_prob = row['ML_AwayWin'] / 100.0
                
                # Normalize (in case they don't sum to exactly 1 due to separate models)
                total_prob = h_prob + d_prob + a_prob
                if total_prob > 0:
                    h_prob /= total_prob
                    d_prob /= total_prob
                    a_prob /= total_prob
                else:
                    # Fallback if ML failed
                    h_prob, d_prob, a_prob = 0.4, 0.3, 0.3
            else:
                # Fallback: PPG Ratio (Crude)
                h_p = row['HomePPG']
                a_p = row['AwayPPG']
                if h_p + a_p == 0:
                    h_prob, a_prob = 0.4, 0.35
                else:
                    h_prob = h_p / (h_p + a_p + 0.5) 
                    a_prob = a_p / (h_p + a_p + 0.5)
                d_prob = 1 - h_prob - a_prob
                if d_prob < 0.1: d_prob = 0.25

            # Apply pseudo-margin (bookie margin ~5-7%) to make them look like "Odds"
            # We add a slight margin to be realistic
            margin_adjustment = 0.95 
            
            # Avoid division by zero
            row['B365H'] = round(1 / (h_prob + 0.001) * margin_adjustment, 2)
            row['B365A'] = round(1 / (a_prob + 0.001) * margin_adjustment, 2)
            row['B365D'] = round(1 / (d_prob + 0.001) * margin_adjustment, 2)
        
        # 2. Over 2.5 Odds
        # Expected Goals
        exp_g = (row['HomeAvgGoalsFor'] + row['AwayAvgGoalsFor'] + 
                 row['HomeAvgGoalsAgainst'] + row['AwayAvgGoalsAgainst']) / 2
        
        # Poisson-ish approx for > 2.5 given Expectation
        # If ExpG = 2.5, Prob(>2.5) ~ 50% -> Odd 2.0
        # If ExpG = 3.5, Prob high -> Odd low
        # Heuristic: Odd = 2.0 * (2.5 / exp_g)^1.5
        if exp_g < 0.1: exp_g = 0.1
        
        est_odd_over = 2.0 * ((2.7 / exp_g) ** 1.2)
        if est_odd_over < 1.05: est_odd_over = 1.05
        
        row['B365>2.5'] = round(est_odd_over, 2)
        row['Avg>2.5'] = row['B365>2.5']
        
        # 3. Over 1.5 Odds (Derived from >2.5 or ExpG)
        # Usually much lower.
        # Heuristic from ExpG:
        est_odd_over15 = 1.0 + (est_odd_over - 1.0) * 0.45 # Rough scaling
        if est_odd_over15 < 1.01: est_odd_over15 = 1.01
        
        row['B365>1.5'] = round(est_odd_over15, 2)
        
        return row

    def analyze_upcoming(self, upcoming_df, patterns_analyzer):
        """
        upcoming_df: DataFrame with 'HomeTeam', 'AwayTeam', 'Date'
        patterns_analyzer: Instance of PatternAnalyzer (to reuse scanning logic? No, we need to adapt scanning)
        """
        predictions = []
        
        # We need to manually check conditions for these predicted rows
        # The PatternAnalyzer works on the WHOLE dataframe.
        # Here we only have single rows.
        
        # But we can extract the conditions from the main.py Patterns list
        # We need the user to pass the patterns list here or we define them.
        
        return [] # Placeholder, logic needs to be in main or passed in
