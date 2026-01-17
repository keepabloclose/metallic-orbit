import pandas as pd
import requests
import io
import datetime
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class FixturesFetcher:
    # Mappings for fixturedownload.com
    # Current date is Dec 2025, so we need 2025-2026 season.
    # Usually format is 'league-2025'.
    LEAGUE_URLS = {
        'E0': 'epl-2025',
        'SP1': 'la-liga-2025',
        'D1': 'bundesliga-2025',
        'I1': 'serie-a-2025',
        'F1': 'ligue-1-2025',
        'SP2': 'la-liga-2-2025', # Corrected from segunda-division-2025
        'E1': 'championship-2025'
    }
    
    BASE_URL = "https://fixturedownload.com/download"

    def fetch_upcoming(self, leagues=['E0', 'SP1']):
        upcoming_matches = []
        
        for league_code in leagues:
            if league_code not in self.LEAGUE_URLS:
                continue
                
            slug = self.LEAGUE_URLS[league_code]
            url = f"{self.BASE_URL}/{slug}-GMTStandardTime.csv"
            print(f"Fetching fixtures from {url}...")
            
            # Track success for this specific league to determine if fallback is needed
            current_league_success = False

            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                response = requests.get(url, headers=headers, verify=False) # Skip SSL verify if needed
                if response.status_code == 200:
                    df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
                    # Columns usually: Match Number, Round Number, Date, Location, Home Team, Away Team, Result
                    
                    # Normalize columns
                    df = df.rename(columns={'Home Team': 'HomeTeam', 'Away Team': 'AwayTeam'})
                    
                    # Normalize Team Names to match Historical Data
                    import importlib
                    import src.utils.normalization as norm_module
                    importlib.reload(norm_module) # FORCE RELOAD to pick up 'Brighton' fix
                    NameNormalizer = norm_module.NameNormalizer
                    
                    df['HomeTeam'] = df['HomeTeam'].apply(NameNormalizer.normalize)
                    df['AwayTeam'] = df['AwayTeam'].apply(NameNormalizer.normalize)
                    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
                    df['Time'] = df['Date'].dt.strftime('%H:%M')
                    df['Div'] = league_code
                    
                    # Filter for future matches
                    # Relaxed Filter: Include ALL games from the start of the current UTC day
                    # This ensures Today's games (and odds) are visible regardless of time
                    cutoff_time = now_utc.normalize() # Midnight UTC
                    future = df[df['Date'] >= cutoff_time].sort_values('Date').head(15)
                    
                    today_csv = len(future[future['Date'].dt.date == pd.Timestamp.utcnow().date()])
                    print(f"[{league_code}] CSV matches today: {today_csv}")
                    
                    # PROACTIVE INJECTION: Check API for missing games (today/tomorrow)
                    # Because CSV might be stale or missing games.
                    future = self._inject_missing_from_api(future, league_code, days_ahead=6)
                    
                    upcoming_matches.append(future)
                    current_league_success = True
                else:
                    print(f"Failed to download {url}: {response.status_code}")
            except Exception as e:
                print(f"Error fetching {slug}: {e}")
            
            # FALLBACK: If CSV failed (404 or Exception), try Scraper OR Manual Injection
            if not current_league_success:
                print(f"CSV fetch failed for {slug}. trying Fallback...")
                
                # Generic Scraper Fallback
                print(f"CSV fetch failed for {slug}. trying Fallback...")
                
                # SPECIAL OVERRIDE FOR SP2 (User Request "Jornada 20")
                if league_code == 'SP2':
                    print("Using Manual Injection for SP2 (Jornada 20)")
                    manual_sp2 = self._get_manual_sp2_fixtures()
                    
                    # Check if valid for future?
                    now_utc = pd.Timestamp.utcnow().tz_localize(None)
                    if manual_sp2[manual_sp2['Date'] > now_utc].empty:
                        print("Manual SP2 data is stale. Trying Scraper...")
                    else:
                        upcoming_matches.append(manual_sp2)
                        continue 
                        
                # NEW: Try API Injection First (Empty DF)
                # If CSV is down, we can still build the schedule from API!
                try:
                    empty_df = pd.DataFrame(columns=['Date', 'Time', 'HomeTeam', 'AwayTeam', 'Div'])
                    injected_df = self._inject_missing_from_api(empty_df, league_code, days_ahead=6)
                    
                    if not injected_df.empty:
                        print(f"[{league_code}] Recovered {len(injected_df)} matches via API Injection (CSV Fallback).")
                        upcoming_matches.append(injected_df)
                        current_league_success = True
                        continue # Skip scraper
                except Exception as e:
                    print(f"API Fallback Injection failed: {e}")

                # If API also failed/empty, proceed to Scraper...
                try:
                    from src.data.scraper import BetExplorerScraper
                    scraper = BetExplorerScraper()
                    scraped_df = scraper.scrape_next_matches(league_code=league_code)
                    if not scraped_df.empty:
                        # Normalize Scraper Names too!
                        import src.utils.normalization as norm_module
                        NameNormalizer = norm_module.NameNormalizer
                        
                        if 'HomeTeam' in scraped_df.columns:
                            scraped_df['HomeTeam'] = scraped_df['HomeTeam'].apply(NameNormalizer.normalize)
                        if 'AwayTeam' in scraped_df.columns:
                            scraped_df['AwayTeam'] = scraped_df['AwayTeam'].apply(NameNormalizer.normalize)
                            
                        print(f"Fallback successful: {len(scraped_df)} matches (Normalized).")
                        upcoming_matches.append(scraped_df)
                    else:
                            print("Fallback Scraper also returned no matches.")
                except Exception as e:
                    print(f"Fallback Scraper Error: {e}")
                
        if not upcoming_matches:
            # Return dummy data if fetch fails, so the user sees SOMETHING
            print("No live fixtures found (or fetch failed). Using Mock Data for demonstration.")
            return self._get_mock_fixtures()
            
        final_df = pd.concat(upcoming_matches, ignore_index=True)
        
        if True: # FORCE ENRICHMENT ALWAYS to ensure fresh API odds override CSV stales
            # was: if 'B365H' not in final_df.columns or final_df['B365H'].isna().mean() > 0.5:
            print("Enriching via Odds-API.io (Forced Freshness)...")
            try:
                from src.data.odds_api_client import OddsApiClient
                client = OddsApiClient()
                
                leagues_to_enrich = final_df['Div'].unique()
                all_api_odds = []
                
                for league in leagues_to_enrich:
                    print(f"  Fetching API Odds for {league} (Today/Tomorrow priority)...")
                    odds_df = client.get_upcoming_odds(league, days_ahead=2)
                    if not odds_df.empty:
                        all_api_odds.append(odds_df)
                
                if all_api_odds:
                    enrichment_df = pd.concat(all_api_odds)
                    # DEDUPLICATION: Prevent Merge Explosion if Odds DB has multiple entries
                    # Keep the LAST entry (Latest odds)
                    enrichment_df = enrichment_df.drop_duplicates(subset=['HomeTeam', 'AwayTeam'], keep='last')

                    # DYNAMIC MERGE of all B365 columns found
                    # API now returns variable columns like B365_Over3.5, B365_Under1.5 etc.
                    # We merge ALL of them.
                    
                    enrichment_df['HomeTeam'] = enrichment_df['HomeTeam'].apply(NameNormalizer.normalize)
                    enrichment_df['AwayTeam'] = enrichment_df['AwayTeam'].apply(NameNormalizer.normalize)
                    
                    enrichment_df['MergeKey'] = enrichment_df['HomeTeam'] + "_" + enrichment_df['AwayTeam']
                    final_df['MergeKey'] = final_df['HomeTeam'] + "_" + final_df['AwayTeam']
                    
                    # Identify all valid Odds columns from API response
                    odds_cols = [c for c in enrichment_df.columns if c.startswith('B365') and c not in ['MergeKey']]
                    
                    # STRATEGY CHANGE: Wipe existing odds in final_df to prevent stale collisions
                    # The user wants ONLY API odds.
                    for oc in odds_cols:
                        if oc in final_df.columns:
                             final_df[oc] = None # Wipe it out to force API value or NaN

                    # Merge
                    # We left merge to keep fixtures, but bring in odds
                    merged = final_df.merge(enrichment_df[['MergeKey'] + odds_cols], on='MergeKey', how='left', suffixes=('', '_api'))
                    
                    # Fill NaNs dynamically for all found columns
                    for col in odds_cols:
                        api_col = f"{col}_api"
                        if api_col in merged.columns:
                            # If col didn't exist in original, just use api values
                            if col not in merged.columns:
                                merged[col] = merged[api_col]
                            else:
                                # PRIORITIZE API ODDS (Live) over CSV (Static)
                                # If API has a value, use it. Else fallback to CSV.
                                merged[col] = merged[api_col].fillna(merged.get(col))
                            
                    final_df = merged.drop(columns=[c for c in merged.columns if c.endswith('_api')])
                        
                    print(f"API Enrichment Complete. Merged {len(odds_cols)} odds columns.")

            except Exception as e:
                print(f"API Enrichment Failed: {e}")
                # Optional: st.warning(f"Live odds update failed: {e}")
                
        # Fallback to Scraper if still bad?
        # (Optional: Only if API failed completely)

        # UNION with Real Odds CSV (Legacy/Manual Override)
        try:
            import os
            real_odds_path = os.path.join(os.path.dirname(__file__), 'real_odds.csv')
            if os.path.exists(real_odds_path):
                real_odds_df = pd.read_csv(real_odds_path)
                # Merge
                final_df = pd.merge(final_df, real_odds_df[['HomeTeam', 'AwayTeam', 'Real_B365H', 'Real_B365D', 'Real_B365A']], 
                                    on=['HomeTeam', 'AwayTeam'], how='left')
                
                # Fill gaps
                if 'Real_B365H' in final_df.columns:
                     final_df['B365H'] = final_df['B365H'].fillna(final_df['Real_B365H'])
                     final_df['B365D'] = final_df['B365D'].fillna(final_df['Real_B365D'])
                     final_df['B365A'] = final_df['B365A'].fillna(final_df['Real_B365A'])

                print("Merged Real Odds CSV successfully.")
        except Exception as e:
            print(f"Error merging real odds: {e}")
            
        return final_df

    def _get_manual_sp2_fixtures(self):
        """
        Returns the specific 'Jornada 21' list (Real Schedule).
        Ref: User Screenshot (Jan 8 2026 -> Start Jan 9 Friday).
        """
        # Base Date: Friday Jan 9, 2026
        fri = pd.Timestamp("2026-01-09").normalize()
        sat = fri + pd.Timedelta(days=1)
        sun = fri + pd.Timedelta(days=2)
        mon = fri + pd.Timedelta(days=3)
        
        data = [
            # Viernes 9/1
            {'Div': 'SP2', 'Date': fri, 'Time': '20:30', 'HomeTeam': 'Cadiz', 'AwayTeam': 'Sp Gijon'},
            
            # Sabado 10/1
            {'Div': 'SP2', 'Date': sat, 'Time': '14:00', 'HomeTeam': 'Mirandes', 'AwayTeam': 'Almeria'},
            {'Div': 'SP2', 'Date': sat, 'Time': '16:15', 'HomeTeam': 'Andorra', 'AwayTeam': 'Cultural Leonesa'},
            {'Div': 'SP2', 'Date': sat, 'Time': '16:15', 'HomeTeam': 'Sociedad B', 'AwayTeam': 'Albacete'},
            {'Div': 'SP2', 'Date': sat, 'Time': '18:30', 'HomeTeam': 'Burgos', 'AwayTeam': 'Eibar'},
            {'Div': 'SP2', 'Date': sat, 'Time': '18:30', 'HomeTeam': 'Las Palmas', 'AwayTeam': 'Dep. La Coruna'},
            {'Div': 'SP2', 'Date': sat, 'Time': '21:00', 'HomeTeam': 'Santander', 'AwayTeam': 'Zaragoza'},
            # {'Div': 'SP2', 'Date': sat, 'Time': '14:00', 'HomeTeam': 'Leganes', 'AwayTeam': 'Valladolid'}, # Removed Dupe
            
            # Domingo 11/1
            {'Div': 'SP2', 'Date': sun, 'Time': '14:00', 'HomeTeam': 'Leganes', 'AwayTeam': 'Valladolid'},
            
            {'Div': 'SP2', 'Date': sun, 'Time': '16:15', 'HomeTeam': 'Malaga', 'AwayTeam': 'Ceuta'},
            {'Div': 'SP2', 'Date': sun, 'Time': '16:15', 'HomeTeam': 'Granada', 'AwayTeam': 'Castellon'},
            
            # Lunes 12/1
            {'Div': 'SP2', 'Date': mon, 'Time': '20:30', 'HomeTeam': 'Huesca', 'AwayTeam': 'Cordoba'},
        ]
        # Clean double entry for Leganes if I made mistake above - corrected.
        
        return pd.DataFrame(data)

    
    def _inject_missing_from_api(self, df, league_code, days_ahead=2):
        """
        Fetches events from Odds API and injects them if missing from existing DF.
        Crucial for when CSV source is stale.
        """
        try:
            from src.data.odds_api_client import OddsApiClient
            from src.utils.normalization import NameNormalizer
            
            client = OddsApiClient()
            
            # 1. Fetch Events (Raw list)
            # Strategy: Use get_upcoming_odds logic but just extract events first to check keys
            # Or assume we can get them.
            
            # Since OddsApiClient returns a DataFrame of ODDS, we can use that!
            # It normally returns ALL upcoming matches it finds.
            
            odds_df = client.get_upcoming_odds(league_code, days_ahead=days_ahead)
            if odds_df.empty: return df
            
            # 2. Compare against CSV (df)
            # Create unique keys
            existing_keys = set(zip(df['HomeTeam'], df['AwayTeam']))
            
            new_rows = []
            
            now_utc = pd.Timestamp.utcnow().tz_localize(None)
            
            # 2. Iterate and Inject
            for _, row in odds_df.iterrows():
                h_norm = row['HomeTeam']
                a_norm = row['AwayTeam']
                
                # Check exist
                if (h_norm, a_norm) in existing_keys: continue
                
                # Check Date
                date_str = row.get('Date')
                if not date_str: continue
                
                try:
                    dt = pd.to_datetime(date_str).tz_convert(None) # UTC
                except: continue
                
                if pd.isna(dt): continue # Handle failures
                
                # Filter (Active & Within limit)
                # Note: get_upcoming_odds already filters by days_ahead mostly, but double check
                if dt < (now_utc - pd.Timedelta(hours=4)): continue
                if dt > (now_utc + pd.Timedelta(days=days_ahead + 1)): continue 

                print(f"[{league_code}] Injecting missing match (+Odds): {h_norm} vs {a_norm}")
                
                # Create Row
                new_row = {
                    'Div': league_code,
                    'Date': dt,
                    'Time': dt.strftime('%H:%M'),
                    'HomeTeam': h_norm,
                    'AwayTeam': a_norm,
                    'FTHG': None, 'FTAG': None, 'FTR': None,
                    'B365H': row.get('B365H'),
                    'B365D': row.get('B365D'),
                    'B365A': row.get('B365A'),
                    'B365_BTTS_Yes': row.get('B365_BTTS_Yes'),
                    'B365_BTTS_No': row.get('B365_BTTS_No')
                }
                
                # Add Totals if present in row
                for k, v in row.items():
                    if str(k).startswith('B365_') and k not in new_row:
                        new_row[k] = v
                        
                new_rows.append(new_row)

            if new_rows:
                print(f"[{league_code}] Injected {len(new_rows)} matches.")
                return pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
            
            return df

        except Exception as e:
            print(f"Injection Error {league_code}: {e}")
            return df

