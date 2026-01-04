from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import datetime
import os

class BetExplorerScraper:
    URLS = {
        "E0": "https://www.betexplorer.com/football/england/premier-league/",
        "E1": "https://www.betexplorer.com/football/england/championship/",
        "SP1": "https://www.betexplorer.com/football/spain/laliga/",
        "SP2": "https://www.betexplorer.com/football/spain/laliga2/",
        "D1": "https://www.betexplorer.com/football/germany/bundesliga/",
        "I1": "https://www.betexplorer.com/football/italy/serie-a/",
        "F1": "https://www.betexplorer.com/football/france/ligue-1/",
    }

    def __init__(self):
        self.options = Options()
        self.options.add_argument("--headless=new")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

    def scrape_next_matches(self, url=None, league_code=None):
        if not url and league_code:
            url = self.URLS.get(league_code)
        
        if not url:
            print("No URL provided.")
            return pd.DataFrame()

        print(f"Scraping {url}...")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
        
        matches = []
        try:
            driver.get(url)
            time.sleep(3) # Wait for JS
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # BetExplorer lists matches in a table.
            # Rows usually have data-dt (timestamp)
            
            # BetExplorer lists matches in a table.
            # Headers often contain the date. Rows contain matches.
            
            rows = soup.find_all('tr')
            current_date = pd.Timestamp.now().normalize()
            
            for row in rows:
                # Check for date header
                # Usually <th ...> ... </th>
                if row.find('th'):
                    header_text = row.get_text(strip=True)
                    # Try to parse date from header like "03.01.2026" or "Saturday, 03 January 2026"
                    # BetExplorer format varies. Let's assume DD.MM.YYYY if present.
                    try:
                         # Simple heuristic: split by space, check for dates
                         # or regex search
                         import re
                         date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', header_text)
                         if date_match:
                             d_str = date_match.group(1)
                             current_date = pd.to_datetime(d_str, dayfirst=True)
                    except:
                        pass
                    continue
                
                # Check for match row
                team_cells = row.find_all('td', class_='h-text-left')
                if team_cells:
                    text = team_cells[0].get_text(strip=True)
                    if '-' in text:
                        parts = text.split('-')
                        home = parts[0].strip()
                        away = parts[1].strip()
                        
                        matches.append({
                            'Div': league_code,
                            'HomeTeam': home,
                            'AwayTeam': away,
                            'Date': current_date,
                            'Time': '12:00' # Scraper hard/impossible to get time accurately without more parsing
                        })
                        
        except Exception as e:
            print(f"Scrape Error: {e}")
        finally:
            driver.quit()
            
        return pd.DataFrame(matches)

# Keep legacy function if needed, or wrap it
def scrape_odds():
    scraper = BetExplorerScraper()
    # ... logic to run for all leagues ...
    pass

