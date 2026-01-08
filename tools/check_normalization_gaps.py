import sys
import os
import pandas as pd
import time

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))
sys.path.append(os.getcwd())

from src.data.upcoming import FixturesFetcher
from src.data.odds_api_client import OddsApiClient
from src.utils.normalization import NameNormalizer

def check_gaps():
    leagues = ['E0', 'E1', 'SP1', 'SP2', 'D1', 'I1', 'F1']
    
    fetcher = FixturesFetcher()
    client = OddsApiClient()
    
    print("🔎 STARTING GLOBAL NORMALIZATION CHECK...")
    print("="*60)
    
    gaps_found = {}
    
    for league in leagues:
        print(f"\nProcessing {league}...")
        
        # 1. Get Local Fixtures (The 'Target' names)
        # Note: fetch_upcoming usually returns a few match days.
        fixtures = fetcher.fetch_upcoming([league])
        if fixtures.empty:
            print(f"  ⚠️ No local fixtures found for {league}. Skipping.")
            continue
            
        # Get set of Normalized Local Teams
        local_teams = set(fixtures['HomeTeam'].unique()) | set(fixtures['AwayTeam'].unique())
        print(f"  ✅ Local Teams Loaded: {len(local_teams)}")
        
        # 2. Get API Odds (The 'Source' names)
        # Force refresh to ensure we see the raw API names (before internal norm, actually internal norm happens inside client)
        # Wait, OddsApiClient normalizes internally. 
        # We need to see if the *Normalized* API name matches the *Normalized* Local name.
        # If Client.normalize(API_Name) != Local_Name, then the merge fails.
        
        odds_df = client.get_upcoming_odds(league, days_ahead=7)
        if odds_df.empty:
            print(f"  ⚠️ No odds data found for {league}.")
            continue
            
        api_teams = set(odds_df['HomeTeam'].unique()) | set(odds_df['AwayTeam'].unique())
        print(f"  ✅ API Teams Loaded: {len(api_teams)}")
        
        # 3. Find Mismatches
        # Mismatch = An API team name that exists in Odds DF but corresponds to NOTHING in Local DF
        # This implies NameNormalizer didn't map it to the "Official" name used in CSV.
        
        league_gaps = []
        for t in api_teams:
            # Fuzzy check? No, exact match required for merge.
            if t not in local_teams:
                # Try to find a "Similar" team in local to suggest a mapping
                import difflib
                matches = difflib.get_close_matches(t, local_teams, n=1, cutoff=0.6)
                sim = matches[0] if matches else "???"
                league_gaps.append((t, sim))
        
        if league_gaps:
            print(f"  ❌ GAPS FOUND: {len(league_gaps)}")
            for gap in league_gaps:
                print(f"     API: '{gap[0]}'  --> Local: '{gap[1]}' (Missing Mapping?)")
            gaps_found[league] = league_gaps
        else:
            print("  ✅ No gaps. Perfect match.")
            
    print("\n" + "="*60)
    print("SUMMARY OF REQUIRED FIXES:")
    for l, gaps in gaps_found.items():
        print(f"\n[{l}]")
        for g in gaps:
            print(f"'{g[0]}': '{g[1]}',")

if __name__ == "__main__":
    check_gaps()
