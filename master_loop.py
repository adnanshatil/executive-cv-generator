import time
import datetime
import subprocess
import sys

def run_master_loop():
    print("🚀 ATS Master Loop Started. Leave this terminal open!")
    print("   - Scraper: Scheduled for 3:00 AM daily")
    print("   - Controller: Scheduled every 30 minutes")
    print("   - File Locks: Active (Safe from overlaps)")
    
    last_scraper_run = None
    # Set to 0 so the controller runs immediately on startup
    last_controller_run = 0 
    
    while True:
        now = datetime.datetime.now()
        current_time = time.time()
        
        # --- 1. Scraper Schedule (3:00 AM) ---
        if now.hour == 3:
            # Check if we haven't run it yet today
            if last_scraper_run is None or last_scraper_run.date() < now.date():
                print(f"\n[{now.strftime('%H:%M:%S')}] ⏰ 3:00 AM reached. Triggering Scraper...")
                
                # subprocess.run triggers the script exactly as if you typed it in the terminal
                subprocess.run([sys.executable, "-m", "src.scraper_sync"])
                last_scraper_run = now
        
        # --- 2. Controller Schedule (Every 30 Mins) ---
        # 1800 seconds = 30 minutes
        if current_time - last_controller_run >= 1800:
            print(f"\n[{now.strftime('%H:%M:%S')}] ⚙️ 30-minute interval reached. Triggering Controller...")
            
            subprocess.run([sys.executable, "main_controller.py"])
            last_controller_run = time.time()
            
        # Sleep for 5 minute before checking the clocks again to save CPU
        time.sleep(300)

if __name__ == "__main__":
    try:
        run_master_loop()
    except KeyboardInterrupt:
        print("\n🛑 Master Loop stopped by user.")