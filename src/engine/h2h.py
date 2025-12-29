
import pandas as pd

class H2HManager:
    def __init__(self, data):
        self.data = data.copy()
        # Ensure Date is datetime
        if not pd.api.types.is_datetime64_any_dtype(self.data['Date']):
            self.data['Date'] = pd.to_datetime(self.data['Date'], dayfirst=True)

    def get_h2h_matches(self, home_team, away_team):
        """
        Retrieves all matches between two teams from the loaded history.
        """
        mask = (
            ((self.data['HomeTeam'] == home_team) & (self.data['AwayTeam'] == away_team)) |
            ((self.data['HomeTeam'] == away_team) & (self.data['AwayTeam'] == home_team))
        )
        matches = self.data[mask].sort_values('Date', ascending=False)
        return matches

    def get_h2h_summary(self, home_team, away_team):
        """
        Returns a summary dictionary (Wins, Draws, Goals).
        """
        matches = self.get_h2h_matches(home_team, away_team)
        if matches.empty:
            return None

        summary = {
            'Matches': len(matches),
            'HomeWins': 0, # Wins for the requested 'home_team'
            'AwayWins': 0, # Wins for the requested 'away_team'
            'Draws': 0,
            'HomeGoals': 0,
            'AwayGoals': 0
        }

        for _, row in matches.iterrows():
            res = row['FTR']
            h = row['HomeTeam']
            a = row['AwayTeam']
            hg = row['FTHG']
            ag = row['FTAG']

            # Goals
            if h == home_team:
                summary['HomeGoals'] += hg
                summary['AwayGoals'] += ag
            else:
                summary['HomeGoals'] += ag
                summary['AwayGoals'] += hg

            # Result
            if res == 'D':
                summary['Draws'] += 1
            elif (h == home_team and res == 'H') or (h == away_team and res == 'A'):
                summary['HomeWins'] += 1
            else:
                summary['AwayWins'] += 1
                
        return summary

    def format_for_display(self, matches):
        """
        Returns a styled DataFrame for UI display (Spanish headers).
        """
        if matches.empty:
            return pd.DataFrame()

        # Cols to show
        cols = ['Date', 'Div', 'Season', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR']
        # Add corners/cards if available
        optional = ['HST', 'AST', 'HC', 'AC', 'HY', 'AY', 'HR', 'AR']
        cols.extend([c for c in optional if c in matches.columns])
        
        df = matches[cols].copy()
        
        # Format Date
        df['Date'] = df['Date'].dt.strftime('%d/%m/%Y')
        
        # Rename Map
        rename_map = {
            'Date': 'Fecha', 'Div': 'Liga', 'Season': 'Temporada',
            'HomeTeam': 'Local', 'AwayTeam': 'Visitante',
            'FTHG': 'Goles L', 'FTAG': 'Goles V', 'FTR': 'Res',
            'HST': 'Tiros L', 'AST': 'Tiros V',
            'HC': 'Córners L', 'AC': 'Córners V',
            'HY': 'Am. L', 'AY': 'Am. V',
            'HR': 'Roj. L', 'AR': 'Roj. V'
        }
        df = df.rename(columns=rename_map)
        return df
