import time
import subprocess
import sys
import os
from datetime import datetime, timedelta

# Configuration
WAIT_MINUTES = 55
LOG_FILE = "verification_result.log"
SCRIPT_TO_RUN = "debug_predictions.py"

def main():
    start_time = datetime.now()
    target_time = start_time + timedelta(minutes=WAIT_MINUTES)
    
    print(f"[{start_time.strftime('%H:%M:%S')}] Automated Verification Scheduled.")
    print(f"Target Execution Time: {target_time.strftime('%H:%M:%S')}")
    print(f"waiting {WAIT_MINUTES} minutes for API rate limit reset...")
    print(f"Please keep this terminal/window open.")

    # Sleep
    try:
        time.sleep(WAIT_MINUTES * 60)
    except KeyboardInterrupt:
        print("\nCancelled by user.")
        return

    # Execute
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Waking up! Running {SCRIPT_TO_RUN}...")
    
    # Run the prediction script and capture output
    with open(LOG_FILE, "w", encoding='utf-8') as f:
        f.write(f"--- Verification Run: {datetime.now()} ---\n\n")
        f.flush()
        
        # Run subprocess
        result = subprocess.run(
            [sys.executable, SCRIPT_TO_RUN],
            cwd=os.getcwd(),
            stdout=f,
            stderr=subprocess.STDOUT
        )
        
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Execution Complete.")
    print(f"Logs saved to: {os.path.abspath(LOG_FILE)}")
    
    if result.returncode == 0:
        print("SUCCESS: Script finished successfully.")
    else:
        print(f"FAILURE: Script exited with code {result.returncode}.")

if __name__ == "__main__":
    main()
