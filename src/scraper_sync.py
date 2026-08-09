import os
import re
import json
import datetime
from pathlib import Path
from apify_client import ApifyClient
from .config import APIFY_TOKEN
from .google_services import (
    fetch_all_job_ids,
    create_job_folder_in_drive,
    upload_file_to_drive,
    append_scraped_job
)

# Initialize the Apify Client
client = ApifyClient(APIFY_TOKEN)

# Search Configuration
SEARCH_QUERIES = ["Enterprise Architect"]
LOCATIONS = ["Finland"]
MAX_JOBS = 150  # Apify actor minimum

def calculate_deadline(job_data: dict) -> str:
    """Extracts deadline if available, otherwise defaults to +7 days."""
    return (datetime.datetime.now() + datetime.timedelta(days=7)).strftime("%Y-%m-%d")

def run_sync():
    print("🚀 Starting LinkedIn Scraper Sync via Apify...")

    # 1. Fetch existing Job IDs from Google Sheets to prevent duplicates
    print("📊 Fetching existing jobs from Google Sheets...")
    existing_ids = fetch_all_job_ids()
    print(f"   Found {len(existing_ids)} existing jobs.")

    # 2. Configure Apify Actor
    run_input = {
        "keyword": SEARCH_QUERIES,         
        "locations": LOCATIONS,            
        # "publishedAt": "r604800",      # Last 7 days
        "publishedAt": "r86400",      # Last 24 hours
        "maxItems": MAX_JOBS,              
        "saveOnlyUniqueItems": True        
    }

    print(f"🕵️‍♂️ Calling Apify to scrape jobs for {SEARCH_QUERIES} in {LOCATIONS}...")
    run = client.actor("cheap_scraper/linkedin-job-scraper").call(run_input=run_input)
    
    # Fetch results from the Apify Dataset
    jobs_found = list(client.dataset(run.default_dataset_id).iterate_items())
    print(f"✅ Apify returned {len(jobs_found)} jobs. Processing...")

    new_jobs_added = 0

    # 3. Process each job
    for job in jobs_found:
        raw_url = job.get("url", "")
        
        # A. Robust Job ID Extraction
        match = re.search(r'([0-9]{9,11})', raw_url)
        if match:
            linkedin_id = str(match.group(1))
        else:
            backup_id = job.get("id") or job.get("jobId")
            if backup_id:
                linkedin_id = str(backup_id)
            else:
                # If we absolutely cannot find an ID, we cannot track it
                continue
                
        # B. Generate the Clean LinkedIn Link!
        linkedin_link = f"https://www.linkedin.com/jobs/view/{linkedin_id}/"

        # C. Extract Data with broad fallbacks
        company = (
            job.get("companyName") or 
            job.get("company") or 
            job.get("employer") or 
            "Unknown Company"
        )
        
        role = (
            job.get("title") or 
            job.get("jobTitle") or 
            job.get("position") or 
            job.get("positionName") or 
            "Unknown Role"
        )
        
        description = (
            job.get("description") or 
            job.get("jobDescription") or 
            job.get("text") or 
            job.get("about")
        )
        
        # D. FALLBACK DEBUGGER: If description is STILL missing, dump the raw JSON!
        if not description:
            description = (
                "⚠️ AUTO-DEBUG MODE: The scraper did not return a standard 'description' field.\n"
                "Here is the raw data Apify returned so you can see the correct field names:\n\n" + 
                json.dumps(job, indent=2, default=str)
            )
        
        # Deduplication check
        if linkedin_id in existing_ids:
            continue

        print(f"   ✨ New Job Found! {company} - {role} ({linkedin_id})")

        # 4. Create Google Drive Folder and Text File
        folder_id, folder_link = create_job_folder_in_drive(linkedin_id)
        
        temp_file = Path(f"{linkedin_id}.txt")
        temp_file.write_text(description, encoding="utf-8")
        
        scraped_info_link = upload_file_to_drive(temp_file, folder_id)
        temp_file.unlink()

        # 5. Append to Google Sheet
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        deadline_str = calculate_deadline(job)

        append_scraped_job(
            status="Scraped",
            deadline=deadline_str,
            company=company,
            role=role,
            linkedin_id=linkedin_id,
            linkedin_link=linkedin_link,
            scraped_info_link=scraped_info_link,
            folder_link=folder_link,
            scraped_date=now_str
        )
        
        existing_ids.add(linkedin_id)
        new_jobs_added += 1

    print(f"🎉 Sync Complete! Added {new_jobs_added} new jobs to your Google Sheet.")

if __name__ == "__main__":
    run_sync()