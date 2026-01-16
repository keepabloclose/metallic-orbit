
import pandas as pd

class NameNormalizer:
    """
    Centralized utility for normalizing team names across different data sources 
    (Football-Data.co.uk vs API vs Common Usage).
    Ensures that a team like 'Leicester City' is treated the same as 'Leicester' 
    to preserve historical data continuity across leagues.
    
    RESTRICTED TO SUPPORTED LEAGUES ONLY (E0, E1, SP1, SP2, D1, I1, F1).
    """
    
    @classmethod
    def normalize(cls, name):
        """Returns the normalized team name."""
        if not isinstance(name, str):
            return str(name)
        
        name = name.strip()
        # Handle Non-Breaking Spaces (often in CSVs)
        name = name.replace('\xa0', ' ')
        
        # Case insensitive check (heuristic)
        # We'll stick to exact mapping for now but cleaned
        
        
        # Extended Mapping for SUPPORTED LEAGUES
        mapping = {
            # --- SPAIN (SP1, SP2) ---
            'Rayo Vallecano': 'Vallecano',
            'CA Osasuna': 'Osasuna',
            'RCD Mallorca': 'Mallorca',
            'Athletic Club': 'Ath Bilbao',
            'Real Betis': 'Betis',
            'Real Sociedad': 'Sociedad',
            'RC Celta': 'Celta',
            'Celta de Vigo': 'Celta',
            'Sevilla FC': 'Sevilla',
            'Sevilla': 'Sevilla',
            'Villarreal CF': 'Villarreal', # FIX
            'Valencia CF': 'Valencia',     # FIX
            'Deportivo Alaves': 'Alaves',
            'Deportivo Alavés': 'Alaves',
            'Alavés': 'Alaves',
            'Atlético de Madrid': 'Ath Madrid',
            'Atletico Madrid': 'Ath Madrid',
            'Girona FC': 'Girona',
            'Real Oviedo': 'Oviedo',
            'Levante UD': 'Levante',
            'Real Zaragoza': 'Zaragoza',
            'Sporting de Gijón': 'Sp Gijon',
            'Sporting Gijon': 'Sp Gijon',
            'Sporting Gijón': 'Sp Gijon',
            'Gijon': 'Sp Gijon', # Scraper
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
            'Racing Club Ferrol': 'Ferrol',
            'UD Almería': 'Almeria',
            'Cadiz CF': 'Cadiz',
            'Cultural Leonesa': 'Cultural Leonesa',
            'Real Sociedad B': 'Sociedad B',
            'AD Ceuta': 'Ceuta',
            'FC Andorra': 'Andorra',
            'U.D. Las Palmas': 'Las Palmas',
            'Las Palmas': 'Las Palmas',
            'CD Leganes': 'Leganes',
            'Leganés': 'Leganes',
            'Deportivo': 'Dep. La Coruna',
            'Coruna': 'Dep. La Coruna', # Scraper
            'La Coruna': 'Dep. La Coruna',
            'Getafe CF': 'Getafe',
            'RCD Espanyol de Barcelona': 'Espanyol',
            'RCD Espanyol': 'Espanyol',
            'Espanol': 'Espanyol',

            # --- ENGLAND (E0, E1) ---
            'Spurs': 'Tottenham',
            'Tottenham Hotspur': 'Tottenham',
            'Man Utd': 'Man United',
            'Manchester United': 'Man United',
            'Man City': 'Man City',
            'Manchester City': 'Man City',
            'Wolves': 'Wolves',
            'Wolverhampton': 'Wolves',
            'Wolverhampton Wanderers': 'Wolves',
            'Nottm Forest': "Nott'm Forest",
            'Nottingham Forest': "Nott'm Forest",
            'Sheffield Utd': 'Sheffield United',
            'Sheffield United': 'Sheffield United',
            'Leicester City': 'Leicester', 
            'Leicester': 'Leicester',
            'Leeds United': 'Leeds',
            'Brighton & Hove Albion': 'Brighton',
            'Brighton': 'Brighton',
            'Newcastle United': 'Newcastle',
            'Newcastle': 'Newcastle',
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
            'Ipswich Town': 'Ipswich',
            'Southampton FC': 'Southampton',
            'Arsenal FC': 'Arsenal',
            'Liverpool FC': 'Liverpool',
            'Chelsea FC': 'Chelsea',
            'Aston Villa FC': 'Aston Villa',
            'Everton FC': 'Everton',
            'Fulham FC': 'Fulham',
            'Brentford FC': 'Brentford',
            'Crystal Palace FC': 'Crystal Palace',
            'West Ham United': 'West Ham',
            'West Ham United FC': 'West Ham',
            'AFC Bournemouth': 'Bournemouth',
            'Bournemouth': 'Bournemouth',
            'US Cremonese': 'Cremonese', # Fix for Serie A match
            'Cremonese': 'Cremonese',

            # --- GERMANY (D1) ---
            '1. FC Union Berlin': 'Union Berlin',
            '1. FSV Mainz 05': 'Mainz',
            'Mainz 05': 'Mainz',
            'FSV Mainz': 'Mainz', # API
            'FC St. Pauli': 'St Pauli',
            'St. Pauli': 'St Pauli',
            '1. FC Heidenheim 1846': 'Heidenheim',
            '1. FC Heidenheim': 'Heidenheim', # API
            'Heidenheim': 'Heidenheim',
            '1. FC Kln': 'FC Koln',
            '1. FC Köln': 'FC Koln',
            'FC Köln': 'FC Koln',
            '1. FC Cologne': 'FC Koln', # API
            'Bayer 04 Leverkusen': 'Leverkusen',
            'Bayer Leverkusen': 'Leverkusen',
            'Leverkusen': 'Leverkusen',
            'Borussia Mönchengladbach': "M'gladbach",
            'Borussia Moenchengladbach': "M'gladbach",
            'Borussia M.Gladbach': "M'gladbach",
            'M\'gladbach': "M'gladbach",
            'FC Bayern München': 'Bayern Munich',
            'Bayern Munich': 'Bayern Munich',
            'VfL Wolfsburg': 'Wolfsburg',
            'FC Augsburg': 'Augsburg',
            'Eintracht Frankfurt': 'Ein Frankfurt',
            'TSG 1899 Hoffenheim': 'Hoffenheim',
            'TSG Hoffenheim': 'Hoffenheim',
            'VfL Bochum 1848': 'Bochum',
            'VfL Bochum': 'Bochum',
            'Holstein Kiel': 'Holstein Kiel',
            'VfB Stuttgart': 'Stuttgart',
            'Borussia Dortmund': 'Dortmund',
            'RB Leipzig': 'RB Leipzig',
            'Sport-Club Freiburg': 'Freiburg',
            'SC Freiburg': 'Freiburg',
            'Hamburger SV': 'Hamburg',
            'Fortuna Dusseldorf': 'Fortuna Dusseldorf',
            'Werder Bremen': 'SV Werder Bremen', 
            
            # --- ITALY (I1) ---
            'Inter Milan': 'Inter',
            'Internazionale': 'Inter',
            'Inter Milano': 'Inter', # API
            'AC Milan': 'Milan',
            'Juventus FC': 'Juventus',
            'Juventus Turin': 'Juventus', # API
            'SS Lazio': 'Lazio',
            'Lazio Rome': 'Lazio', # API
            'AS Roma': 'Roma',
            'SSC Napoli': 'Napoli',
            'Atalanta BC': 'Atalanta',
            'Bologna FC': 'Bologna',
            'ACF Fiorentina': 'Fiorentina',
            'Torino FC': 'Torino',
            'Udinese Calcio': 'Udinese',
            'Genoa CFC': 'Genoa',
            'Hellas Verona': 'Verona',
            'Hellas Verona FC': 'Verona',
            'US Lecce': 'Lecce',
            'AC Monza': 'Monza',
            'Frosinone Calcio': 'Frosinone',
            'US Salernitana 1919': 'Salernitana',
            'Empoli FC': 'Empoli',
            'Cagliari Calcio': 'Cagliari',
            'Parma Calcio 1913': 'Parma',
            'Parma Calcio': 'Parma', # API
            'Parma': 'Parma',
            'Como 1907': 'Como',
            'Venezia FC': 'Venezia',
            'Pisa SC': 'Pisa', # API
            'Sassuolo Calcio': 'Sassuolo', # API

            # --- SPAIN (SP1/SP2 updates) ---
            'Real Betis Seville': 'Betis',
            'RC Celta de Vigo': 'Celta', 
            'Espanyol Barcelona': 'Espanyol',
            'Real Sociedad San Sebastian': 'Sociedad',
            'Real Sociedad San Sebastian B': 'Sociedad B',
            'Real Valladolid': 'Valladolid',
            'Albacete Balompie': 'Albacete',
            'CD Castellon': 'Castellon',
            'RC Deportivo La Coruna': 'Dep. La Coruna',

            # --- NETHERLANDS (N1) ---
            'Ajax Amsterdam': 'Ajax',
            'Feyenoord Rotterdam': 'Feyenoord',
            'PSV Eindhoven': 'PSV',
            'SC Heerenveen': 'Heerenveen',
            'AZ Alkmaar': 'AZ Alkmaar', # Verify Local
            'FC Twente Enschede': 'Twente',
            'FC Groningen': 'Groningen',
            'NEC Nijmegen': 'NEC Nijmegen',
            'PEC Zwolle': 'Zwolle',
            'Sparta Rotterdam': 'Sparta Rotterdam',
            'Excelsior Rotterdam': 'Excelsior',
            'Go Ahead Eagles': 'Go Ahead Eagles',
            'Fortuna Sittard': 'Fortuna Sittard',
            'FC Utrecht': 'Utrecht',
            'FC Volendam': 'Volendam',
            'Heracles Almelo': 'Heracles',
            'SC Telstar': 'Telstar',
            'NAC Breda': 'NAC Breda',
            
            # --- PORTUGAL (P1) ---
            'Santa Clara Azores': 'Santa Clara',
            'Nacional da Madeira': 'Nacional',
            'Moreirense FC': 'Moreirense',
            'CD Tondela': 'Tondela',

            # --- FRANCE (F1) ---
            'AS Monaco': 'Monaco',
            'FC Lorient': 'Lorient',
            'Paris Saint-Germain': 'Paris SG',
            'PSG': 'Paris SG',
            'LOSC Lille': 'Lille',
            'Lille OSC': 'Lille',
            'Olympique de Marseille': 'Marseille',
            'Olympique Marseille': 'Marseille',
            'Stade Brestois 29': 'Brest',
            'Stade Brestois': 'Brest',
            'Stade Rennais FC': 'Rennes',
            'Stade Rennais': 'Rennes',
            'OGC Nice': 'Nice',
            'FC Nantes': 'Nantes',
            'RC Strasbourg Alsace': 'Strasbourg',
            'Strasbourg Alsace': 'Strasbourg',
            'Montpellier HSC': 'Montpellier',
            'Toulouse FC': 'Toulouse',
            'Stade de Reims': 'Reims',
            'RC Lens': 'Lens',
            'AJ Auxerre': 'Auxerre',
            'Angers SCO': 'Angers',
            'AS Saint-Etienne': 'St Etienne',
            'Saint-Etienne': 'St Etienne',
            'Le Havre AC': 'Le Havre',
            'Olympique Lyon': 'Lyon',
            'Olympique Lyonnais': 'Lyon',
            'FC Metz': 'Metz',
        }
        return mapping.get(name, name)
