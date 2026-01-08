import pandas as pd
import numpy as np

class FeatureEngineer:
    def __init__(self, df):
        self.df = df.copy()
        # Ensure Date is datetime
        if 'Date' in self.df.columns:
            self.df['Date'] = pd.to_datetime(self.df['Date'], dayfirst=True)
            self.df = self.df.sort_values(['Date'])
        
        # --- CRITICAL FIX: Deduplicate Input to prevent Merge Explosion ---
        # If duplicates enter here, the subsequent left-joins (Home/Away stats) will square/cube them.
        initial_len = len(self.df)
        if 'HomeTeam' in self.df.columns and 'AwayTeam' in self.df.columns:
             self.df = self.df.drop_duplicates(subset=['HomeTeam', 'AwayTeam', 'Date'])
             if len(self.df) < initial_len:
                 print(f"FeatureEngineer: Dropped {initial_len - len(self.df)} duplicates at entry.")
        
    def add_rest_days(self, cup_schedule=None):
        """
        Calculates the number of days since the last match, including Cup competitions if provided.
        """
        print("Calculating Rest Days (inc. Cups)...")
        # Create a long format of matches to track team schedule
        home_games = self.df[['Date', 'HomeTeam']].rename(columns={'HomeTeam': 'Team'})
        away_games = self.df[['Date', 'AwayTeam']].rename(columns={'AwayTeam': 'Team'})
        
        schedule_parts = [home_games, away_games]
        
        if cup_schedule is not None and not cup_schedule.empty:
            # Ensure proper format for cup_schedule: Date, Team
            cup_df = cup_schedule[['Date', 'Team']].copy()
            schedule_parts.append(cup_df)
            
        all_games = pd.concat(schedule_parts).sort_values(['Team', 'Date']).drop_duplicates()
        
        all_games['LastMatch'] = all_games.groupby('Team')['Date'].shift(1)
        all_games['RestDays'] = (all_games['Date'] - all_games['LastMatch']).dt.days
        
        # Merge back to main dataframe
        # We need to be careful to map the correct rest days for Home and Away specific to that match
        # Mapping for HomeTeam
        self.df = self.df.merge(
            all_games[['Date', 'Team', 'RestDays']].rename(columns={'RestDays': 'HomeRestDays'}),
            left_on=['Date', 'HomeTeam'],
            right_on=['Date', 'Team'],
            how='left'
        ).drop(columns=['Team'])
        
        # Mapping for AwayTeam
        self.df = self.df.merge(
            all_games[['Date', 'Team', 'RestDays']].rename(columns={'RestDays': 'AwayRestDays'}),
            left_on=['Date', 'AwayTeam'],
            right_on=['Date', 'Team'],
            how='left'
        ).drop(columns=['Team'])
        
        # Fill NaN (first game of season) with a default large number (e.g., 7)
        self.df[['HomeRestDays', 'AwayRestDays']] = self.df[['HomeRestDays', 'AwayRestDays']].fillna(7)
        return self.df

    def add_rolling_stats(self, window=5):
        """
        Calculates rolling averages for goals, shots, fouls, etc.
        """
        print(f"Calculating Rolling Stats (Window={window})...")
        cols_to_roll = {
            'FTHG': 'HomeGoals', 'FTAG': 'AwayGoals',
            'HST': 'HomeShotsTarget', 'AST': 'AwayShotsTarget',
            'HF': 'HomeFouls', 'AF': 'AwayFouls',
            'HC': 'HomeCorners', 'AC': 'AwayCorners'
        }
        
        # We need to calculate these PER TEAM, regardless of whether they played Home or Away
        # This requires reconstructing a 'Team Performance' history
        
        # GUARD: If we don't have basic results (Goals), we can't calculate rolling stats.
        if 'FTHG' not in self.df.columns or 'FTAG' not in self.df.columns:
            print("FeatureEngineer: Missing FTHG/FTAG, skipping Rolling Stats.")
            return self.df

        # Expanded to include Cards (Yellow + Red)
        possible_cols = ['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'HST', 'AST', 'HF', 'AF', 'HC', 'AC', 'HY', 'AY', 'HR', 'AR']
        
        # Only select columns that actually exist in the dataframe
        cols_needed = [c for c in possible_cols if c in self.df.columns]
        
        # If critical columns like HomeTeam/AwayTeam are missing, we can't do anything (shouldn't happen)
        if 'HomeTeam' not in cols_needed or 'AwayTeam' not in cols_needed:
            return self.df
            
        home_cols = [c for c in cols_needed if c in ['Date', 'HomeTeam', 'FTHG', 'FTAG', 'HST', 'AST', 'HF', 'AF', 'HC', 'AC', 'HY', 'AY', 'HR', 'AR']]
        # For away cols, we need to map carefully.
        # But for simpler logic: Split DF -> Rename -> Concat
        
        home_stats = self.df[cols_needed].copy()
        # Rename for Home perspective (Safely)
        rename_map_h = {
            'HomeTeam': 'Team', 'AwayTeam': 'Opponent',
            'FTHG': 'GoalsFor', 'FTAG': 'GoalsAgainst',
            'HST': 'ShotsTargetFor', 'AST': 'ShotsTargetAgainst',
            'HF': 'FoulsFor', 'AF': 'FoulsAgainst',
            'HC': 'CornersFor', 'AC': 'CornersAgainst',
            'HY': 'YellowFor', 'AY': 'YellowAgainst',
            'HR': 'RedFor', 'AR': 'RedAgainst'
        }
        home_stats = home_stats.rename(columns={k:v for k,v in rename_map_h.items() if k in home_stats.columns})
        
        away_stats = self.df[cols_needed].copy()
        # Rename for Away perspective
        rename_map_a = {
            'AwayTeam': 'Team', 'HomeTeam': 'Opponent',
            'FTAG': 'GoalsFor', 'FTHG': 'GoalsAgainst',
            'AST': 'ShotsTargetFor', 'HST': 'ShotsTargetAgainst',
            'AF': 'FoulsFor', 'HF': 'FoulsAgainst',
            'AC': 'CornersFor', 'HC': 'CornersAgainst',
            'AY': 'YellowFor', 'HY': 'YellowAgainst',
            'AR': 'RedFor', 'HR': 'RedAgainst'
        }
        away_stats = away_stats.rename(columns={k:v for k,v in rename_map_a.items() if k in away_stats.columns})
        
        all_stats = pd.concat([home_stats, away_stats]).sort_values(['Team', 'Date'])
        
        if 'Date' in self.df.columns:
            self.df['Month'] = self.df['Date'].dt.month
        
        # --- NEW: Capped Goals (Max 3) for Noise Reduction ---
        self.df['FTHG_Capped'] = self.df['FTHG'].clip(upper=3)
        self.df['FTAG_Capped'] = self.df['FTAG'].clip(upper=3)
        
        # --- NEW: Synthetic Dominance Index (Event Proxy) ---
        # Formula: SOT*3 + Corners*1.5 + Shots*0.5 (Normalized later)
        if {'HST', 'HC'}.issubset(self.df.columns): # Check if columns exist
            # Shots Total approximate if not exists
            hs = self.df.get('HS', self.df['HST'] * 2) # Fallback heuristic
            as_ = self.df.get('AS', self.df['AST'] * 2)
            
            self.df['HomeDominanceRaw'] = (self.df.get('HST', 0)*3.0) + (self.df.get('HC', 0)*1.5) + (hs*0.5)
            self.df['AwayDominanceRaw'] = (self.df.get('AST', 0)*3.0) + (self.df.get('AC', 0)*1.5) + (as_*0.5)
        else:
            self.df['HomeDominanceRaw'] = 0
            self.df['AwayDominanceRaw'] = 0

        # Calculate Means
        metrics = ['GoalsFor', 'GoalsAgainst', 'ShotsTargetFor', 'ShotsTargetAgainst', 
                   'FoulsFor', 'FoulsAgainst', 'CornersFor', 'CornersAgainst',
                   'CardsFor', 'CardsAgainst',
                   'GoalsCappedFor', 'GoalsCappedAgainst', # NEW
                   'DominanceFor', 'DominanceAgainst']      # NEW
        
        # Prepare Stats df with new metrics
        home_cols_new = ['Date', 'HomeTeam', 'FTHG', 'FTAG', 'HST', 'AST', 'HF', 'AF', 'HC', 'AC', 'HY', 'AY', 'HR', 'AR', 'FTHG_Capped', 'FTAG_Capped', 'HomeDominanceRaw', 'AwayDominanceRaw']
        away_cols_new = ['Date', 'AwayTeam', 'FTAG', 'FTHG', 'AST', 'HST', 'AF', 'HF', 'AC', 'HC', 'AY', 'HY', 'AR', 'HR', 'FTAG_Capped', 'FTHG_Capped', 'AwayDominanceRaw', 'HomeDominanceRaw']
        
        # Safe selection of cols
        h_sel = [c for c in home_cols_new if c in self.df.columns]
        a_sel = [c for c in away_cols_new if c in self.df.columns]
        
        home_stats = self.df[h_sel].copy().rename(columns={
            'HomeTeam': 'Team', 'AwayTeam': 'Opponent',
            'FTHG': 'GoalsFor', 'FTAG': 'GoalsAgainst',
            'FTHG_Capped': 'GoalsCappedFor', 'FTAG_Capped': 'GoalsCappedAgainst',
            'HomeDominanceRaw': 'DominanceFor', 'AwayDominanceRaw': 'DominanceAgainst',
             # ... (Keep existing rename logic implicitly handled by consistent structure if possible, but explicit is better)
             'HST': 'ShotsTargetFor', 'AST': 'ShotsTargetAgainst',
             'HF': 'FoulsFor', 'AF': 'FoulsAgainst',
             'HC': 'CornersFor', 'AC': 'CornersAgainst',
             'HY': 'YellowFor', 'AY': 'YellowAgainst',
             'HR': 'RedFor', 'AR': 'RedAgainst'
        })
        
        away_stats = self.df[a_sel].copy().rename(columns={
            'AwayTeam': 'Team', 'HomeTeam': 'Opponent',
            'FTAG': 'GoalsFor', 'FTHG': 'GoalsAgainst',
            'FTAG_Capped': 'GoalsCappedFor', 'FTHG_Capped': 'GoalsCappedAgainst',
            'AwayDominanceRaw': 'DominanceFor', 'HomeDominanceRaw': 'DominanceAgainst',
             'AST': 'ShotsTargetFor', 'HST': 'ShotsTargetAgainst',
             'AF': 'FoulsFor', 'HF': 'FoulsAgainst',
             'AC': 'CornersFor', 'HC': 'CornersAgainst',
             'AY': 'YellowFor', 'HY': 'YellowAgainst',
             'AR': 'RedFor', 'HR': 'RedAgainst'
        })
        
        all_stats = pd.concat([home_stats, away_stats]).sort_values(['Team', 'Date'])
        
        # Calculate Total Cards (Y + R) if columns indicate
        if 'YellowFor' in all_stats.columns:
            all_stats['CardsFor'] = all_stats['YellowFor'] + all_stats['RedFor']
            all_stats['CardsAgainst'] = all_stats['YellowAgainst'] + all_stats['RedAgainst']
        else:
             all_stats['CardsFor'] = 0
             all_stats['CardsAgainst'] = 0
        
        
        # --- NEW: Weighted Rolling Stats (Z-Score Prep) ---
        for metric in metrics:
            if metric in all_stats:
                # Weighted Mean (EMA)
                all_stats[f'Avg{metric}_{window}'] = all_stats.groupby('Team')[metric].transform(lambda x: x.shift(1).ewm(span=window, min_periods=1).mean())
                
                # Weighted StdDev (Rolling EWM Std is complex, use simple rolling std for stability or approximation)
                # Approximation: EWM Var = EWM(x^2) - EWM(x)^2
                # But simple rolling std is usually sufficient for Z-Score volatility check
                # User asked for "Weighted StdDev".
                # Pandas ewm().std() exists!
                all_stats[f'Std{metric}_{window}'] = all_stats.groupby('Team')[metric].transform(lambda x: x.shift(1).ewm(span=window, min_periods=3).std())

        
        # Merge back to main DF
        
        # For Home Team
        home_merge_cols = ['Date', 'Team'] + [f'Avg{m}_{window}' for m in metrics if f'Avg{m}_{window}' in all_stats] + [f'Std{m}_{window}' for m in metrics if f'Std{m}_{window}' in all_stats]
        self.df = self.df.merge(
            all_stats[home_merge_cols].rename(columns={c: f'Home{c}' for c in home_merge_cols if c not in ['Date', 'Team']}),
            left_on=['Date', 'HomeTeam'],
            right_on=['Date', 'Team'],
            how='left'
        ).drop(columns=['Team'])
        
        # For Away Team
        away_merge_cols = ['Date', 'Team'] +  [f'Avg{m}_{window}' for m in metrics if f'Avg{m}_{window}' in all_stats] + [f'Std{m}_{window}' for m in metrics if f'Std{m}_{window}' in all_stats]
        self.df = self.df.merge(
            all_stats[away_merge_cols].rename(columns={c: f'Away{c}' for c in away_merge_cols if c not in ['Date', 'Team']}),
            left_on=['Date', 'AwayTeam'],
            right_on=['Date', 'Team'],
            how='left'
        ).drop(columns=['Team'])
        
        # --- FIX: Alias columns without window suffix for compatibility with Strategies ---
        # e.g. HomeAvgGoalsFor_5 -> HomeAvgGoalsFor
        for col in self.df.columns:
            if f'_{window}' in col:
                base_name = col.replace(f'_{window}', '')
                if base_name not in self.df.columns:
                    self.df[base_name] = self.df[col]

        # Fill NA
        self.df = self.df.fillna(0) # Aggressive fillna for new columns
        
        # --- NEW: Rate-Based Features (Matches Strategies.py) ---
        # We need to calculate the % of last N games where event happened.
        # Event Logic on 'all_stats'
        all_stats['IsOver25'] = ((all_stats['GoalsFor'] + all_stats['GoalsAgainst']) > 2.5).astype(int)
        all_stats['IsBTTS'] = ((all_stats['GoalsFor'] > 0) & (all_stats['GoalsAgainst'] > 0)).astype(int)
        all_stats['IsCleanSheet'] = (all_stats['GoalsAgainst'] == 0).astype(int)
        all_stats['IsWin'] = (all_stats['GoalsFor'] > all_stats['GoalsAgainst']).astype(int)
        all_stats['IsLoss'] = (all_stats['GoalsFor'] < all_stats['GoalsAgainst']).astype(int)
        
        # Calculate Rolling Means (Rates)
        for metric in ['IsOver25', 'IsBTTS', 'IsCleanSheet', 'IsWin', 'IsLoss']:
            all_stats[f'{metric}_Rate'] = all_stats.groupby('Team')[metric].transform(lambda x: x.shift(1).rolling(window=window, min_periods=3).mean())
        
        # Specific Aliases expected by Strategies
        # HomeOver25_Rate, HomeBTTS_Rate, HomeCleanSheet_Rate
        # HomeWinsLast5 -> Sum of IsWin
        all_stats['WinsLast5'] = all_stats.groupby('Team')['IsWin'].transform(lambda x: x.shift(1).rolling(window=window, min_periods=3).sum())
        all_stats['LossesLast5'] = all_stats.groupby('Team')['IsLoss'].transform(lambda x: x.shift(1).rolling(window=window, min_periods=3).sum())
        
        # Merge back Rate Features
        rate_cols = ['IsOver25_Rate', 'IsBTTS_Rate', 'IsCleanSheet_Rate', 'WinsLast5', 'LossesLast5']
        
        # For Home
        self.df = self.df.merge(
             all_stats[['Date', 'Team'] + rate_cols].rename(columns={
                 'IsOver25_Rate': 'HomeOver25_Rate',
                 'IsBTTS_Rate': 'HomeBTTS_Rate', 
                 'IsCleanSheet_Rate': 'HomeCleanSheet_Rate',
                 'WinsLast5': 'HomeWinsLast5',
                 'LossesLast5': 'HomeLossesLast5'
             }),
             left_on=['Date', 'HomeTeam'],
             right_on=['Date', 'Team'],
             how='left'
        ).drop(columns=['Team'])
        
        # For Away
        self.df = self.df.merge(
             all_stats[['Date', 'Team'] + rate_cols].rename(columns={
                 'IsOver25_Rate': 'AwayOver25_Rate',
                 'IsBTTS_Rate': 'AwayBTTS_Rate', 
                 'IsCleanSheet_Rate': 'AwayCleanSheet_Rate',
                 'WinsLast5': 'AwayWinsLast5',
                 'LossesLast5': 'AwayLossesLast5'
             }),
             left_on=['Date', 'AwayTeam'],
             right_on=['Date', 'Team'],
             how='left'
        ).drop(columns=['Team'])
        
        # --- NEW: Aliases for Strategy Compatibility ---
        
        # 1. StdDev Alias
        if 'HomeStdGoalsFor' in self.df.columns:
            self.df['HomeStdDevGoals'] = self.df['HomeStdGoalsFor']
        if 'AwayStdGoalsFor' in self.df.columns:
            self.df['AwayStdDevGoals'] = self.df['AwayStdGoalsFor']
            
        # 2. Z-Score Calculation (Global Base)
        # We need a baseline. For backtesting, we can use the rolling global average of the whole dataset up to that point?
        # Or just a static 1.45 approximation like Predictor uses.
        avg_g_global = 1.45
        
        if 'HomeAvgGoalsFor' in self.df.columns and 'HomeStdDevGoals' in self.df.columns:
             self.df['HomeZScore_Goals'] = (self.df['HomeAvgGoalsFor'] - avg_g_global) / (self.df['HomeStdDevGoals'].replace(0, 1))
             
        if 'AwayAvgGoalsFor' in self.df.columns and 'AwayStdDevGoals' in self.df.columns:
             self.df['AwayZScore_Goals'] = (self.df['AwayAvgGoalsFor'] - avg_g_global) / (self.df['AwayStdDevGoals'].replace(0, 1))
             
        # 3. Z-Score xG (Dominance Proxy)
        # Predictor: z_home_xg = (home_stats.get('DominanceFor', 25.0) - 25.0) / 10.0
        if 'HomeDominanceFor' in self.df.columns:
            self.df['HomeZScore_xG'] = (self.df['HomeDominanceFor'] - 25.0) / 10.0
        else:
            self.df['HomeZScore_xG'] = 0.0
            
        if 'AwayDominanceFor' in self.df.columns:
            self.df['AwayZScore_xG'] = (self.df['AwayDominanceFor'] - 20.0) / 10.0 # Visitor baseline lower?
        else:
            self.df['AwayZScore_xG'] = 0.0

        return self.df

    def add_recent_form(self, window=5):
        """
        Calculates recent form based on Points Per Game (PPG).
        Win = 3, Draw = 1, Loss = 0.
        """
        print(f"Calculating Recent Form PPG (Window={window})...")
        
        # 1. Structure Data: Date, Team, Points
        home_pts = self.df[['Date', 'HomeTeam', 'FTR']].copy()
        home_pts['Points'] = home_pts['FTR'].map({'H': 3, 'D': 1, 'A': 0})
        home_pts = home_pts.rename(columns={'HomeTeam': 'Team'})
        
        away_pts = self.df[['Date', 'AwayTeam', 'FTR']].copy()
        away_pts['Points'] = away_pts['FTR'].map({'A': 3, 'D': 1, 'H': 0})
        away_pts = away_pts.rename(columns={'AwayTeam': 'Team'})
        
        all_pts = pd.concat([home_pts[['Date', 'Team', 'Points']], away_pts[['Date', 'Team', 'Points']]])
        all_pts = all_pts.sort_values(['Team', 'Date'])
        
        # 2. Calculate Rolling PPG (Shift 1 to avoid lookahead) WITH EMA
        all_pts['RollingPPG'] = all_pts.groupby('Team')['Points'].transform(lambda x: x.shift(1).ewm(span=window, min_periods=1).mean())
        
        # 3. Merge back
        # Home Form
        self.df = self.df.merge(
            all_pts[['Date', 'Team', 'RollingPPG']].rename(columns={'RollingPPG': 'HomePPG'}),
            left_on=['Date', 'HomeTeam'],
            right_on=['Date', 'Team'],
            how='left'
        ).drop(columns=['Team'])
        
        # Away Form
        self.df = self.df.merge(
            all_pts[['Date', 'Team', 'RollingPPG']].rename(columns={'RollingPPG': 'AwayPPG'}),
            left_on=['Date', 'AwayTeam'],
            right_on=['Date', 'Team'],
            how='left'
        ).drop(columns=['Team'])
        
        # Fill NA (First games) with 1.35 (roughly average)
        self.df[['HomePPG', 'AwayPPG']] = self.df[['HomePPG', 'AwayPPG']].fillna(1.35)
        
        return self.df

    def add_opponent_difficulty(self, window=5):
        """
        Calculates the average strength (PPG) of the opponents faced in the last N games.
        """
        print(f"Calculating Schedule Difficulty (Opponent PPG, Window={window})...")
        
        # We need a lookup of Team+Date -> RollingPPG (Entering the match)
        # We can use the already calculated 'HomePPG' and 'AwayPPG' but mapped to the team.
        
        # 1. Create a "Team Performance" master list
        h_perf = self.df[['Date', 'HomeTeam', 'AwayTeam', 'AwayPPG']].rename(columns={'HomeTeam': 'Team', 'AwayTeam': 'Opponent', 'AwayPPG': 'Opp_PPG'})
        a_perf = self.df[['Date', 'AwayTeam', 'HomeTeam', 'HomePPG']].rename(columns={'AwayTeam': 'Team', 'HomeTeam': 'Opponent', 'HomePPG': 'Opp_PPG'})
        
        all_perf = pd.concat([h_perf, a_perf]).sort_values(['Team', 'Date'])
        
        # 2. Rolling Average of Opponent PPG (EMA)
        # "In the last 5 games, what was the weighted average strength of teams I played?"
        all_perf['AvgOpponentStrength'] = all_perf.groupby('Team')['Opp_PPG'].transform(lambda x: x.shift(1).ewm(span=window, min_periods=1).mean())
        
        # 3. Merge back
        self.df = self.df.merge(
            all_perf[['Date', 'Team', 'AvgOpponentStrength']].rename(columns={'AvgOpponentStrength': 'HomeOppDifficulty'}),
            left_on=['Date', 'HomeTeam'],
            right_on=['Date', 'Team'],
            how='left'
        ).drop(columns=['Team'])
        
        self.df = self.df.merge(
            all_perf[['Date', 'Team', 'AvgOpponentStrength']].rename(columns={'AvgOpponentStrength': 'AwayOppDifficulty'}),
            left_on=['Date', 'AwayTeam'],
            right_on=['Date', 'Team'],
            how='left'
        ).drop(columns=['Team'])
        
        # Fill NA
        self.df[['HomeOppDifficulty', 'AwayOppDifficulty']] = self.df[['HomeOppDifficulty', 'AwayOppDifficulty']].fillna(1.35)
        
        return self.df

    def add_relative_strength(self):
        """
        Calculates Relative Strength metrics.
        Example: Home Attack Strength = HomeAvgGoalsFor / LeagueAvgGoalsFor
        Safeguarded against missing columns for Cloud Deployment.
        """
        # Feature Dependencies
        required_cols = [
            'HomeAvgShotsTargetFor', 'AwayAvgShotsTargetAgainst',
            'AwayAvgShotsTargetFor', 'HomeAvgShotsTargetAgainst',
            'HomeAvgGoalsFor', 'AwayAvgGoalsAgainst',
            'AwayAvgGoalsFor', 'HomeAvgGoalsAgainst',
            'HomePPG', 'AwayPPG'
        ]

        # Initialize missing columns with defaults to prevent Crash
        for col in required_cols:
            if col not in self.df.columns:
                print(f"Warning: Missing column {col}, using default.")
                self.df[col] = 1.35 if 'PPG' in col else (3.5 if 'Shots' in col else 1.2)

        # Avoid division by zero
        eps = 0.01
        
        # Attack vs Defense Ratios
        # Home Attack vs Away Defense (using shots on target as a proxy for "Threat")
        self.df['HomeAttackStrength'] = self.df['HomeAvgShotsTargetFor'] / (self.df['AwayAvgShotsTargetAgainst'] + eps)
        self.df['AwayAttackStrength'] = self.df['AwayAvgShotsTargetFor'] / (self.df['HomeAvgShotsTargetAgainst'] + eps)
        
        # Interaction Features (User Request for Context):
        # 1. Expected Goals Proxy: Offense * Opponent Defense
        self.df['HomeExpG_Raw'] = self.df['HomeAvgGoalsFor'] * self.df['AwayAvgGoalsAgainst']
        self.df['AwayExpG_Raw'] = self.df['AwayAvgGoalsFor'] * self.df['HomeAvgGoalsAgainst']
        
        # 2. Top Clash Indicator
        # High PPG vs High PPG
        self.df['IsTopClash'] = ((self.df['HomePPG'] > 1.7) & (self.df['AwayPPG'] > 1.7)).astype(int)
        
        # 3. Defensive Lock
        # Low Goals Against for both
        self.df['DefensiveLock'] = ((self.df['HomeAvgGoalsAgainst'] < 1.0) & (self.df['AwayAvgGoalsAgainst'] < 1.0)).astype(int)

        return self.df
        # Low Conceded vs Low Conceded
        self.df['IsDefensiveLock'] = ((self.df['HomeAvgGoalsAgainst'] < 1.0) & (self.df['AwayAvgGoalsAgainst'] < 1.0)).astype(int)

        return self.df
