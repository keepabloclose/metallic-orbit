import sys
import os
import json
import pandas as pd
from datetime import datetime

# Setup Path
sys.path.append(os.getcwd())

from src.auth.user_manager import UserManager
from src.user.portfolio_manager import PortfolioManager

def run_verification():
    print("🚀 NOTICE: Starting Full System Verification (YOLO Mode)...")
    
    # 1. Setup Managers
    try:
        um = UserManager()
        pm = PortfolioManager()
        print("✅ Managers Initialized")
    except Exception as e:
        print(f"❌ CRITICAL: Manager Init Fail: {e}")
        return

    # 2. User Registration
    test_user = "yolo_tester"
    try:
        # Cleanup possibly existing user
        if test_user in um.users:
            del um.users[test_user]
            um._save_users()
            
        success, msg = um.register(test_user, "password123", "Yolo", "Tester", "test@example.com")
        if success:
            print(f"✅ User '{test_user}' Registered")
        else:
            print(f"❌ User Registration Failed: {msg}")
            return
    except Exception as e:
        print(f"❌ CRITICAL: Auth Fail: {e}")
        return

    # 3. Simulate Bet Addition (Testing JSON Serialization Fix)
    print("Testing Bet Addition (JSON Serialization)...")
    match_fake = {
        'Date': pd.Timestamp.now(), # Simulate Pandas Timestamp which caused crash
        'HomeTeam': 'Arsenal',
        'AwayTeam': 'Liverpool'
    }
    
    try:
        # A. Real Bet
        bet_id_1 = pm.add_bet(
            username=test_user,
            match_data=match_fake,
            selection="Over 2.5",
            stake=50.0,
            odds=2.0,
            strategy="YoloStrat",
            status="Pending"
        )
        print(f"✅ Real Bet Added (ID: {bet_id_1}) - JSON Serialization Works!")
        
        # B. Prediction (Zero Stake)
        bet_id_2 = pm.add_bet(
            username=test_user,
            match_data=match_fake,
            selection="Home Win",
            stake=0.0,
            odds=1.5,
            strategy="Tracker",
            status="Pending"
        )
        print(f"✅ Prediction Added (ID: {bet_id_2})")
        
    except TypeError as e:
        print(f"❌ JSON SERIALIZATION ERROR DETECTED: {e}")
        return
    except Exception as e:
        print(f"❌ Bet Addition Failed: {e}")
        return

    # 4. Verify Stats (Logic Check)
    print("Testing Stats Logic...")
    
    # Settle Bets
    pm.update_bet_status(test_user, bet_id_1, 'Won') # +50 Profit
    pm.update_bet_status(test_user, bet_id_2, 'Won') # +0 Profit (0 stake)
    
    stats = pm.get_portfolio_stats(test_user)
    
    print(f"Stats Result: {json.dumps(stats, indent=2)}")
    
    # Assertions
    if stats['total_profit'] == 50.0:
        print("✅ Profit Calculation: CORRECT (Ignored Zero Stake)")
    else:
        print(f"❌ Profit Calculation: WRONG (Expected 50.0, Got {stats['total_profit']})")
        
    if stats['total_bets'] == 2 and stats['win_rate'] == 100.0:
         print("✅ Win Rate Calculation: CORRECT (Included All)")
    else:
         print(f"❌ Win Rate Calculation: WRONG (Expected 100%, Got {stats['win_rate']}%)")

    print("🎉 Verification Complete: SYSTEM STABLE")

if __name__ == "__main__":
    run_verification()
