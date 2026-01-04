import requests
import sys
import os
sys.path.append(os.getcwd())
from src.utils.logo_manager import LogoManager

def brute_force():
    manager = LogoManager()
    base = manager.BASE_URL
    league_path = manager.LEAGUE_MAP['SP1'].replace(" ", "%20")
    
    # Check known working to confirm path
    known = "Rayo%20Vallecano.png"
    url = f"{base}/{league_path}/{known}"
    r = requests.head(url)
    print(f"Control (Rayo): {r.status_code}")
    
    variations = {
        'Barcelona': [
            "FC Barcelona.png", "Barcelona.png", "F.C. Barcelona.png", 
            "Futbol Club Barcelona.png", "Barca.png", "FCBarcelona.png",
            "F.C.Barcelona.png", "Barcelona FC.png"
        ],
        'Getafe': [
            "Getafe CF.png", "Getafe.png", "Getafe C.F..png", 
            "Getafe Club de Futbol.png", "Getafe Club de Fútbol.png",
            "Getafe C.F.png"
        ],
        'Real Madrid': [
            "Real Madrid.png", "Real Madrid CF.png", "Real Madrid C.F..png"
        ]
    }
    
    for team, vars in variations.items():
        print(f"\n--- Checking {team} ---")
        for v in vars:
            v_enc = v.replace(" ", "%20")
            url = f"{base}/{league_path}/{v_enc}"
            try:
                r = requests.head(url, timeout=1)
                if r.status_code == 200:
                    print(f"✅ FOUND: {v}")
                    break # Stop if found
                else:
                    print(f"❌ {v}: {r.status_code}")
            except:
                print(f"Error {v}")

if __name__ == "__main__":
    brute_force()
