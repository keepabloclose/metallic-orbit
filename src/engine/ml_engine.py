import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
import warnings
import os
import joblib

# Suppress sklearn warnings for cleaner output
warnings.filterwarnings('ignore')

class MLEngine:
    MODEL_PATH = os.path.join(os.path.dirname(__file__), 'trained_model.pkl')
    
    def __init__(self):
        self.models = {}
        self.regressors = {}
        self.feature_cols = [
            'HomePPG', 'AwayPPG',
            'HomeAvgGoalsFor', 'HomeAvgGoalsAgainst',
            'AwayAvgGoalsFor', 'AwayAvgGoalsAgainst',
            'HomeAvgCornersFor', 'AwayAvgCornersFor',
            'HomeAvgShotsTargetFor', 'AwayAvgShotsTargetFor',
            'HomeRestDays', 'AwayRestDays',
            'HomeAttackStrength', 'AwayAttackStrength',
            'HomeExpG_Raw', 'AwayExpG_Raw',
            'IsTopClash', 'IsDefensiveLock'
        ]
        self.targets = {
            'ML_HomeWin': lambda row: 1 if row['FTHG'] > row['FTAG'] else 0,
            'ML_AwayWin': lambda row: 1 if row['FTAG'] > row['FTHG'] else 0,
            'ML_Draw': lambda row: 1 if row['FTHG'] == row['FTAG'] else 0,
            'ML_Over25': lambda row: 1 if (row['FTHG'] + row['FTAG']) > 2.5 else 0,
            'ML_Over15': lambda row: 1 if (row['FTHG'] + row['FTAG']) > 1.5 else 0,
            'ML_BTTS': lambda row: 1 if (row['FTHG'] > 0) and (row['FTAG'] > 0) else 0
        }
        self.reg_targets = {
            'REG_HomeGoals': lambda row: row['FTHG'],
            'REG_AwayGoals': lambda row: row['FTAG']
        }
        self.is_trained = False
        self.imputer = SimpleImputer(strategy='mean')

    def _calculate_expanding_stats(self, df):
        """
        Calculates historical stats (PPG, AvgGoals) for training.
        This effectively replays history to generate stats 'as known before the match'.
        """
        # We need to construct a dataset where each row has the stats ENTERING the match.
        # This is expensive to do row-by-row.
        # Optimized approach: Group by Team, calculate shifting expanding mean.
        
        # 1. Create long-form stats (one row per team per match)
        home_cols = ['Date', 'HomeTeam', 'FTHG', 'FTAG', 'FTR', 'HST', 'AST', 'HC', 'AC']
        away_cols = ['Date', 'AwayTeam', 'FTHG', 'FTAG', 'FTR', 'HST', 'AST', 'HC', 'AC']
        
        # Safe column selection (some CSVs might lack HST/AST/HC)
        cols_available = df.columns.tolist()
        h_sel = [c for c in home_cols if c in cols_available]
        a_sel = [c for c in away_cols if c in cols_available]
        
        home_df = df[h_sel].rename(columns={'HomeTeam': 'Team', 'FTHG': 'GoalsFor', 'FTAG': 'GoalsAgainst', 'HST': 'ShotsFor', 'AST': 'ShotsAgainst', 'HC': 'CornersFor', 'AC': 'CornersAgainst'})
        home_df['IsHome'] = 1
        home_df['Points'] = home_df['FTR'].map({'H': 3, 'D': 1, 'A': 0}) if 'FTR' in df.columns else 0 # Fallback
        
        away_df = df[a_sel].rename(columns={'AwayTeam': 'Team', 'FTAG': 'GoalsFor', 'FTHG': 'GoalsAgainst', 'AST': 'ShotsFor', 'HST': 'ShotsAgainst', 'AC': 'CornersFor', 'HC': 'CornersAgainst'})
        away_df['IsHome'] = 0
        away_df['Points'] = df['FTR'].map({'A': 3, 'D': 1, 'H': 0}) if 'FTR' in df.columns else 0

        # Combine
        full_df = pd.concat([home_df, away_df]).sort_values('Date')
        
        # 2. Calculate Expanding Means (Shifted by 1 to exclude current match)
        metrics = full_df.groupby('Team')[['GoalsFor', 'GoalsAgainst', 'Points', 'ShotsFor', 'CornersFor']].transform(
            lambda x: x.expanding().mean().shift(1)
        )
        
        full_df['AvgGoalsFor'] = metrics['GoalsFor']
        full_df['AvgGoalsAgainst'] = metrics['GoalsAgainst']
        full_df['PPG'] = metrics['Points'] 
        full_df['AvgShots'] = metrics['ShotsFor']
        if 'CornersFor' in metrics: full_df['AvgCornersFor'] = metrics['CornersFor']
        else: full_df['AvgCornersFor'] = 0
        
        # 3. Join back to original structure
        stats_home = full_df[full_df['IsHome'] == 1][['AvgGoalsFor', 'AvgGoalsAgainst', 'PPG', 'AvgShots', 'AvgCornersFor']]
        stats_home.columns = ['HomeAvgGoalsFor', 'HomeAvgGoalsAgainst', 'HomePPG', 'HomeAvgShots', 'HomeAvgCornersFor']
        # Map ShotsFor to ShotsTarget for naming consistency with new feature list, 
        # though HST is technically ShotsTarget, so naming it AvgShotsTargetFor is more accurate.
        stats_home = stats_home.rename(columns={'HomeAvgShots': 'HomeAvgShotsTargetFor'}) 
        
        stats_away = full_df[full_df['IsHome'] == 0][['AvgGoalsFor', 'AvgGoalsAgainst', 'PPG', 'AvgShots', 'AvgCornersFor']]
        stats_away.columns = ['AwayAvgGoalsFor', 'AwayAvgGoalsAgainst', 'AwayPPG', 'AwayAvgShots', 'AwayAvgCornersFor']
        stats_away = stats_away.rename(columns={'AwayAvgShots': 'AwayAvgShotsTargetFor'})
        
        training_df = df.copy()
        training_df = pd.merge(training_df, stats_home, left_index=True, right_index=True, how='left', suffixes=('', '_dup'))
        training_df = training_df[[c for c in training_df.columns if not c.endswith('_dup')]]
        
        training_df = pd.merge(training_df, stats_away, left_index=True, right_index=True, how='left', suffixes=('', '_dup'))
        training_df = training_df[[c for c in training_df.columns if not c.endswith('_dup')]]
        
        # --- NEW FEATURES (Context) ---
        # 1. Expected Goals (Interaction)
        training_df['HomeExpG_Raw'] = training_df['HomeAvgGoalsFor'] * training_df['AwayAvgGoalsAgainst']
        training_df['AwayExpG_Raw'] = training_df['AwayAvgGoalsFor'] * training_df['HomeAvgGoalsAgainst']
        
        # 2. Top Clash
        training_df['IsTopClash'] = ((training_df['HomePPG'] > 1.7) & (training_df['AwayPPG'] > 1.7)).astype(int)
        
        # 3. Defensive Lock
        training_df['IsDefensiveLock'] = ((training_df['HomeAvgGoalsAgainst'] < 1.0) & (training_df['AwayAvgGoalsAgainst'] < 1.0)).astype(int)
        
        training_df = training_df.dropna(subset=['HomePPG', 'AwayPPG'])
        return training_df
        
    def train_models(self, historical_data):
        """
        Trains random forest models for all targets.
        """
        if historical_data.empty:
            return {"error": "No data"}
            
        print("Training ML Models... Generating Features...")
        df_train = self._calculate_expanding_stats(historical_data)
        
        if df_train.empty:
            return
            
        X = df_train[self.feature_cols].copy()
        
        for c in self.feature_cols:
            if c not in X.columns:
                X[c] = 0.0
        
        X_imputed = self.imputer.fit_transform(X)
        
        # --- TIME DECAY WEIGHTS ---
        # Calculate weights based on Recency
        # Weight = exp(-decay_rate * days_ago)
        # Using a half-life of roughly 365 days (1 year) implies decay_rate ~ 0.002
        dates = pd.to_datetime(df_train['Date'])
        max_date = dates.max()
        days_ago = (max_date - dates).dt.days
        
        # Decay Rate: 0.002 means a match 1 year ago has ~48% weight of today
        # 0.001 means ~69%
        # User wants "State of Form" -> Higher emphasis on recent. Let's use 0.003
        decay_rate = 0.003 
        sample_weights = np.exp(-decay_rate * days_ago)
        
        # Normalize weights to sum to n_samples (optional, but good for RF)
        # sample_weights = sample_weights / sample_weights.mean() 
        
        scores = {}
        
        for target_name, target_func in self.targets.items():
            try:
                y = df_train.apply(target_func, axis=1)
                
                # OPTIMIZED HYPERPARAMETERS
                # Adding Sample Weights
                clf = RandomForestClassifier(n_estimators=60, max_depth=8, min_samples_split=10, random_state=42)
                clf.fit(X_imputed, y, sample_weight=sample_weights)
                
                self.models[target_name] = clf
                scores[target_name] = clf.score(X_imputed, y) 
            except Exception as e:
                print(f"Failed to train {target_name}: {e}")

        # 2. Train Regressors (Correct Score)
        for target_name, target_func in self.reg_targets.items():
            try:
                y = df_train.apply(target_func, axis=1)
                print(f"DEBUG: Training Regressor {target_name}. Mean Target: {y.mean():.4f}, Max: {y.max()}")
                # Regressor needs to be slightly robust
                reg = RandomForestRegressor(n_estimators=60, max_depth=8, min_samples_leaf=5, random_state=42)
                reg.fit(X_imputed, y, sample_weight=sample_weights)
                self.regressors[target_name] = reg
                scores[target_name] = reg.score(X_imputed, y) 
            except Exception as e:
                print(f"Failed to train Regressor {target_name}: {e}")
                
        self.is_trained = True
        return scores

    def predict_row(self, row_stats):
        """
        Predicts outcomes for a single match row (dictionary of stats).
        Return: Dict of probabilities e.g. {'ML_HomeWin': 0.75, ...}
        """
        if not self.is_trained:
            return {}
            
        # Extract features in correct order
        input_data = []
        for feat in self.feature_cols:
            # Map simplified keys from predictor to training keys if needed
            # Predictor usually gives 'HomePPG', 'HomeAvgGoalsFor' etc.
            # Handle potential missing keys
            val = row_stats.get(feat, 0.0)
            if val is None: val = 0.0
            input_data.append(val)
            
        X_in = np.array([input_data])
        # Impute (though usually stats are full)
        X_in = self.imputer.transform(X_in)
        
        results = {}
        for name, clf in self.models.items():
            try:
                # Get probability of class 1 (True)
                prob = clf.predict_proba(X_in)[0][1]
                # Convert to percentage int for UI
                results[name] = int(prob * 100)
            except:
                results[name] = 50 # Fallback
                
        # Regressors
        for name, reg in self.regressors.items():
            try:
                pred = reg.predict(X_in)[0]
                print(f"DEBUG: {name} Raw Pred: {pred:.4f}")
                results[name] = round(pred) # Round to nearest integer for goals
            except:
                results[name] = 0
                
        return results

    def save_model(self):
        try:
            joblib.dump({
                'models': self.models,
                'regressors': self.regressors,
                'imputer': self.imputer
            }, self.MODEL_PATH)
            print("Model saved to cache.")
        except Exception as e:
            print(f"Failed to save model: {e}")

    def load_model(self):
        if os.path.exists(self.MODEL_PATH):
            try:
                data = joblib.load(self.MODEL_PATH)
                self.models = data.get('models', {})
                self.regressors = data.get('regressors', {})
                self.imputer = data.get('imputer')
                if self.models:
                    self.is_trained = True
                    return True
            except Exception as e:
                print(f"Failed to load model: {e}")
        return False
