import requests
import pandas as pd
from datetime import datetime
import streamlit as st

class CupLoader:
    def __init__(self):
        self.base_url = "https://fixturedownload.com/feed/json/"
        # Map of competitions to their URL slug for 2024-2025 season
        # Note: fixturedownload usually uses the start year, e.g. 2024 for 24/25
        self.competitions = {
            'Champions League': 'champions-league-2024',
            'Europa League': 'europa-league-2024',
            'Conference League': 'conference-league-2024',
            'Copa del Rey': 'copa-del-rey-2024',
            'FA Cup': 'fa-cup-2024',
            'Coppa Italia': 'coppa-italia-2024',
            'DFB Pokal': 'dfb-pokal-2024',
            'Coupe de France': 'coupe-de-france-2024' # Check if this exists, but harmless if distinct
        }
        
    @st.cache_data(ttl=3600*12) # Cache for 12 hours
    def fetch_all_cups(_self):
        """
        Fetches all defined cups and returns a single DataFrame of [Date, Team]
        representing the schedule of all teams in these competitions.
        """
        all_matches = []
        
        for name, slug in _self.competitions.items():
            try:
                url = f"{_self.base_url}{slug}"
                # mask requests to avoid simple bot detection if necessary, though API seems open
                headers = {'User-Agent': 'Mozilla/5.0'} 
                response = requests.get(url, headers=headers, timeout=5)
                
                if response.status_code == 200:
                    matches = response.json()
                    for m in matches:
                        # Parse date
                        # Format is usually "2024-09-17 16:45:00"
                        if 'DateUtc' in m:
                            date_str = m['DateUtc']
                            
                            # Add Home Team Schedule
                            all_matches.append({
                                'Date': date_str,
                                'Team': m['HomeTeam'],
                                'Comp': name
                            })
                            # Add Away Team Schedule
                            all_matches.append({
                                'Date': date_str,
                                'Team': m['AwayTeam'],
                                'Comp': name
                            })
            except Exception as e:
                print(f"Error fetching {name}: {e}")
                continue
                
        if not all_matches:
            return pd.DataFrame(columns=['Date', 'Team', 'Comp'])
            
        df = pd.DataFrame(all_matches)
        df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None) # Remove timezone for compatibility
        return df.drop_duplicates()
