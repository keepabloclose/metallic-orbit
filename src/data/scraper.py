from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

# Competitions to scrape (Example: Premier League)
# In production, iterate through user's active leagues.
URLS = [
    ("E0", "https://www.betexplorer.com/football/england/premier-league/"),
    ("SP1", "https://www.betexplorer.com/football/spain/laliga/"),
    # Add others as needed
]

def scrape_odds():
    print("Starting odds scraper...")
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    all_odds = []
    
    try:
        for league_code, url in URLS:
            print(f"Scraping {league_code} from {url}...")
            dfs = pd.read_html(driver.page_source)
            print(f"Found {len(dfs)} tables.")
            
            for df_table in dfs:
                # BetExplorer main table usually has columns like 'Match', '1', 'X', '2'
                if 'Match' in df_table.columns and '1' in df_table.columns:
                    print("Found Odds Table!")
                    # Clean up
                    for idx, row in df_table.iterrows():
                        match_text = str(row['Match'])
                        if "-" in match_text:
                            teams = match_text.split("-")
                            if len(teams) >= 2:
                                home = teams[0].strip()
                                away = teams[1].strip()
                                # Some weird parsing might be needed for dates attached to names
                                
                                try:
                                    odd_1 = float(row['1'])
                                    odd_x = float(row['X'])
                                    odd_2 = float(row['2'])
                                    
                                    all_odds.append({
                                        'League': league_code,
                                        'HomeTeam': home,
                                        'AwayTeam': away,
                                        'Real_B365H': odd_1,
                                        'Real_B365D': odd_x,
                                        'Real_B365A': odd_2
                                    })
                                except:
                                    continue
                    break # Stop after finding main table
                    
    except Exception as e:
        print(f"Scrape Error: {e}")
    finally:
        driver.quit()
        
    df = pd.DataFrame(all_odds)
    print(f"Scraped {len(df)} matches.")
    
    out_path = os.path.join(os.getcwd(), 'src', 'data', 'real_odds.csv')
    df.to_csv(out_path, index=False)
    print(f"Saved to {out_path}")

if __name__ == "__main__":
    scrape_odds()
