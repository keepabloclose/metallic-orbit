
import os
import sys
import pandas as pd
import glob
import time

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))
from utils.logo_manager import LogoManager

def verify_all():
    print("🔍 Starting Verification Process...")
    manager = LogoManager()
    
    # 1. Find Data Files
    files = glob.glob("data_cache/*.csv")
    if not files:
        print("❌ No fixture files found in data_cache/")
        return

    all_teams = set()
    
    # 2. Extract Unique Series of (TeamName, Div)
    for f in files:
        try:
            df = pd.read_csv(f)
            if 'Div' not in df.columns or 'HomeTeam' not in df.columns:
                continue
            
            # Get unique pairs
            pairs = df[['Div', 'HomeTeam']].drop_duplicates().values
            for div, team in pairs:
                all_teams.add((div, team))
                
            pairs_a = df[['Div', 'AwayTeam']].drop_duplicates().values
            for div, team in pairs_a:
                all_teams.add((div, team))
                
        except Exception as e:
            print(f"⚠️ Error reading {f}: {e}")

    print(f"📋 Found {len(all_teams)} unique teams to verify.")
    
    # 3. Verify URLs
    results = {'ok': [], 'fail': []}
    
    # Filter only supported LEAGUES
    supported_divs = manager.LEAGUE_MAP.keys()
    teams_to_check = [t for t in all_teams if t[0] in supported_divs]
    
    print(f"📋 Checking {len(teams_to_check)} teams in supported leagues ({list(supported_divs)})...")
    
    progress = 0
    total = len(teams_to_check)
    
    for div, team in teams_to_check:
        url = manager.get_team_logo(team, div)
        if not url:
            results['fail'].append((div, team, "No URL Generated"))
            continue
            
        is_valid = manager.verify_url(url)
        if is_valid:
            results['ok'].append((div, team, url))
            print(f"✅ [{div}] {team}", end='\r')
        else:
            results['fail'].append((div, team, url))
            print(f"❌ [{div}] {team} -> {url.split('/')[-1]}")
            
        progress += 1
        # time.sleep(0.05) # Rate limit protection

    print("\n\n📊 VALIDATION REPORT 📊")
    print(f"✅ Success: {len(results['ok'])}")
    print(f"❌ Failed:  {len(results['fail'])}")
    
    if results['fail']:
        print("\n📝 MISSING BADGES:")
        for div, team, url in results['fail']:
            print(f"- [{div}] {team}") 
            # Suggest correction?
    
if __name__ == "__main__":
    verify_all()
