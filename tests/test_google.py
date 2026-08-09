from pathlib import Path
import datetime
from src.google_services import (
    get_sheet,
    fetch_all_job_ids,
    get_or_create_test_folder,
    upload_file_to_drive,
    append_scraped_job
)

def run_google_integration_test():
    print("🚀 Starting Google API Integration Test...\n")
    
    # 1. Test Sheet Connection
    print("1️⃣ Testing Google Sheet Access...")
    sheet = get_sheet()
    print(f"   ✅ Connected to Sheet: '{sheet.title}'")
    
    job_ids = fetch_all_job_ids()
    print(f"   ✅ Existing Job IDs found: {job_ids}\n")

    # 2. Test Drive Folder Creation (_test_sandbox)
    print("2️⃣ Testing Google Drive Test Folder Creation...")
    test_folder_id, test_folder_link = get_or_create_test_folder()
    print(f"   ✅ Test Sandbox Folder ID: {test_folder_id}")
    print(f"   🔗 Drive Link: {test_folder_link}\n")

    # 3. Test File Upload to Drive
    print("3️⃣ Testing File Upload to Sandbox...")
    dummy_file = Path("tests/dummy_test.txt")
    dummy_file.write_text("This is a test file for the Google Drive integration.", encoding="utf-8")
    
    file_link = upload_file_to_drive(dummy_file, test_folder_id)
    print(f"   ✅ Uploaded 'dummy_test.txt' successfully!")
    print(f"   🔗 File Link: {file_link}\n")
    
    # Clean up local dummy file
    if dummy_file.exists():
        dummy_file.unlink()

    # 4. Test Appending Mock Row to Sheet
    print("4️⃣ Testing Mock Row Creation in Sheet...")
    mock_id = f"999{int(datetime.datetime.now().timestamp())}"  # Unique test ID
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    append_scraped_job(
        status="Scraped",
        deadline="2026-12-31",
        company="Test Company Inc.",
        role="Enterprise Architect Test",
        linkedin_id=mock_id,
        linkedin_link=f"https://www.linkedin.com/jobs/view/{mock_id}/",
        scraped_info_link=file_link,
        folder_link=test_folder_link,
        scraped_date=now_str
    )
    print(f"   ✅ Appended Mock Row with LinkedIn ID: {mock_id}\n")
    
    print("🎉 ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_google_integration_test()