import sys
import os
import pandas as pd
from datetime import datetime, timedelta

sys.path.append(os.getcwd())

from src.engine.settlement import BetSettler

# Mock Classes to Simulate Environment
class MockPM:
    def __init__(self):
        self.bets = [
            # 1. Winning Bet (Over 2.5) - Result 2-1
            {'id': '1', 'home_team': 'A', 'away_team': 'B', 'selection': 'Over 2.5 Goals', 'status': 'Pending', 'match_date': '2025-01-01'},
            # 2. Losing Bet (Home Win) - Result 0-1
            {'id': '2', 'home_team': 'C', 'away_team': 'D', 'selection': 'Home Win', 'status': 'Pending', 'match_date': '2025-01-01'},
            # 3. Winning Bet (BTTS Yes) - Result 1-1
            {'id': '3', 'home_team': 'E', 'away_team': 'F', 'selection': 'BTTS Yes', 'status': 'Pending', 'match_date': '2025-01-01'},
            # 4. Losing Bet (Under 1.5) - Result 2-0
            {'id': '4', 'home_team': 'G', 'away_team': 'H', 'selection': 'Under 1.5', 'status': 'Pending', 'match_date': '2025-01-01'},
        ]
        
    def get_user_bets(self, username):
        return self.bets
        
    def update_bet_status(self, username, bet_id, status):
        print(f"🔄 Updating Bet {bet_id} -> {status}")
        for b in self.bets:
            if b['id'] == bet_id:
                b['status'] = status

class MockUM:
    def __init__(self):
        self.portfolio_manager = MockPM()

def verify_settlement():
    print("🔎 Verifying Bet Settlement Logic...")
    
    um = MockUM()
    
    # Mock Historical Data (Results)
    history_data = pd.DataFrame([
        {'Date': '2025-01-02', 'HomeTeam': 'A', 'AwayTeam': 'B', 'FTHG': 2, 'FTAG': 1}, # Total 3 (Over 2.5 WON)
        {'Date': '2025-01-02', 'HomeTeam': 'C', 'AwayTeam': 'D', 'FTHG': 0, 'FTAG': 1}, # Away Win (Home Win LOST)
        {'Date': '2025-01-02', 'HomeTeam': 'E', 'AwayTeam': 'F', 'FTHG': 1, 'FTAG': 1}, # BTTS Yes (WON)
        {'Date': '2025-01-02', 'HomeTeam': 'G', 'AwayTeam': 'H', 'FTHG': 2, 'FTAG': 0}, # Total 2 (Under 1.5 LOST)
    ])
    
    settled = BetSettler.settle_user_bets(um, "test_user", history_data)
    
    print(f"✅ Settled Count: {settled}")
    
    # Verify States
    bets = um.portfolio_manager.bets
    
    assert bets[0]['status'] == 'Won', "Bet 1 should be Won"
    assert bets[1]['status'] == 'Lost', "Bet 2 should be Lost"
    assert bets[2]['status'] == 'Won', "Bet 3 should be Won"
    assert bets[3]['status'] == 'Lost', "Bet 4 should be Lost"
    
    print("🎉 All Test Cases Passed!")

if __name__ == "__main__":
    verify_settlement()
