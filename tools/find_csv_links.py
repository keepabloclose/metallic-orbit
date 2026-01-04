
import requests
import re
import urllib3

# Suppress warnings as requested
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def find_links():
    base = "https://www.football-data.co.uk"
    pages = {
        "Spain": f"{base}/spainm.php",
        "England": f"{base}/englandm.php"
    }
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for country, url in pages.items():
        print(f"\nScanning {country} ({url})...")
        try:
            r = requests.get(url, headers=headers, verify=False, timeout=10)
            if r.status_code == 200:
                content = r.text
                # Look for ANY .csv links
                # Pattern often: <a href="mmz4281/2526/SP2.csv"> or just "SP2.csv"
                links = re.findall(r'href=["\']?([^"\'>]+\.csv)["\']?', content, re.IGNORECASE)
                
                print(f"Found {len(links)} CSV links.")
                for link in links:
                    full_link = f"{base}/{link}"
                    if "2526" in link: # Prioritize 2526 season
                         print(f"  [POTENTIAL] {full_link}")
                    elif "2425" in link:
                         print(f"  [OLD] {full_link}")
                         
            else:
                print(f"Failed to load page: {r.status_code}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    find_links()
