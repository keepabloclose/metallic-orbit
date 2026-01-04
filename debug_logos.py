import sys
import os
import requests

sys.path.append(os.getcwd())
from src.utils.logo_manager import LogoManager

def check_logos():
    print("--- CHECKING LOGO URLS ---")
    manager = LogoManager()
    
    # Teams to check (Focus on Spanish/English as reported)
    teams_to_check = [
        ('Rayo Vallecano', 'SP1'),
        ('Getafe CF', 'SP1'),
        ('Man Utd', 'E0'),
        ('Newcastle', 'E0'),
        ('Real Madrid', 'SP1'),
        ('Barcelona', 'SP1')
    ]
    
    for team, div in teams_to_check:
        url = manager.get_team_logo(team, div)
        print(f"\nChecking: {team} ({div})")
        print(f"URL: {url}")
        
        if not url:
            print("❌ No URL generated")
            continue
            
        try:
            # Fake Browser
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.head(url, headers=headers, timeout=2)
            if r.status_code == 200:
                print("✅ STATUS 200 OK")
            else:
                print(f"❌ STATUS {r.status_code} (Broken)")
        except Exception as e:
            print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    check_logos()
