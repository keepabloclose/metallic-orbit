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
            
            # BetExplorer often puts fixtures in a specific container.
            # Try appending 'fixtures/' to URL if not present to ensure we get lists
            if 'fixtures' not in url and 'results' not in url:
                if not url.endswith('/'): url += '/'
                url += 'fixtures/'
            
            print(f"Scraping corrected URL: {url}")
            driver.get(url)
            time.sleep(3)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Match rows typically have 'data-dt' attribute (match ID/timestamp)
            rows = soup.find_all('tr')
            
            current_date = pd.Timestamp.now().normalize()
            
            for row in rows:
                # 1. Date Header Check
                if 'table-main__heading' in row.get('class', []):
                    # Extract date
                    txt = row.get_text()
                    # Parse logic...
                    pass
                
                # 2. Match Row Check
                # Look for team names and odds
                # Cells: [Status/Time, Teams, Result/-, 1, X, 2]
                cells = row.find_all('td')
                
                # BetExplorer Fixtures Table usually has:
                # 0: Time
                # 1: Match (Home - Away)
                # 2: Score (or -)
                # 3: Odds 1
                # 4: Odds X
                # 5: Odds 2
                
                if len(cells) >= 6:
                    # Check if it's a match row
                    teams_cell = row.find('td', class_='h-text-left')
                    if teams_cell and '-' in teams_cell.get_text():
                        # Extract Teams
                        teams_txt = teams_cell.get_text(strip=True)
                        parts = teams_txt.split('-')
                        if len(parts) >= 2:
                            home = parts[0].strip()
                            away = parts[1].strip()
                            
                            # Extract Odds
                            # These are usuallly in cells with data-odd
                            try:
                                # Start searching from cell index 
                                # This requires inspecting the specific layout relative to 'h-text-left'
                                # Heuristic: The cells AFTER the team cell are usually 1, X, 2
                                team_idx = cells.index(teams_cell)
                                odd_1 = cells[team_idx + 2].get_text(strip=True)
                                odd_x = cells[team_idx + 3].get_text(strip=True)
                                odd_2 = cells[team_idx + 4].get_text(strip=True)
                                
                                # Validate they look like numbers
                                if odd_1 == '-' or odd_1 == '': odd_1 = None
                                if odd_x == '-' or odd_x == '': odd_x = None
                                if odd_2 == '-' or odd_2 == '': odd_2 = None
                                
                                matches.append({
                                    'Div': league_code,
                                    'Date': current_date, # Fallback, needs DATE header parsing logic ideally
                                    'HomeTeam': home, 
                                    'AwayTeam': away,
                                    'B365H': float(odd_1) if odd_1 else None,
                                    'B365D': float(odd_x) if odd_x else None,
                                    'B365A': float(odd_2) if odd_2 else None
                                })
                            except:
                                pass
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

