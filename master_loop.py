import time
import datetime
import subprocess
import sys

def run_master_loop():
    print("🚀 ATS Master Loop Started. Leave this terminal open!")
    print("   - Daily 2:00 AM: Cleanup -> Archive Deleted -> Scraper Sync -> Screening -> CV Generation")
    print("   - Controller: Scheduled every 30 minutes")
    print("   - File Locks: Active (Safe from overlaps)")
    
    last_daily_run = None
    # Set to 0 so the controller checks for pending jobs immediately on startup
    last_controller_run = 0 
    
    while True:
        now = datetime.datetime.now()
        current_time = time.time()
        
        # --- 1. Daily Schedule (2:00 AM): Cleanup -> Archive Deleted -> Scrape -> Screen -> Generate ---
        if now.hour == 2:
            # Check if we haven't run the daily routine today
            if last_daily_run is None or last_daily_run.date() < now.date():
                print(f"\n[{now.strftime('%H:%M:%S')}] ⏰ 2:00 AM reached. Starting daily maintenance...")
                
                # Step 1: Run Cleanup Script (purges yesterday's discarded job folders & marks 'Deleted')
                print(f"[{now.strftime('%H:%M:%S')}] 🧹 Step 1/5: Running Discarded Folders Cleanup...")
                subprocess.run([sys.executable, "-m", "src.cleanup_discarded"])

                # Step 2: Move all Deleted status rows from Sheet1 to Sheet2
                print(f"[{now.strftime('%H:%M:%S')}] 📦 Step 2/5: Archiving Deleted Rows to Sheet2...")
                subprocess.run([sys.executable, "-m", "src.archive_deleted"])
                
                # Step 3: Run Apify Scraper Sync (fetches new postings)
                print(f"[{now.strftime('%H:%M:%S')}] 🕵️‍♂️ Step 3/5: Running LinkedIn Scraper Sync...")
                subprocess.run([sys.executable, "-m", "src.scraper_sync"])
                
                # Step 4: Run Confidence Screening (calculates relevance, sets 'Generate CV' or 'Discarded')
                print(f"[{now.strftime('%H:%M:%S')}] 🧠 Step 4/5: Running Role Confidence Screening...")
                subprocess.run([sys.executable, "-m", "src.screening"])

                # Step 5: Trigger Controller to generate CVs for approved jobs
                print(f"[{now.strftime('%H:%M:%S')}] ⚙️ Step 5/5: Launching CV Generation Controller...")
                subprocess.run([sys.executable, "main_controller.py"])
                
                last_daily_run = now
                last_controller_run = time.time()
                print(f"[{now.strftime('%H:%M:%S')}] ✨ Daily 2:00 AM maintenance cycle finished.")
        
        # --- 2. Controller & Screening Schedule (Every 30 Mins) ---
        # 1800 seconds = 30 minutes
        if current_time - last_controller_run >= 1800:
            print(f"\n[{now.strftime('%H:%M:%S')}] ⚙️ 30-minute interval reached. Running periodic tasks...")
            
            # Check for any rows set to 'Cal. Confidence' or newly scraped jobs
            subprocess.run([sys.executable, "-m", "src.screening"])
            
            # Check for any rows set to 'Generate CV'
            subprocess.run([sys.executable, "main_controller.py"])
            last_controller_run = time.time()
            
        # Sleep for 5 minutes before checking the clock again to save CPU
        time.sleep(300)

if __name__ == "__main__":
    try:
        run_master_loop()
    except KeyboardInterrupt:
        print("\n🛑 Master Loop stopped by user.")
