
import sys
import os
import io
import pandas as pd # Verify pandas available

# Add src to path
# Assuming tool is in playground/metallic-orbit/tools/check_scraper.py
# and src is in playground/metallic-orbit/src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.data.scraper import BetExplorerScraper

def check_betexplorer():
    print("Initializing BetExplorer Scraper...")
    scraper = BetExplorerScraper()
    
    # URL for Segunda Division Spain
    # scraper.URLS usually has it
    url = scraper.URLS.get('SP2')
    print(f"Scraping SP2 from: {url}")
    
    try:
        df = scraper.scrape_next_matches(url)
        print(f"Scraped {len(df)} matches.")
        
        if not df.empty:
            print(df.head())
            
            # Check for Eibar
            mask = df['HomeTeam'].str.contains('Eibar', case=False) | df['AwayTeam'].str.contains('Eibar', case=False)
            eibar = df[mask]
            
            if not eibar.empty:
                print("Found Eibar matches:")
                print(eibar)
            else:
                print("Eibar match not found in scraper results.")
        else:
            print("No matches returned from scraper.")
            
    except Exception as e:
        print(f"Scraping failed: {e}")

if __name__ == "__main__":
    check_betexplorer()
