
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

def test_scrape_odds_structure():
    url = "https://www.betexplorer.com/football/england/premier-league/"
    print(f"Testing URL: {url}")
    
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get(url)
        time.sleep(5) # Wait for table to load
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        rows = soup.find_all('tr')
        print(f"Found {len(rows)} rows.")
        
        for i, row in enumerate(rows[:10]): # Inspect first 10
            text = row.get_text(strip=True)
            print(f"Row {i}: {text[:100]}...")
            
            # Look for 1X2 data
            # Typically odds are in <span> or <td> with data-odd attribute
            tds = row.find_all('td')
            if len(tds) > 4:
                print(f"  -> Potential Match Row? Cols: {len(tds)}")
                # Try to print specific cells
                # 0: Match (Teams)
                # 1: Score?
                # 2,3,4: Odds? or 5,6,7? BetExplorer structure varies.
                for j, td in enumerate(tds):
                    print(f"     Col {j}: {td.get_text(strip=True)}")
                    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    test_scrape_odds_structure()
