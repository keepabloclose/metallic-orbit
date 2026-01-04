import pandas as pd
import requests
import io
import os

class DataLoader:
    BASE_URL = "https://www.football-data.co.uk/mmz4281"
    
    def __init__(self, cache_dir="data_cache"):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def fetch_data(self, leagues, seasons):
        """
        Fetches data for given leagues and seasons.
        Returns a single concatenated DataFrame.
        """
        all_data = []
        
        for season in seasons:
            for league in leagues:
                url = f"{self.BASE_URL}/{season}/{league}.csv"
                print(f"Fetching {league} {season} from {url}...")
                
                try:
                    # Try local cache first
                    cache_path = os.path.join(self.cache_dir, f"{league}_{season}.csv")
                    if os.path.exists(cache_path):
                        df = pd.read_csv(cache_path)
                    else:
                        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                        response = requests.get(url, headers=headers)
                        response.raise_for_status()
                        # Use latin-1 for football-data.co.uk to handle accents correctly
                        df = pd.read_csv(io.StringIO(response.content.decode('latin-1')))
                        # Save to cache
                        df.to_csv(cache_path, index=False)
                    
                    # Ensure Date parsing
                    if 'Date' in df.columns:
                        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
                        
                    # Add metadata columns
                    if 'Div' not in df.columns:
                        df['Div'] = league
                        
                    df['Season'] = season
                    all_data.append(df)
                    
                except Exception as e:
                    print(f"Error fetching {league} {season}: {e}")
        
        if not all_data:
            return pd.DataFrame()
            
        return pd.concat(all_data, ignore_index=True)
