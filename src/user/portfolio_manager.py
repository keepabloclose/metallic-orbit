
import json
import os
import pandas as pd
from datetime import datetime
import uuid

class PortfolioManager:
    """
    Manages user portfolios, bets, and bankroll.
    Data is stored in data/portfolios/{username}.json
    """
    
    def __init__(self, data_dir="data/portfolios"):
        self.data_dir = data_dir
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
    def _get_file_path(self, username):
        return os.path.join(self.data_dir, f"{message_clean_username(username)}.json")
        
    def _load_portfolio(self, username):
        """Loads user portfolio or returns default structure."""
        fp = self._get_file_path(username)
        if os.path.exists(fp):
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self._get_default_portfolio()
        return self._get_default_portfolio()
        
    def _get_default_portfolio(self):
        return {
            "bets": [],
            "balance": 0.0, # Initial Balance? User can set it?
            "currency": "€",
            "created_at": str(datetime.now())
        }
        
    def _save_portfolio(self, username, data):
        fp = self._get_file_path(username)
        with open(fp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            
    def add_bet(self, username, match_data, selection, stake, odds, strategy="Manual", status="Pending", league="Unknown"):
        """
        Adds a new bet to the user's portfolio.
        """
        portfolio = self._load_portfolio(username)
        
        # If league is not explicitly passed, try to get from match_data
        if league == "Unknown":
            league = match_data.get('Div', 'Unknown')
        
        bet_id = str(uuid.uuid4())[:8]
        bet = {
            "id": bet_id,
            "date": str(datetime.now()), # Timestamp of placement
            "match_date": str(match_data.get('Date', '')), # When match happens
            "league": league,
            "home_team": match_data.get('HomeTeam', 'Unknown'),
            "away_team": match_data.get('AwayTeam', 'Unknown'),
            "selection": selection, # e.g. "Over 2.5", "Home Win"
            "odds": float(odds),
            "stake": float(stake),
            "potential_return": float(stake) * float(odds),
            "strategy": strategy,
            "status": status, # Pending, Won, Lost, Void
            "result_amount": 0.0 # Final P/L
        }
        
        portfolio['bets'].append(bet)
        self._save_portfolio(username, portfolio)
        return bet_id
        
    def get_user_bets(self, username):
        """Returns list of bets for a user."""
        portfolio = self._load_portfolio(username)
        return portfolio.get('bets', [])
        
    def update_bet(self, username, bet_id, new_stake):
        """
        Updates the stake of a bet.
        Only allowed if the bet is 'Pending'.
        """
        portfolio = self._load_portfolio(username)
        found = False
        for bet in portfolio['bets']:
            if bet['id'] == bet_id:
                if bet['status'] != 'Pending':
                    return False # Cannot edit settled bets
                
                bet['stake'] = float(new_stake)
                # Recalculate potential return
                bet['potential_return'] = float(new_stake) * float(bet['odds'])
                found = True
                break
        
        if found:
            self._save_portfolio(username, portfolio)
            
        return found
        
    def update_bet_status(self, username, bet_id, new_status, result_amount=None):
        """
        Updates the status of a bet (e.g. from Pending to Won).
        """
        portfolio = self._load_portfolio(username)
        found = False
        for bet in portfolio['bets']:
            if bet['id'] == bet_id:
                bet['status'] = new_status
                if result_amount is not None:
                    bet['result_amount'] = float(result_amount)
                    
                # AUTO CALC RETURN for simple cases if result_amount not passed
                if result_amount is None:
                    if new_status == 'Won':
                         bet['result_amount'] = (bet['stake'] * bet['odds']) - bet['stake'] # PROFIT
                    elif new_status == 'Lost':
                         bet['result_amount'] = -bet['stake']
                    elif new_status == 'Void':
                         bet['result_amount'] = 0.0
                
                found = True
                break
        
        if found:
            self._save_portfolio(username, portfolio)
            
        return found
        
    def delete_bet(self, username, bet_id):
        """Removes a bet."""
        portfolio = self._load_portfolio(username)
        initial_len = len(portfolio['bets'])
        portfolio['bets'] = [b for b in portfolio['bets'] if b['id'] != bet_id]
        
        if len(portfolio['bets']) < initial_len:
            self._save_portfolio(username, portfolio)
            return True
        return False

    def get_portfolio_stats(self, username):
        """
        Calculates Key Performance Indicators (ROI, Hit Rate, etc.)
        """
        bets = self.get_user_bets(username)
        if not bets:
            return {
                "total_bets": 0,
                "settled_bets": 0,
                "pending_bets": 0,
                "win_rate": 0,
                "roi": 0,
                "total_profit": 0,
                "total_staked": 0,
                "total_returned": 0
            }
            
        df = pd.DataFrame(bets)
        
        # Filter for settled bets
        settled = df[df['status'].isin(['Won', 'Lost', 'Void'])]
        
        if settled.empty:
             return {
                "total_bets": len(df),
                "settled_bets": 0,
                "pending_bets": len(df[df['status']=='Pending']),
                "win_rate": 0,
                "roi": 0,
                "total_profit": 0,
                "total_staked": df['stake'].sum() if 'stake' in df.columns else 0,
                "total_returned": 0
            }
            
        # Calculate Stats
        
        # 1. Financial Stats (Real Money Only)
        real_money_bets = settled[settled['stake'] > 0]
        total_staked = real_money_bets['stake'].sum()
        total_profit = 0
        total_returned = 0 # Revenue (Stake + Profit)
        
        for _, row in real_money_bets.iterrows():
            if row['status'] == 'Won':
                revenue = row['stake'] * row['odds']
                total_profit += (revenue - row['stake'])
                total_returned += revenue
            # Lost bets return 0
            elif row['status'] == 'Void':
                total_returned += row['stake']
            elif row['status'] == 'Lost':
                total_profit -= row['stake']
                
        roi = (total_profit / total_staked) * 100 if total_staked > 0 else 0

        # 2. Performance Stats (All Predictions, including tracking)
        # Win Rate includes EVERYTHING to check strategy accuracy
        wins = len(settled[settled['status'] == 'Won'])
        win_rate = (wins / len(settled)) * 100
        
        return {
            "total_bets": len(df),
            "settled_bets": len(settled),
            "pending_bets": len(df) - len(settled),
            "win_rate": round(win_rate, 2),
            "roi": round(roi, 2),
            "total_profit": round(total_profit, 2),
            "total_staked": round(total_staked, 2),
            "total_returned": round(total_returned, 2)
        }

def message_clean_username(username):
    # Simple sanitization
    return username.replace(" ", "_").replace("/", "").replace("\\", "").lower()
