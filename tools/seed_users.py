
import sys
import os
sys.path.append(os.getcwd())

from src.auth.user_manager import UserManager

def seed():
    print("Forcing User Seed...")
    # Initialize (will trigger the auto-seed logic I just added)
    mgr = UserManager()
    
    # Double check
    if mgr.authenticate("test", "pass"):
        print("✅ SUCCESS: User 'test' exists and validates.")
    else:
        print("❌ FAILURE: User 'test' NOT found after init.")
        # Force register
        mgr.register("test", "pass", "Test", "User", "test@example.com")
        print("Forced registration complete.")

if __name__ == "__main__":
    seed()
