import pandas as pd
import requests
import time
import random
import os

class FBrefLoader:
    # FBref URLs Structure
    # https://fbref.com/en/comps/12/La-Liga-Stats
    # Standard Stats: https://fbref.com/en/comps/12/stats/La-Liga-Stats
    # Shooting: https://fbref.com/en/comps/12/shooting/La-Liga-Stats
    
    LEAGUE_IDS = {
        'SP1': ('12', 'La-Liga'),
        'E0': ('9', 'Premier-League'),
        'D1': ('20', 'Bundesliga'),
        'I1': ('11', 'Serie-A'),
        'F1': ('13', 'Ligue-1')
    }
    
    def __init__(self, data_dir="data_cache/fbref"):
        self.data_dir = data_dir
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
    def _fetch_table(self, url):
        print(f"Fetching {url}...")
        try:
            # Random delay to avoid rate limit
            time.sleep(random.uniform(2, 5))
            
            # Use requests to get content
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Referer": "https://fbref.com/",
                "Accept-Language": "en-US,en;q=0.9"
            }
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                print(f"Failed to fetch {url}: {response.status_code}")
                if response.status_code == 429:
                    print("Rate limit hit! Waiting 30s...")
                    time.sleep(30)
                return None
                
            # Parse with pandas, specifying flavor to avoid lxml issues
            dfs = pd.read_html(response.content, flavor='html5lib')
            if dfs:
                # The stats table is usually the first big table
                for df in dfs:
                    if len(df) > 50: # Simple heuristic
                        return df
            return None
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None

    def fetch_player_stats(self, league_code='SP1', season='2024-2025'):
        """
        Scrapes stats for a given league and season.
        Note: Historical seasons have different URLs on FBref.
        For now, let's target the CURRENT season pages as they are easiest.
        """
        if league_code not in self.LEAGUE_IDS:
            print(f"League {league_code} not supported yet.")
            return None
            
        id_num, name_slug = self.LEAGUE_IDS[league_code]
        
        # Standard Stats
        url_std = f"https://fbref.com/en/comps/{id_num}/stats/{name_slug}-Stats"
        df_std = self._fetch_table(url_std)
        
        if df_std is not None:
            # Cleanup MultiIndex if present
            if isinstance(df_std.columns, pd.MultiIndex):
                df_std.columns = ['_'.join(col).strip() for col in df_std.columns.values]
            
            # Save raw
            filename = f"{league_code}_std.csv"
            df_std.to_csv(os.path.join(self.data_dir, filename), index=False)
            print(f"Saved {filename}")
            return df_std
            
        return None

if __name__ == "__main__":
    loader = FBrefLoader()
    df = loader.fetch_player_stats('SP1')
    if df is not None:
        print(df.head())
