import requests
import sys
import os
sys.path.append(os.getcwd())
from src.utils.logo_manager import LogoManager

def check_alternates():
    manager = LogoManager()
    base = manager.BASE_URL
    league_path = manager.LEAGUE_MAP['SP1'].replace(" ", "%20")
    
    candidates = [
        "Getafe.png", "Getafe CF.png", "Getafe C.F..png",
        "Barcelona.png", "FC Barcelona.png", "F.C. Barcelona.png"
    ]
    
    print("--- CHECKING CANDIDATES (SP1) ---")
    for c in candidates:
        c_enc = c.replace(" ", "%20")
        url = f"{base}/{league_path}/{c_enc}"
        try:
            r = requests.head(url, timeout=2)
            status = "✅ 200" if r.status_code == 200 else f"❌ {r.status_code}"
            print(f"{c}: {status}")
        except Exception as e:
            print(f"{c}: Error {e}")

if __name__ == "__main__":
    check_alternates()
