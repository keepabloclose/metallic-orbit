
import requests

def check(url):
    try:
        r = requests.head(url, timeout=2)
        return r.status_code
    except:
        return 999

print("🔍 Debugging Branch and Path...")

# 1. Determine Branch
branches = ['master', 'main']
valid_branch = None

for b in branches:
    url = f"https://raw.githubusercontent.com/luukhopman/football-logos/{b}/README.md"
    code = check(url)
    print(f"Branch '{b}': {code}")
    if code == 200:
        valid_branch = b
        break

if not valid_branch:
    print("❌ Could not determine branch. Exiting.")
    exit()

print(f"✅ Active Branch: {valid_branch}")
BASE = f"https://raw.githubusercontent.com/luukhopman/football-logos/{valid_branch}/logos"

# 2. Determine Structure
tests = [
    # Hypo 1: Country/League/Team
    "ENG/Premier League/Liverpool FC.png",
    "ENG/Premier League/Liverpool.png",
    "England/Premier League/Liverpool.png",
    
    # Hypo 2: Just League
    "Premier League/Liverpool.png",
    "Premier League/Liverpool FC.png",
    
    # Hypo 3: Country Code Only?
    "GB-ENG/Premier League/Liverpool.png",
    
    # Hypo 4: Case sensitivity
    "eng/premier league/liverpool.png",
    
     # Hypo 5: Serie A
    "ITA/Serie A/AC Milan.png",
    "ITA/Serie A/Milan.png",
    "Italia/Serie A/AC Milan.png",
]

for t in tests:
    url = f"{BASE}/{t}".replace(" ", "%20")
    code = check(url)
    if code == 200:
        print(f"✅ FOUND: {t}")
    else:
        print(f"❌ {code}: {t}")
