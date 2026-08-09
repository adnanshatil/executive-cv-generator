import re
import time
import io
import fcntl
import sys
from pathlib import Path
from googleapiclient.http import MediaIoBaseDownload
from src.google_services import (
    get_sheet, 
    get_drive_service, 
    update_job_status,
    extract_id,
    upload_file_to_drive
)
from src.config import OUTPUT_DIR, LOG_DIR
from src.pipeline import run_pipeline

# Configure limits and timings
POLL_INTERVAL_SECONDS = 3600  # Runs once an hour
JOBS_PER_CYCLE = 1            # Process exactly 1 job at a time to prevent Mac Mini overheating

def download_text_from_drive(file_link: str) -> str:
    """Downloads the raw job description text from Google Drive."""
    service = get_drive_service()
    file_id = extract_id(file_link)
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    return fh.getvalue().decode("utf-8")

def run_controller():
    # 1. The Deadbolt Lock: Ensure only one instance runs at a time
    lock_file_path = Path(__file__).parent / "controller.lock"
    lock_file = open(lock_file_path, "w")
    try:
        # Try to lock the file. If another script already has it locked, this throws an error.
        fcntl.lockf(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (BlockingIOError, IOError):
        # Create a timestamped log for the skip
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{now_str}] ⏳ Previous generation is still running. Exiting safely.\n"
        
        from src.config import LOG_DIR
        with open(LOG_DIR / "controller_empty_runs.log", "a", encoding="utf-8") as f:
            f.write(log_msg)
            
        print(log_msg.strip())
        sys.exit(0) # Exit cleanly

    # 2. If we got the lock, proceed as normal!
    print("🤖 ATS Controller Online. Watching Google Sheet for 'Generate CV'...")
    
    while True:
        try:
            sheet = get_sheet()
            records = sheet.get_all_records()
            
            # Find jobs waiting for generation
            pending_jobs = []
            for idx, row in enumerate(records, start=2): # Row 2 is first data row
                if row.get("Status") == "Generate CV":
                    row["_row_number"] = idx
                    pending_jobs.append(row)
            
            if not pending_jobs:
                # Create a timestamped message using the 'time' module
                now_str = time.strftime("%Y-%m-%d %H:%M:%S")
                log_msg = f"[{now_str}] 💤 No jobs pending. Exiting until next scheduled run.\n"
                
                # Print to console (for manual testing)
                print(log_msg.strip())
                
                # Write directly to your log file
                log_file = LOG_DIR / "controller_empty_runs.log"
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(log_msg)
                return

            # Take only the first job in the queue
            job = pending_jobs[0]
            row_num = job["_row_number"]
            linkedin_id = str(job["LinkedIn ID"])
            company = job["Company"]
            role = job["Role"]
            info_link = job["Scraped Info Link"]
            folder_link = job["Folder Link"]
            folder_id = extract_id(folder_link)
            
            print(f"\n⚙️ Triggering generation for: {company} - {role} ({linkedin_id})")
            
            # 1. Lock the row
            update_job_status(row_num, "Generating")
            
            # 2. Download the raw description from Drive
            print("   📥 Downloading job description from Drive...")
            requirements_text = download_text_from_drive(info_link)
            
            # 3. Trigger Ollama Pipeline
            print("   🧠 Running local Ollama pipeline (This may take up to an hour)...")
            metrics = run_pipeline(
                input_param=job["LinkedIn Link"], # Passed for logging purposes
                pre_company=company,
                pre_role=role,
                pre_requirements=requirements_text
            )
            print(f"   ✅ Generation complete in {metrics.get('total_time_min', 'unknown')} minutes!")
            
            # 4. Identify generated files
            # Pull the final names Ollama actually used for the files
            final_company = metrics.get("company", company)
            final_role = metrics.get("role", role)
            
            clean_comp_fn = re.sub(r'[^a-zA-Z0-9]', '_', final_company).strip('_').lower()
            clean_role_fn = re.sub(r'[^a-zA-Z0-9]', '_', final_role).strip('_').lower()
            clean_comp_fn = re.sub(r'_+', '_', clean_comp_fn)
            clean_role_fn = re.sub(r'_+', '_', clean_role_fn)
            
            print(f"   🔍 Hunting for local files with prefix: cv_{clean_comp_fn}_{clean_role_fn}")
            
            files_to_upload = {
                "cv_docx": OUTPUT_DIR / f"cv_{clean_comp_fn}_{clean_role_fn}.docx",
                "cv_pdf": OUTPUT_DIR / f"cv_{clean_comp_fn}_{clean_role_fn}.pdf",
                "cover_md": OUTPUT_DIR / f"cover_letter_{clean_comp_fn}_{clean_role_fn}.md",
                "cover_pdf": OUTPUT_DIR / f"cover_letter_{clean_comp_fn}_{clean_role_fn}.pdf"
            }
            
            # 5. Upload files to Drive
            print(f"   🔍 Hunting for local files with prefix: cv_{clean_comp_fn}_{clean_role_fn}")
            print("   📤 Uploading files to Google Drive...")
            uploaded_links = {}
            for key, file_path in files_to_upload.items():
                if file_path.exists():
                    uploaded_links[key] = upload_file_to_drive(file_path, folder_id)
                else:
                    print(f"   ⚠️ Warning: Expected output file not found: {file_path.name}")
            
            # 6. Update Google Sheet with final links
            print("   📝 Updating Google Sheet links...")

            # Prioritize the PDF links for the sheet, but fallback to Word/MD if PDF failed
            final_cv_link = uploaded_links.get("cv_pdf", uploaded_links.get("cv_docx", ""))
            final_cover_link = uploaded_links.get("cover_pdf", uploaded_links.get("cover_md", ""))
            
            sheet.update_cell(row_num, 8, final_cv_link)      # Col H: CV 
            sheet.update_cell(row_num, 9, final_cover_link)   # Col I: Cover Letter
            
            update_job_status(row_num, "Generated")
            
            print(f"🎉 Job {linkedin_id} fully processed! Taking a quick 1-minute breath...")
            time.sleep(60) # Give the Mac Mini a brief pause before looping again
            
        except Exception as e:
            print(f"❌ Error encountered: {e}")
            print("Retrying in 5 minutes...")
            time.sleep(300)

if __name__ == "__main__":
    run_controller()