import pandas as pd
import numpy as np

class RefereeAnalyzer:
    def __init__(self, df):
        self.df = df.copy()
        # Ensure Referee column exists and is clean
        if 'Referee' in self.df.columns:
            self.df = self.df.dropna(subset=['Referee'])
            # Normalize Names
            self.df['Referee'] = self.df['Referee'].apply(self._normalize_name)
        else:
            print("Warning: No 'Referee' column found in data.")
            self.df = pd.DataFrame()

    def _normalize_name(self, name):
        if pd.isna(name) or name == 0 or str(name).strip() == "":
            return None
        
        name_str = str(name).strip()
        
        # Handle "Last, First" format (Common in some data sources)
        if ',' in name_str:
            parts = name_str.split(',')
            if len(parts) == 2:
                # Swap to "First Last"
                name_str = f"{parts[1].strip()} {parts[0].strip()}"
        
        # Remove common titles
        name_str = name_str.replace("Dr.", "").replace("Mr.", "").strip()
        
        # Standardize Case
        name_str = name_str.title()
        
        # Specific Fixes
        if "Hernandez Hernandez" in name_str: return "Hernandez Hernandez"
        
        # Remove trailing dots
        if name_str.endswith('.'): name_str = name_str[:-1]
        
        return name_str

    def get_summary(self, min_matches=5):
        """
        Returns a DataFrame with summary stats for all referees.
        """
        if self.df.empty:
            return pd.DataFrame()

        # Group by Referee and League (Div)
        # We need columns: HY (Home Yellow), AY (Away Yellow), HR (Home Red), AR (Away Red), HF (Home Fouls), AF (Away Fouls)
        # Check available columns
        cols = self.df.columns
        stats_cols = {
            'HY': 'HomeYellow', 'AY': 'AwayYellow',
            'HR': 'HomeRed', 'AR': 'AwayRed',
            'HF': 'HomeFouls', 'AF': 'AwayFouls'
        }
        
        # Filter for existing columns only
        agg_dict = {}
        for short, original in stats_cols.items():
            if short in cols:
                agg_dict[short] = 'mean'
            elif original in cols: # Sometimes names differ
                 pass # We rely on standard names usually (HY, AY) in football-data.co.uk
        
        # Standard football-data.co.uk columns for cards/fouls are:
        # HY, AY, HR, AR, HF, AF
        
        required_cols = ['HY', 'AY', 'HR', 'AR', 'HF', 'AF']
        available_cols = [c for c in required_cols if c in self.df.columns]
        
        if not available_cols:
             return pd.DataFrame()

        # Group by Referee AND League
        if 'Div' in self.df.columns:
            summary = self.df.groupby(['Referee', 'Div'])[available_cols].agg(['count', 'mean', 'sum'])
        else:
            summary = self.df.groupby('Referee')[available_cols].agg(['count', 'mean', 'sum'])
        
        # Flatten columns
        # Structure is (Col, Agg) -> Col_Agg
        summary.columns = ['_'.join(col).strip() for col in summary.columns.values]
        
        # Rename count (it's the same for all columns, just take one)
        count_col = f"{available_cols[0]}_count"
        summary = summary.rename(columns={count_col: 'Matches'})
        
        # Reset index to make Referee and Div columns
        summary = summary.reset_index()
        
        # Calculate Aggregates
        # Avg Total Cards
        if 'HY_mean' in summary.columns and 'AY_mean' in summary.columns:
            summary['AvgYellows'] = summary['HY_mean'] + summary['AY_mean']
        
        if 'HR_mean' in summary.columns and 'AR_mean' in summary.columns:
            summary['AvgReds'] = summary['HR_mean'] + summary['AR_mean']
            
        if 'HF_mean' in summary.columns and 'AF_mean' in summary.columns:
            summary['AvgFouls'] = summary['HF_mean'] + summary['AF_mean']
            # Bias: (Home Fouls - Away Fouls) / Total Fouls roughly?
            # Or simplified: Home Fouls per Game vs Away Fouls per Game
            summary['HomeFoulsAvg'] = summary['HF_mean']
            summary['AwayFoulsAvg'] = summary['AF_mean']
            
        # Filter by min matches
        summary = summary[summary['Matches'] >= min_matches].sort_values('Matches', ascending=False)
        
        return summary

    def get_referee_matches(self, referee_name):
        return self.df[self.df['Referee'] == referee_name].sort_values('Date', ascending=False)
