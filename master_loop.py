import time
import datetime
import subprocess
import sys

def run_master_loop():
    print("🚀 ATS Master Loop Started. Leave this terminal open!")
    print("   - Daily 3:00 AM: Cleanup Discarded Folders -> Scraper Sync")
    print("   - Controller: Scheduled every 30 minutes")
    print("   - File Locks: Active (Safe from overlaps)")
    
    last_daily_run = None
    # Set to 0 so the controller checks for pending jobs immediately on startup
    last_controller_run = 0 
    
    while True:
        now = datetime.datetime.now()
        current_time = time.time()
        
        # --- 1. Daily Schedule (3:00 AM): Cleanup then Scrape ---
        if now.hour == 11:
            # Check if we haven't run the daily routine today
            if last_daily_run is None or last_daily_run.date() < now.date():
                print(f"\n[{now.strftime('%H:%M:%S')}] ⏰ 3:00 AM reached. Starting daily maintenance...")
                
                # Step A: Run Cleanup Script first
                print(f"[{now.strftime('%H:%M:%S')}] 🧹 Step 1/2: Running Discarded Folders Cleanup...")
                subprocess.run([sys.executable, "-m", "src.cleanup_discarded"])
                
                # Step B: Run Apify Scraper Sync
                print(f"[{now.strftime('%H:%M:%S')}] 🕵️‍♂️ Step 2/2: Running LinkedIn Scraper Sync...")
                subprocess.run([sys.executable, "-m", "src.scraper_sync"])
                
                last_daily_run = now
                print(f"[{now.strftime('%H:%M:%S')}] ✨ Daily 3:00 AM maintenance cycle finished.")
        
        # --- 2. Controller Schedule (Every 30 Mins) ---
        # 1800 seconds = 30 minutes
        if current_time - last_controller_run >= 1800:
            print(f"\n[{now.strftime('%H:%M:%S')}] ⚙️ 30-minute interval reached. Triggering Controller...")
            
            subprocess.run([sys.executable, "main_controller.py"])
            last_controller_run = time.time()
            
        # Sleep for 5 minutes before checking the clock again to save CPU
        time.sleep(300)

if __name__ == "__main__":
    try:
        run_master_loop()
    except KeyboardInterrupt:
        print("\n🛑 Master Loop stopped by user.")