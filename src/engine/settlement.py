import pandas as pd
from datetime import datetime

class BetSettler:
    """
    Handles automatic settlement of bets based on historical match results.
    """
    
    @staticmethod
    def settle_user_bets(user_manager, username, historical_data):
        """
        Scans pending bets for the user and checks if they can be settled.
        Returns a summary of settled bets.
        """
        pm = user_manager.portfolio_manager
        bets = pm.get_user_bets(username)
        pending_bets = [b for b in bets if b['status'] == 'Pending']
        
        if not pending_bets or historical_data.empty:
            return 0
            
        settled_count = 0
        
        # Ensure Historical Data has necessary columns and date format
        if 'Date' in historical_data.columns:
            historical_data['Date'] = pd.to_datetime(historical_data['Date'])
            
        now = datetime.now()
        
        for bet in pending_bets:
            try:
                # 1. Match Identification
                # Naive matching: HomeTeam, AwayTeam. 
                # Ideally, we should store a unique match_id in the bet, but for now names are key.
                
                # Filter by teams
                match = historical_data[
                    (historical_data['HomeTeam'] == bet['home_team']) & 
                    (historical_data['AwayTeam'] == bet['away_team'])
                ]
                
                # Check Date (Match must be in the past)
                # bet['match_date'] is string, need to ensure match result is actually FROM that match
                # If multiple matches (rare), take the one closest to bet date.
                
                if match.empty:
                    continue
                    
                # Get the result row (assuming single match found or taking last if repeats)
                res = match.iloc[-1]
                
                # Verify match has finished (FTHG/FTAG present)
                if pd.isna(res.get('FTHG')) or pd.isna(res.get('FTAG')):
                    continue
                    
                # 2. Evaluate Outcome
                selection = bet['selection'].lower()
                fthg = int(res['FTHG'])
                ftag = int(res['FTAG'])
                total_goals = fthg + ftag
                outcome = None # 'Won' or 'Lost'
                
                # Logic: Over/Under
                if 'over' in selection:
                    # Extract line, e.g. "Over 2.5" -> 2.5
                    import re
                    line_match = re.search(r'(\d+\.?\d*)', selection)
                    if line_match:
                        line = float(line_match.group(1))
                        outcome = 'Won' if total_goals > line else 'Lost'
                        
                elif 'under' in selection:
                    import re
                    line_match = re.search(r'(\d+\.?\d*)', selection)
                    if line_match:
                        line = float(line_match.group(1))
                        outcome = 'Won' if total_goals < line else 'Lost'
                        
                # Logic: 1X2 / Moneyline
                elif 'home' in selection and 'win' in selection: # Home Win
                    outcome = 'Won' if fthg > ftag else 'Lost'
                elif 'away' in selection and 'win' in selection: # Away Win
                    outcome = 'Won' if ftag > fthg else 'Lost'
                elif 'draw' in selection or 'empate' in selection:
                    outcome = 'Won' if fthg == ftag else 'Lost'
                    
                # Logic: BTTS
                elif 'btts' in selection or 'both teams' in selection:
                    btts_happened = (fthg > 0 and ftag > 0)
                    if 'yes' in selection:
                        outcome = 'Won' if btts_happened else 'Lost'
                    elif 'no' in selection:
                        outcome = 'Won' if not btts_happened else 'Lost'
                
                # 3. Update Status
                if outcome:
                    pm.update_bet_status(username, bet['id'], outcome)
                    settled_count += 1
                    
            except Exception as e:
                print(f"Error settling bet {bet['id']}: {e}")
                continue
                
        return settled_count
