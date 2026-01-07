
import requests
import json
import os
import time
import pandas as pd
from datetime import datetime, timedelta

class OddsApiClient:
    API_KEY = "e9be0a4fb2370fa9a2b574fccd726c50da0aae8acfd94a4b6c286a92b62345a2"
    BASE_URL = "https://api2.odds-api.io/v3"
    CACHE_DIR = "data_cache/odds_api"
    
    # Mapping commonly used Div codes to Slugs found in audit/docs
    LEAGUE_SLUGS = {
        'E0': 'england-premier-league',
        'E1': 'england-championship',
        'SP1': 'spain-laliga',
        'SP2': 'spain-laliga-2', 
        'D1': 'germany-bundesliga',
        'I1': 'italy-serie-a',
        'F1': 'france-ligue-1',
        'P1': 'portugal-liga-portugal',
        'N1': 'netherlands-eredivisie',
        'B1': 'belgium-pro-league',
        'SCO': 'scotland-premiership',
        'T1': 'turkey-super-lig', 
        'G1': 'greece-super-league',
    }

    def __init__(self):
        if not os.path.exists(self.CACHE_DIR):
            try:
                os.makedirs(self.CACHE_DIR)
            except:
                pass

    def _get_cache_path(self, key):
        return os.path.join(self.CACHE_DIR, f"{key}.json")

    def _load_cache(self, key, ttl_minutes=60):
        path = self._get_cache_path(key)
        if os.path.exists(path):
            mtime = os.path.getmtime(path)
            if (time.time() - mtime) < (ttl_minutes * 60):
                try:
                    with open(path, 'r') as f:
                        return json.load(f)
                except:
                    pass
        return None

    def _save_cache(self, key, data):
        try:
            path = self._get_cache_path(key)
            with open(path, 'w') as f:
                json.dump(data, f)
        except:
            pass

    # --- PERSISTENCE LAYER (DATABASE) ---
    DB_PATH = "data_cache/odds_database.csv"
    
    def _load_db(self):
        if os.path.exists(self.DB_PATH):
            try:
                df = pd.read_csv(self.DB_PATH)
                # Ensure date parsing if needed, but strings are fine for basic display
                return df
            except:
                return pd.DataFrame()
        return pd.DataFrame()

    def _save_to_db(self, new_df, league_code="UNKNOWN"):
        if new_df.empty: return
        
        # Add Metadata
        new_df['League'] = league_code
        new_df['FetchedAt'] = datetime.utcnow().isoformat()
        
        # Load existing
        existing = self._load_db()
        
        # Combine
        combined = pd.concat([existing, new_df], ignore_index=True)
        
        # Deduplicate (Keep latest based on Teams)
        # We drop old entries for the same match
        if not combined.empty:
             combined = combined.drop_duplicates(subset=['HomeTeam', 'AwayTeam'], keep='last')
        
        # Save
        if not os.path.exists("data_cache"): os.makedirs("data_cache")
        combined.to_csv(self.DB_PATH, index=False)
        print(f"[OddsDB] Saved {len(combined)} records (League: {league_code}) to {self.DB_PATH}")

    def get_upcoming_odds(self, league_code, days_ahead=2, force_refresh=False):
        """
        Fetches odds for the given league.
        Strategy: DB First. Only fetch API if DB is stale (>6h) or empty for this league.
        """
        print(f"[OddsAPI] Getting odds for {league_code} (Next {days_ahead} days)...")
        
        # 0. Check Database Freshness
        db = self._load_db()
        if not db.empty and not force_refresh:
            # Check if we have data for this league
            # Handle case where 'League' col might not exist in old CSV
            if 'League' in db.columns and 'FetchedAt' in db.columns:
                league_data = db[db['League'] == league_code]
                if not league_data.empty:
                    # Check Age of data (using the newest record as proxy)
                    last_fetch = league_data['FetchedAt'].max()
                    try:
                        last_fetch_dt = datetime.fromisoformat(last_fetch)
                        age = datetime.utcnow() - last_fetch_dt
                        if age.total_seconds() < (6 * 3600): # 6 Hours TTL
                            print(f"[OddsAPI] Using Persisted Data from DB (Age: {age}). Skipping API.")
                            return league_data
                        else:
                             print(f"[OddsAPI] DB Data Stale (Age: {age}). Refreshing...")
                    except:
                        pass # Parse error, fetch fresh
        
        slug = self.LEAGUE_SLUGS.get(league_code)
        if not slug:
            print(f"[OddsAPI] No slug for {league_code}")
            return pd.DataFrame()
            
        # Initialize DB fallback (Global scope for function)
        db_fallback = pd.DataFrame()
        if not db.empty:
             db_fallback = db

        # 1. Fetch Events (Standard Logic)
        cache_key = f"events_{league_code}"
        events = self._load_cache(cache_key, 60) # Short cache for events list
        
        # ... (Events Fetch Logic same as before) ...
        if not events:
            try:
                url = f"{self.BASE_URL}/events?apiKey={self.API_KEY}&sport=football&league={slug}"
                res = requests.get(url)
                if res.status_code == 200:
                    data = res.json()
                    events = data.get('data', []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                    self._save_cache(cache_key, events)
                elif res.status_code == 429:
                    print(f"[OddsAPI] Quota Exceeded (429). Using Best Available DB Data.")
                    # Return whatever we have in DB for this league, even if stale
                    if not db.empty and 'League' in db.columns:
                        return db[db['League'] == league_code]
                    return pd.DataFrame()
                else:
                    pass
            except Exception:
                pass
                
        # 2. Extract Event IDs & Filter by Date
        valid_events = []
        now = datetime.utcnow()
        limit_date = now + timedelta(days=days_ahead)
        start_buffer = now - timedelta(hours=2) # Allow matches that started 2h ago
        
        for e in events:
            # Check date
            start_str = e.get('commence_time') or e.get('date')
            
            if start_str:
                try:
                    # Parse "2023-10-15T12:00:00Z"
                    start_dt = datetime.strptime(start_str.replace('Z', ''), "%Y-%m-%dT%H:%M:%S")
                    if start_buffer <= start_dt <= limit_date:
                        valid_events.append(e)
                except:
                    pass
            else:
                pass

        if not valid_events:
            print(f"[OddsAPI] No matches found in next {days_ahead} days. Returning DB.")
            return db_fallback # Return DB in case we missed date filter but DB has them

            
        # 3. Fetch Odds (Batch)
        results = []
        batch_size = 10
        event_ids = [str(e['id']) for e in valid_events]
        print(f"[OddsAPI] Fetching odds for {len(event_ids)} ID(s)...")
        
        # bookmakers_param = "Bet365" # Don't filter, grab all and filter in code
        
        for i in range(0, len(event_ids), batch_size):
            batch = event_ids[i:i+batch_size]
            batch_str = ",".join(batch)
            
            try:
                # Use 'eventIds' (plural) for batch support per documentation
                
                # Calculate variable TTL based on minimum time to kickoff in this batch
                min_seconds_to_start = float('inf')
                for eid in batch:
                    # Find event object
                    ev = next((e for e in valid_events if str(e['id']) == eid), None)
                    if ev:
                        try:
                            start_str = ev.get('commence_time') or ev.get('date') # V3 support
                            if start_str:
                                # ISO 8601 parsing (simple)
                                # API format usually: "2023-10-15T12:00:00Z"
                                dt = datetime.strptime(start_str.replace('Z', ''), "%Y-%m-%dT%H:%M:%S")
                                delta = (dt - now).total_seconds()
                                if delta < min_seconds_to_start: min_seconds_to_start = delta
                        except: pass
                
                # Logic:
                # > 48h away: Cache 12h (720 min)
                # > 24h away: Cache 3h (180 min)
                # > 6h away:  Cache 1h (60 min)
                # < 6h away:  Cache 15 min (Pre-game final checks)
                
                ttl_min = 60 # Default
                if min_seconds_to_start == float('inf'):
                    ttl_min = 60
                elif min_seconds_to_start > 48 * 3600:
                    ttl_min = 720
                elif min_seconds_to_start > 24 * 3600:
                    ttl_min = 180
                elif min_seconds_to_start > 6 * 3600:
                    ttl_min = 60
                else:
                    ttl_min = 15 # Closer to kickoff
                
                print(f"[OddsAPI] Batch TTL: {ttl_min}m (Earliest match in {(min_seconds_to_start/3600):.1f}h)")

                # Check cache for this batch
                batch_cache_key = f"odds_{slug}_{hash(batch_str)}"
                cached_batch = self._load_cache(batch_cache_key, ttl_minutes=ttl_min)
                
                odds_data = []
                if cached_batch:
                    # print(f"[OddsAPI] Batch Cache HIT")
                    odds_data = cached_batch
                else:
                    # Use '/odds/multi' for batch support per documentation
                    # REMOVED strict market filter to get EVERYTHING available (including BTTS if it exists)
                    url = f"{self.BASE_URL}/odds/multi?apiKey={self.API_KEY}&eventIds={batch_str}&bookmakers=Bet365" 
                    res = requests.get(url)
                    
                    if res.status_code == 200:
                        raw = res.json()
                        odds_data = raw if isinstance(raw, list) else [raw]
                        self._save_cache(batch_cache_key, odds_data)
                        print(f"[OddsAPI] Batch {i}: Fetched {len(odds_data)} items. (TTL: {ttl_min}m)")
                        time.sleep(1.2) # Throttling
                    else:
                        print(f"[OddsAPI] Batch {i} failed: {res.status_code} {res.text}")
                
                for item in odds_data:
                    parsed = self._parse_match_odds(item)
                    if parsed:
                        results.append(parsed)
                    else:
                         # print(f"[OddsAPI] Item {item.get('id')} parsed but returned None (likely no Bet365 odds yet)")
                         pass
                        
            except Exception as e:
                print(f"[OddsAPI] Batch fetch error: {e}")
                
        print(f"[OddsAPI] Total results: {len(results)}")
        
        df = pd.DataFrame(results)
        
        # Save to DB for persistence
        self._save_to_db(df, league_code)
        
        return df

    # ... (NAME_MAPPING remains the same) ...

    # Updated to use centralized NameNormalizer
    from src.utils.normalization import NameNormalizer

    def _normalize_name(self, name):
         return self.NameNormalizer.normalize(name)

    def _parse_match_odds(self, item):
        # item is the event object with 'bookmakers' dict
        # item: { id, home, away, bookmakers: { '10BET': [...], ... } }
        
        try:
            raw_home = item.get('home') or item.get('home_team')
            raw_away = item.get('away') or item.get('away_team')
            
            # Use Centralized Normalizer
            from src.utils.normalization import NameNormalizer
            home_team = NameNormalizer.normalize(raw_home)
            away_team = NameNormalizer.normalize(raw_away)
            
            # DEBUG
            # print(f"[TRACE PARSE] '{raw_home}' -> '{home_team}'")
            
            bookmakers = item.get('bookmakers', {})
            if not bookmakers: return None
            
            # Strict bet365 check
            found_bookie = None
            
            # API might return 'bet365', 'Bet365', 'Bet365 (no latency)'
            for b_key in bookmakers.keys():
                if 'bet365' in b_key.lower():
                    found_bookie = bookmakers[b_key]
                    break
            
            if not found_bookie: return None
            
            # Parse Markets
            b365_h, b365_d, b365_a = None, None, None
            b365_btts_yes, b365_btts_no = None, None
            
            # Dynamic Totals Storage
            totals_dict = {} # Stores "B365_Over1.5": price, "B365_Under1.5": price, "B365_Home_Over0.5": price etc.
            
            for m in found_bookie:
                # V3 Schema: 'key' might be 'Goals Over/Under', 'Match Winner'
                # V4 Schema: 'key' is 'totals', 'h2h'
                raw_key = m.get('key', '').lower()
                m_name = m.get('name', '').lower()
                
                # DEBUG: Trace all markets
                print(f"MARKET_SCAN: key='{raw_key}' name='{m_name}'") # Comment out to reduce noise if needed
                
                # if 'both teams' in m_name:
                #      print(f"*** BTTS MARKET: '{m_name}' ***")
                #      for o in m.get('outcomes', []):
                #          print(f"   Outcome: '{o.get('name')}' | Price: {o.get('price')}")
                
                # Normalize keys
                m_key = raw_key
                # RELAXED PARSING (V3/Proxy compatibility)
                name_l = m_name
                
                if 'goals over/under' in raw_key or 'goals over/under' in name_l: m_key = 'totals'
                elif 'match winner' in raw_key or '1x2' in raw_key or 'match winner' in name_l: m_key = 'h2h'
                elif 'ml' == raw_key or 'ml' == name_l or 'moneyline' in name_l: m_key = 'h2h' # FIX: Capture ML market
                
                if 'both teams' in name_l and 'half' in name_l:
                    pass # Ignore half-time BTTS
                elif 'btts' in raw_key or 'both teams to score' in name_l or 'both teams' in name_l: 
                    m_key = 'btts'
                
                # Catch-all for totals (e.g. "Alternative Match Goals", "Match Goals")
                elif 'total' in name_l and ('goal' in name_l or 'match' in name_l): m_key = 'totals'
                elif 'alternative' in name_l and 'goal' in name_l: m_key = 'totals'
                
                # 1. Match Result (1x2)
                if m_key == 'h2h':
                    odds_list = m.get('outcomes') or m.get('odds') or []
                    for o in odds_list:
                        # Support COMPACT format (e.g. {'home': 1.2, 'draw': 3.0, 'away': 5.0})
                        if 'home' in o and 'away' in o:
                            b365_h = o.get('home')
                            b365_d = o.get('draw')
                            b365_a = o.get('away')
                            continue

                        n = str(o.get('name') or o.get('label') or '').lower()
                        p = o.get('price') or o.get('odds')
                        
                        # Match against Normalized OR Raw name to catch mismatches like "Man City" vs "Manchester City"
                        # Also standard synonyms
                        h_matches = {home_team.lower(), raw_home.lower(), 'home', '1'}
                        a_matches = {away_team.lower(), raw_away.lower(), 'away', '2'}
                        d_matches = {'draw', 'x', 'the draw'}
                        
                        if n in h_matches: b365_h = p
                        elif n in a_matches: b365_a = p
                        elif n in d_matches: b365_d = p

                # 2. Totals & Alternate Totals (Merged Logic)
                elif m_key == 'totals' or m_key == 'alternate_totals':
                    # Check for "Compact/Asian" Format (hdp, over, under)
                    odds_arr = m.get('odds', [])
                    # Standard V4 Format (outcomes list)
                    outcomes_arr = m.get('outcomes', [])
                    
                    # Logic 1: Compact Format (V3?)
                    if odds_arr:
                        for o in odds_arr:
                            point = o.get('hdp')
                            p_over = o.get('over')
                            p_under = o.get('under')
                            if point is not None:
                                if p_over: totals_dict[f'B365_Over{point}'] = float(p_over)
                                if p_under: totals_dict[f'B365_Under{point}'] = float(p_under)
                                
                    # Logic 2: Standard Format (V4)
                    elif outcomes_arr:
                        for o in outcomes_arr:
                             point = o.get('point')
                             if point is not None:
                                 n = str(o.get('name') or o.get('label') or '').lower()
                                 price = o.get('price') or o.get('odds')
                                 # Save generic keys: B365_OverX.X
                                 if 'over' in n:
                                     totals_dict[f'B365_Over{point}'] = price
                                 elif 'under' in n:
                                     totals_dict[f'B365_Under{point}'] = price

                # 3. BTTS
                elif m_key == 'btts':
                    odds_list = m.get('outcomes', [])
                    for o in odds_list:
                        n = o.get('name', '').lower() # 'Yes' or 'No'
                        if 'yes' in n: b365_btts_yes = o.get('price')
                        elif 'no' in n: b365_btts_no = o.get('price')

                # 4. Corners / Cards / Team Totals (Generic Parsing)
                # If market key contains 'corner', 'card', 'team' try to find useful lines
                else:
                    target_type = None
                    if 'corner' in m_key: target_type = 'Corners'
                    elif 'card' in m_key: target_type = 'Cards'
                    elif 'team' in m_key and 'total' in m_key: # Team Totals
                        # This is trickier as it might split by team name or "Home/Away"
                        # Outcomes often look like: { name: "Over", point: 1.5, description: "Home Team" } or similar?
                        # Or outcomes: { name: "Home Over", ... }
                        # Let's assume standard API structure: Market="home_team_totals"?
                        if 'home' in m_key: target_type = 'HomeTeam_Goals'
                        elif 'away' in m_key: target_type = 'AwayTeam_Goals'
                        else: target_type = 'TeamGoals' # Fallback
                        
                    if target_type:
                        odds_list = m.get('outcomes', [])
                        for o in odds_list:
                            point = o.get('point')
                            if point:
                                n = o.get('name', '').lower()
                                price = o.get('price')
                                
                                # Refine Team Totals if mixed market
                                # Some APIs return name="Over", description="Home"
                                desc = o.get('description', '').lower()
                                
                                prefix = f"B365_{target_type}"
                                if target_type == 'TeamGoals':
                                    if 'home' in desc or 'home' in n: prefix = "B365_HomeTeam_Goals"
                                    elif 'away' in desc or 'away' in n: prefix = "B365_AwayTeam_Goals"
                                
                                if 'over' in n:
                                    totals_dict[f'{prefix}_Over{point}'] = price
                                elif 'under' in n:
                                    totals_dict[f'{prefix}_Under{point}'] = price

            # Convert to float
            def clean(v):
                try: return float(v)
                except: return None
            
            row = {
                'HomeTeam': home_team,
                'AwayTeam': away_team,
                'B365H': clean(b365_h),
                'B365D': clean(b365_d),
                'B365A': clean(b365_a),
                'B365_BTTS_Yes': clean(b365_btts_yes),
                'B365_BTTS_No': clean(b365_btts_no)
            }
            
            # Merge Totals
            for k, v in totals_dict.items():
                row[k] = clean(v)
                
            return row
            
        except Exception as e:
            return None
