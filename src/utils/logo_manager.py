
import requests

class LogoManager:
    BASE_URL = "https://raw.githubusercontent.com/luukhopman/football-logos/master/logos"
    
    LEAGUE_MAP = {
        'E0': 'England - Premier League',
        'SP1': 'Spain - La Liga',
        'I1': 'Italy - Serie A',
        'D1': 'Germany - Bundesliga',
        'F1': 'France - Ligue 1',
        'N1': 'Netherlands - Eredivisie',
        'N1': 'Netherlands - Eredivisie',
        'P1': 'Portugal - Liga Portugal',
        'SP2': 'Spain - La Liga 2',
        'E1': 'England - Championship'
    }

    # Manual overrides for team names that don't match the repo
    # MyDataName -> RepoName
    TEAM_NAME_SHIFTS = {
        # EPL
        'Man United': 'Manchester United',
        'Man Utd': 'Manchester United', # Just in case
        'Man City': 'Manchester City',
        'Liverpool': 'Liverpool FC',
        'Arsenal': 'Arsenal FC',
        'Chelsea': 'Chelsea FC',
        'Everton': 'Everton FC',
        'Fulham': 'Fulham FC',
        'Brentford': 'Brentford FC',
        'Burnley': 'Burnley FC',
        'Bournemouth': 'AFC Bournemouth',
        'Sunderland': 'Sunderland AFC',
        'Leicester': 'Leicester City',
        'Leeds': 'Leeds United',
        'Norwich': 'Norwich City',
        'Nottm Forest': 'Nottingham Forest',
        'Wolves': 'Wolverhampton Wanderers',
        'Newcastle': 'Newcastle United',
        'Sheffield United': 'Sheffield United',
        'West Ham': 'West Ham United',
        'Brighton': 'Brighton & Hove Albion',
        
        # Serie A (Verified via Repo Listing)
        'Inter': 'Inter Milan',
        'Milan': 'AC Milan',
        'Roma': 'AS Roma',
        'Lazio': 'SS Lazio',
        'Napoli': 'SSC Napoli',
        'Juventus': 'Juventus FC',
        'Atalanta': 'Atalanta BC', 
        'Fiorentina': 'ACF Fiorentina',
        'Udinese': 'Udinese Calcio',
        'Salernitana': 'US Salernitana 1919',
        'Monza': 'AC Monza', # Assumption, or check repo?
        'Lecce': 'US Lecce',
        'Verona': 'Hellas Verona',
        'Bologna': 'Bologna FC 1909',
        'Cagliari': 'Cagliari Calcio',
        'Empoli': 'Empoli FC',
        'Genoa': 'Genoa CFC',
        'Torino': 'Torino FC',
        
        # La Liga
        'Real Madrid': 'Real Madrid CF',
        'Barcelona': 'FC Barcelona',
        'Ath Madrid': 'Atletico Madrid',
        'Sevilla': 'Sevilla FC',
        'Betis': 'Real Betis',
        'Sociedad': 'Real Sociedad',
        'Valencia': 'Valencia CF',
        'Villarreal': 'Villarreal CF',
        'Ath Bilbao': 'Athletic Club',
        
        # Bundesliga
        'Dortmund': 'Borussia Dortmund',
        'Leverkusen': 'Bayer 04 Leverkusen',
        'M\'gladbach': 'Borussia Monchengladbach',
        'Bayern Munich': 'Bayern Munich', # Repo listed "Bayern Munich.png"
        'Frankfurt': 'Eintracht Frankfurt',
        'Mainz': '1.FSV Mainz 05', # Repo listed "1.FSV Mainz 05.png"
        'Union Berlin': '1.FC Union Berlin',
        'Koln': '1.FC Koln',
        'Freiburg': 'SC Freiburg',
        'Wolfsburg': 'VfL Wolfsburg',
        'Leipzig': 'RB Leipzig',
        'Stuttgart': 'VfB Stuttgart',
        'Augsburg': 'FC Augsburg',
        'Hoffenheim': 'TSG 1899 Hoffenheim',
        'Bochum': 'VfL Bochum 1848', # Guess
        
        # Ligue 1
        'PSG': 'Paris Saint-Germain',
        'Marseille': 'Olympique de Marseille',
        'Lyon': 'Olympique Lyonnais',
        'Monaco': 'AS Monaco',
        'Lille': 'LOSC Lille',
    }
    
    # Hardcoded URLs for teams where repo is missing/broken
    HARDCODED_URLS = {
        'Barcelona': "https://upload.wikimedia.org/wikipedia/en/thumb/4/47/FC_Barcelona_%28crest%29.svg/200px-FC_Barcelona_%28crest%29.svg.png",
        'Getafe CF': "https://upload.wikimedia.org/wikipedia/en/thumb/7/7f/Getafe_CF_logo.svg/200px-Getafe_CF_logo.svg.png",
        'Getafe': "https://upload.wikimedia.org/wikipedia/en/thumb/7/7f/Getafe_CF_logo.svg/200px-Getafe_CF_logo.svg.png",
        'Real Madrid': "https://upload.wikimedia.org/wikipedia/en/thumb/5/56/Real_Madrid_CF.svg/200px-Real_Madrid_CF.svg.png"
    }

    def __init__(self):
        self.cache = {}

    def get_league_logo(self, div):
        """Returns the URL for the league logo."""
        path = self.LEAGUE_MAP.get(div)
        if path:
            return f"{self.BASE_URL}/{path}.png".replace(" ", "%20")
        return None

    def get_team_logo(self, team_name, div=None):
        """
        Returns the constructed URL for the team logo.
        If div is provided, uses strictly that league folder (more accurate).
        Otherwise, might search (not implemented yet).
        """
        # Check Hardcoded first
        if team_name in self.HARDCODED_URLS:
            return self.HARDCODED_URLS[team_name]
        if not div:
            return None # Can't guess league easily without data
            
        league_path = self.LEAGUE_MAP.get(div)
        if not league_path:
            return None
            
        # Normalize Name
        clean_name = self.TEAM_NAME_SHIFTS.get(team_name, team_name)
        
        # URL Encode logic (simple space replacement)
        # Note: Github raw URLs handle spaces as %20
        clean_name_encoded = clean_name.replace(" ", "%20")
        league_path_encoded = league_path.replace(" ", "%20")
        
        return f"{self.BASE_URL}/{league_path_encoded}/{clean_name_encoded}.png"

    def verify_url(self, url):
        """Checks if URL exists (HEAD request). Returns True/False."""
        try:
            r = requests.head(url, timeout=2)
            return r.status_code == 200
        except:
            return False
