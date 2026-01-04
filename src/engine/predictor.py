
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
        
        if 'Date' in self.history.columns:
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
            'Real Oviedo': 'Oviedo',
            'Real Sociedad': 'Sociedad',
            
            # Germany Misc
            'SV Werder Bremen': 'Werder Bremen',
            'TSG Hoffenheim': 'Hoffenheim',
            'Sport-Club Freiburg': 'Freiburg',
            'SC Freiburg': 'Freiburg',
            'Hamburger SV': 'Hamburg',
            # La Liga 2 (SP2) & Updates
            'Levante UD': 'Levante',
            'Real Zaragoza': 'Zaragoza',
            'Sporting de Gijón': 'Sp Gijon',
            'Sporting Gijon': 'Sp Gijon',
            'Sporting Gijón': 'Sp Gijon',
            'Racing de Santander': 'Santander',
            'Racing Santander': 'Santander',
            'SD Eibar': 'Eibar',
            'Granada CF': 'Granada',
            'Elche CF': 'Elche',
            'CD Tenerife': 'Tenerife',
            'Albacete Balompié': 'Albacete',
            'Burgos CF': 'Burgos',
            'FC Cartagena': 'Cartagena',
            'CD Castellón': 'Castellon',
            'CD Eldense': 'Eldense',
            'Cordoba CF': 'Cordoba',
            'SD Huesca': 'Huesca',
            'Malaga CF': 'Malaga',
            'Mirandes': 'Mirandes',
            'CD Mirandés': 'Mirandes',
            'Mirandés': 'Mirandes',
            'Racing Club Ferrol': 'Ferrol',
            'UD Almería': 'Almeria',
            'Cadiz CF': 'Cadiz',
            
            # User-Specific / Future / Copa Teams
            'Cultural Leonesa': 'Cultural Leonesa',
            'Real Sociedad B': 'Sociedad B',
            'AD Ceuta': 'Ceuta',
            'FC Andorra': 'Andorra',
            'S.D. Huesca': 'Huesca',
            'U.D. Las Palmas': 'Las Palmas',
            'Las Palmas': 'Las Palmas',
            'CD Leganes': 'Leganes',
            'Leganés': 'Leganes',
            'Deportivo': 'Dep. La Coruna', # Assumed
            'Racing de Santander': 'Santander', # Ensure match
            'Real Zaragoza': 'Zaragoza',

            # Getafe specific fix
            'Getafe CF': 'Getafe',
            'Rayo Vallecano': 'Vallecano',
            'Girona FC': 'Girona',
            
            # English Championship (E1)
            'Leeds United': 'Leeds',
            'Sunderland AFC': 'Sunderland',
            'West Bromwich Albion': 'West Brom',
            'West Bromwich': 'West Brom',
            'Blackburn Rovers': 'Blackburn',
            'Preston North End': 'Preston',
            'Sheffield Wednesday': 'Sheffield Weds',
            'Queens Park Rangers': 'QPR',
            'Coventry City': 'Coventry',
            'Stoke City': 'Stoke',
            'Hull City': 'Hull',
            'Middlesbrough FC': 'Middlesbrough',
            'Sheffield United': 'Sheffield United',
            'Burnley FC': 'Burnley',
            'Luton Town': 'Luton',
            'Norwich City': 'Norwich',
            'Watford FC': 'Watford',
            'Bristol City': 'Bristol City',
            'Cardiff City': 'Cardiff',
            'Derby County': 'Derby',
            'Oxford United': 'Oxford',
            'Portsmouth FC': 'Portsmouth',
            'Plymouth Argyle': 'Plymouth',
            'Swansea City': 'Swansea',
        }
        return mapping.get(name, name)

    def get_latest_stats(self, team):
        """
        Finds the most recent match for a team and returns its stats (Rolling avgs, etc).
        ROBUST VERSION: Returns League Average defaults if team not found.
        """
        team_norm = self.normalize_name(team)
        
        # Search in Home matches
        home_matches = self.history[self.history['HomeTeam'] == team_norm]
        
        # FALLBACK: If exact match failed, try containing
        if home_matches.empty:
             home_matches = self.history[self.history['HomeTeam'].astype(str).str.contains(team_norm, regex=False, na=False)]
             if not home_matches.empty:
                 # Found fuzzy match, use it
                 team_norm = home_matches.iloc[0]['HomeTeam'] 

        latest_home = home_matches.iloc[-1] if not home_matches.empty else None
        
        # Search in Away matches
        away_matches = self.history[self.history['AwayTeam'] == team_norm]
        if away_matches.empty:
             away_matches = self.history[self.history['AwayTeam'].astype(str).str.contains(team_norm, regex=False, na=False)]
             
        latest_away = away_matches.iloc[-1] if not away_matches.empty else None
        
        # Determine Last Match Date
        last_match_date = pd.Timestamp.min
        if latest_home is not None: last_match_date = max(last_match_date, latest_home['Date'])
        if latest_away is not None: last_match_date = max(last_match_date, latest_away['Date'])
        
        # If absolutely no history, return Default Stats (League Average Proxy)
        if latest_home is None and latest_away is None:
            # print(f"[WARN] No history for {team}. Using defaults.") 
            return self._get_default_stats()

        # Helper to get last N matches from history (Raw stats)
        def get_team_rolling_stats(team_name, n=5):
            # Filter all matches for this team
            matches = self.history[(self.history['HomeTeam'] == team_name) | (self.history['AwayTeam'] == team_name)].sort_values('Date')
            
            if matches.empty:
                return self._get_default_stats()
            
            # Take last n
            last_n = matches.tail(n)
            
            # Calculate means manually (robustly)
            def safe_mean(series):
                m = series.mean()
                return m if pd.notna(m) else 0.0

            # Goals
            goals_for = safe_mean(last_n.apply(lambda x: x['FTHG'] if x['HomeTeam'] == team_name else x['FTAG'], axis=1))
            goals_ag = safe_mean(last_n.apply(lambda x: x['FTAG'] if x['HomeTeam'] == team_name else x['FTHG'], axis=1))
            
            # Shots Target
            st_for = safe_mean(last_n.apply(lambda x: x.get('HST', 0) if x['HomeTeam'] == team_name else x.get('AST', 0), axis=1))
            st_ag = safe_mean(last_n.apply(lambda x: x.get('AST', 0) if x['HomeTeam'] == team_name else x.get('HST', 0), axis=1))

            # Corners
            c_for = safe_mean(last_n.apply(lambda x: x.get('HC', 0) if x['HomeTeam'] == team_name else x.get('AC', 0), axis=1))
            c_ag = safe_mean(last_n.apply(lambda x: x.get('AC', 0) if x['HomeTeam'] == team_name else x.get('HC', 0), axis=1))
            
            # Cards
            cards_for = safe_mean(last_n.apply(lambda x: (x.get('HY',0) + x.get('HR',0)) if x['HomeTeam'] == team_name else (x.get('AY',0) + x.get('AR',0)), axis=1))
            
            # Fouls
            avg_fouls = safe_mean(last_n.apply(lambda x: x.get('HF', 0) if x['HomeTeam'] == team_name else x.get('AF', 0), axis=1))
            
            # PPG (Form)
            pts = safe_mean(last_n.apply(lambda x: 3 if (x['HomeTeam'] == team_name and x['FTR'] == 'H') or (x['AwayTeam'] == team_name and x['FTR'] == 'A') else (1 if x['FTR'] == 'D' else 0), axis=1))
            
            # Form Details (Wins/Losses count)
            wins = last_n.apply(lambda x: 1 if (x['HomeTeam'] == team_name and x['FTR'] == 'H') or (x['AwayTeam'] == team_name and x['FTR'] == 'A') else 0, axis=1).sum()
            losses = last_n.apply(lambda x: 1 if (x['HomeTeam'] == team_name and x['FTR'] == 'A') or (x['AwayTeam'] == team_name and x['FTR'] == 'H') else 0, axis=1).sum()

            # Attack Strength fallback
            att_strength = 1.0
            
            # Consistency Metrics
            # BTTS Rate
            btts_rate = safe_mean(last_n.apply(lambda x: 1 if (x['FTHG'] > 0 and x['FTAG'] > 0) else 0, axis=1))
            
            # Over 2.5 Rate
            over25_rate = safe_mean(last_n.apply(lambda x: 1 if (x['FTHG'] + x['FTAG'] > 2.5) else 0, axis=1))
            
            # Clean Sheet Rate
            cs_count = last_n.apply(lambda x: 1 if ((x['HomeTeam'] == team_name and x['FTAG'] == 0) or 
                                                    (x['AwayTeam'] == team_name and x['FTHG'] == 0)) else 0, axis=1).sum()
            cs_rate = cs_count / len(last_n) if len(last_n) > 0 else 0
            
            # Failed to Score Rate
            failed_score = safe_mean(last_n.apply(lambda x: 1 if ((x['HomeTeam'] == team_name and x['FTHG'] == 0) or
                                                        (x['AwayTeam'] == team_name and x['FTAG'] == 0)) else 0, axis=1))
                                                        
            # Standard Deviation of Total Goals
            match_goals = last_n.apply(lambda x: x['FTHG'] + x['FTAG'], axis=1)
            std_dev_goals = match_goals.std() if len(match_goals) > 1 else 1.0 # Default 1.0 stability
            
            # Zero Zeros
            draw_zeros = last_n.apply(lambda x: 1 if (x['FTHG'] == 0 and x['FTAG'] == 0) else 0, axis=1).sum()

            stats = {
                'AvgGoalsFor': goals_for if goals_for > 0 else 1.0, # Prevent strict 0 for unknown
                'AvgGoalsAgainst': goals_ag if goals_ag > 0 else 1.2,
                'AvgShotsTargetFor': st_for if st_for > 0 else 3.5,
                'AvgShotsTargetAgainst': st_ag if st_ag > 0 else 4.0,
                'AvgCornersFor': c_for if c_for > 0 else 4.5,
                'AvgCornersAgainst': c_ag if c_ag > 0 else 5.0,
                'AvgCardsFor': cards_for if cards_for > 0 else 1.5,
                'AvgFouls': avg_fouls if avg_fouls > 0 else 10.0,
                'PPG': pts,
                'WinsLast5': wins,
                'LossesLast5': losses,
                'AttackStrength': att_strength,
                'BTTS_Rate': btts_rate,
                'Over25_Rate': over25_rate,
                'CleanSheet_Rate': cs_rate,
                'FailedToScore_Rate': failed_score,
                'StdDev_Goals': std_dev_goals,
                'ZeroZero_Count': draw_zeros
            }
            return stats

        stats = get_team_rolling_stats(team_norm)
        
        # Add Rest Days
        if last_match_date != pd.Timestamp.min:
            stats['RestDays'] = (pd.Timestamp.now() - last_match_date).days
        else:
            stats['RestDays'] = 7 # Default
        
        # Add Opp Difficulty Proxy (Default 1.35)
        stats['OppDifficulty'] = 1.35 
        
        return stats
        
    def _get_default_stats(self):
        """Returns baseline stats for an unknown team."""
        return {
            'AvgGoalsFor': 1.35, 'AvgGoalsAgainst': 1.35,
            'AvgShotsTargetFor': 4.0, 'AvgShotsTargetAgainst': 4.0,
            'AvgCornersFor': 5.0, 'AvgCornersAgainst': 5.0,
            'AvgCardsFor': 2.0, 'AvgFouls': 11.0,
            'PPG': 1.0, 'WinsLast5': 1, 'LossesLast5': 1,
            'AttackStrength': 1.0,
            'BTTS_Rate': 0.5, 'Over25_Rate': 0.5, 'CleanSheet_Rate': 0.25,
            'FailedToScore_Rate': 0.25,
            'StdDev_Goals': 1.5, 'ZeroZero_Count': 0,
            'RestDays': 7, 'OppDifficulty': 1.35
        }

    def get_ref_stats(self, ref_name):
        """
        Calculates rolling stats for a referee.
        """
        if not ref_name: return {'AvgCards': 4.0} # Default
        
        if 'Referee' not in self.history.columns:
            return {'AvgCards': 4.0}
            
        ref_matches = self.history[self.history['Referee'] == ref_name]
        
        if ref_matches.empty:
             ref_matches = self.history[self.history['Referee'].astype(str).str.contains(ref_name, na=False, regex=False)]
             
        if ref_matches.empty:
            return {'AvgCards': 4.0}
            
        recent = ref_matches.tail(20)
        
        cards_list = recent.apply(lambda x: x.get('HY',0) + x.get('AY',0) + x.get('HR',0) + x.get('AR',0), axis=1)
        avg_cards = cards_list.mean()
        
        return {'AvgCards': avg_cards if pd.notna(avg_cards) else 4.0, 'Matches': len(recent)}

    def predict_match_safe(self, home_team, away_team, referee=None, match_date=None): 
        home_stats = self.get_latest_stats(home_team)
        away_stats = self.get_latest_stats(away_team)
        
        # Ref Stats
        ref_stats = self.get_ref_stats(referee)
        
        # With new robustness, these should rarely be None, but good to check
        if not home_stats: home_stats = self._get_default_stats()
        if not away_stats: away_stats = self._get_default_stats()

        # --- GLOBAL STATS (For Z-Score Baseline) ---
        league_avg_hg = self.history['FTHG'].mean() if not self.history.empty else 1.5
        league_avg_ag = self.history['FTAG'].mean() if not self.history.empty else 1.2
        
        # --- Z-SCORE CALCULATION ---
        h_std = home_stats.get('StdDev_Goals', 1.0)
        if h_std < 0.1: h_std = 0.5
        z_home_goals = (home_stats['AvgGoalsFor'] - league_avg_hg) / h_std
        
        a_std = away_stats.get('StdDev_Goals', 1.0)
        if a_std < 0.1: a_std = 0.5
        z_away_goals = (away_stats['AvgGoalsFor'] - league_avg_ag) / a_std
        
        z_home_xg = (home_stats.get('DominanceFor', 25.0) - 25.0) / 10.0
        z_away_xg = (away_stats.get('DominanceFor', 20.0) - 20.0) / 10.0

        # --- TRAP FLAGS ---
        idx_date = pd.Timestamp.now()
        is_late_season = idx_date.month in [4, 5]
        ppg_diff = abs(home_stats['PPG'] - away_stats['PPG'])
        is_close_rivals = ppg_diff < 0.3
        trap_fear_error = 1 if (is_late_season and is_close_rivals) else 0
        
        h_tired = 1 if home_stats.get('RestDays', 7) < 3 else 0
        a_tired = 1 if away_stats.get('RestDays', 7) < 3 else 0
        trap_fatigue = h_tired + a_tired
        
        h_defensive = home_stats['AvgShotsTargetFor'] < 3.5
        a_defensive = away_stats['AvgShotsTargetFor'] < 3.5
        trap_style_clash = 1 if (h_defensive and a_defensive) else 0

        # 4. Predict
        row = {
            'HomeTeam': home_team,
            'AwayTeam': away_team,
            'HomePPG': home_stats['PPG'],
            'AwayPPG': away_stats['PPG'],
            'HomeAvgGoalsFor': home_stats['AvgGoalsFor'],
            'HomeAvgGoalsAgainst': home_stats['AvgGoalsAgainst'],
            'AwayAvgGoalsFor': away_stats['AvgGoalsFor'],
            'AwayAvgGoalsAgainst': away_stats['AvgGoalsAgainst'],
            
            'HomeWinsLast5': home_stats['WinsLast5'],
            'HomeLossesLast5': home_stats['LossesLast5'],
            'AwayWinsLast5': away_stats['WinsLast5'],
            'AwayLossesLast5': away_stats['LossesLast5'],
            
            'RestDays': home_stats.get('RestDays', 7),
            'RefAvgCards': ref_stats['AvgCards'],
            
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
            
            'HomeStdDevGoals': home_stats.get('StdDev_Goals', 0),
            'AwayStdDevGoals': away_stats.get('StdDev_Goals', 0),
            'HomeAvgFouls': home_stats.get('AvgFouls', 0),
            'AwayAvgFouls': away_stats.get('AvgFouls', 0),
            'HomeZeroZero_Count': home_stats.get('ZeroZero_Count', 0),
            'AwayZeroZero_Count': away_stats.get('ZeroZero_Count', 0),
            
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
        
        eps = 0.01
        row['HomeAttackStrength'] = row['HomeAvgShotsTargetFor'] / (away_stats['AvgShotsTargetAgainst'] + eps)
        row['AwayAttackStrength'] = row['AwayAvgShotsTargetFor'] / (home_stats['AvgShotsTargetAgainst'] + eps)
        
        # --- ML FEATURE ENGINEERING ---
        # Crucial: Must match exactly what MLEngine._calculate_expanding_stats produces
        row['HomeExpG_Raw'] = row['HomeAvgGoalsFor'] * row['AwayAvgGoalsAgainst']
        row['AwayExpG_Raw'] = row['AwayAvgGoalsFor'] * row['HomeAvgGoalsAgainst']
        
        row['IsTopClash'] = 1 if (row['HomePPG'] > 1.7 and row['AwayPPG'] > 1.7) else 0
        row['IsDefensiveLock'] = 1 if (row['HomeAvgGoalsAgainst'] < 1.0 and row['AwayAvgGoalsAgainst'] < 1.0) else 0

        # --- ML ENGINE PREDICTION ---
        ml_preds = self.ml_engine.predict_row(row)
        if ml_preds:
            row.update(ml_preds)
        
        # --- ODDS HANDLING ---
        if 'Real_B365H' in row and pd.notna(row['Real_B365H']):
            row['B365H'] = row['Real_B365H']
            row['B365D'] = row['Real_B365D']
            row['B365A'] = row['Real_B365A']
        else:
            if 'ML_HomeWin' in row:
                h_prob = row['ML_HomeWin'] / 100.0
                d_prob = row['ML_Draw'] / 100.0
                a_prob = row['ML_AwayWin'] / 100.0
                total_prob = h_prob + d_prob + a_prob
                if total_prob > 0:
                    h_prob /= total_prob
                    d_prob /= total_prob
                    a_prob /= total_prob
                else:
                    h_prob, d_prob, a_prob = 0.4, 0.3, 0.3
            else:
                h_p = row['HomePPG']
                a_p = row['AwayPPG']
                if h_p + a_p == 0:
                    h_prob, a_prob = 0.4, 0.35
                else:
                    h_prob = h_p / (h_p + a_p + 0.5) 
                    a_prob = a_p / (h_p + a_p + 0.5)
                d_prob = 1 - h_prob - a_prob
                if d_prob < 0.1: d_prob = 0.25

            margin_adjustment = 0.95 
            row['B365H'] = round(1 / (h_prob + 0.001) * margin_adjustment, 2)
            row['B365A'] = round(1 / (a_prob + 0.001) * margin_adjustment, 2)
            row['B365D'] = round(1 / (d_prob + 0.001) * margin_adjustment, 2)
        
        # 2. Over 2.5 Odds (Derived)
        exp_g = (row['HomeAvgGoalsFor'] + row['AwayAvgGoalsFor'] + 
                 row['HomeAvgGoalsAgainst'] + row['AwayAvgGoalsAgainst']) / 2
        
        if exp_g < 0.1: exp_g = 0.1
        est_odd_over = 2.0 * ((2.7 / exp_g) ** 1.2)
        if est_odd_over < 1.05: est_odd_over = 1.05
        
        row['B365>2.5'] = round(est_odd_over, 2)
        row['Avg>2.5'] = row['B365>2.5']
        
        # 3. Over 1.5 Odds
        est_odd_over15 = 1.0 + (est_odd_over - 1.0) * 0.45 
        if est_odd_over15 < 1.01: est_odd_over15 = 1.01
        
        row['B365>1.5'] = round(est_odd_over15, 2)
        
        return row

    def analyze_upcoming(self, upcoming_df, patterns_analyzer):
        """
        Scans upcoming matches for AI Strategies/Patterns.
        Returns a list of dictionaries with match info + found patterns.
        """
        results = []
        if upcoming_df.empty:
            return []
            
        print(f"Analyzing {len(upcoming_df)} matches for patterns...")
        
        for idx, row in upcoming_df.iterrows():
            # 1. Enrich Data (Calculate Features + Predict)
            # Use predict_match_safe logic but tailored for a row input if possible, 
            # or just pull the teams and call predict_match_safe
            
            home = row['HomeTeam']
            away = row['AwayTeam']
            date = row.get('Date', pd.Timestamp.now())
            
            try:
                # This returns a FULL row with features ('HomePPG', 'HomeAvgGoalsFor' etc.)
                # AND predictions ('B365H', 'est_odd_over' etc.)
                enriched_row = self.predict_match_safe(home, away, match_date=date)
                
                # Merge with original row data (e.g. Div, Time)
                # enriched_row is a dict, row is a Series
                full_data = row.to_dict()
                full_data.update(enriched_row)
                
                # 2. Check Patterns
                # patterns_analyzer.check_patterns expects a dict with all features
                found_patterns = patterns_analyzer.check_patterns(full_data)
                
                if found_patterns:
                    full_data['strategies'] = found_patterns
                    results.append(full_data)
                    
            except Exception as e:
                # Continue if one match fails (e.g. Missing Data handled by get_default_stats, but safe catch)
                print(f"Error analyzing {home} vs {away}: {e}")
                continue
                
        return results 
