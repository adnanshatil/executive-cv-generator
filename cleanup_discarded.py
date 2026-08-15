import time
from src.google_services import (
    get_sheet,
    get_drive_service,
    update_job_status
)

def extract_id(url_or_id: str) -> str:
    """Helper to extract clean Google Drive IDs from full clickable URLs."""
    clean_str = str(url_or_id).strip()
    if "folders/" in clean_str:
        return clean_str.split("folders/")[1].split("?")[0]
    if "file/d/" in clean_str:
        return clean_str.split("file/d/")[1].split("/")[0]
    if "id=" in clean_str:
        return clean_str.split("id=")[1].split("&")[0]
    return clean_str

def delete_drive_folder(drive_service, folder_id: str) -> bool:
    """Permanently deletes a folder and its contents from Google Drive."""
    try:
        drive_service.files().delete(fileId=folder_id).execute()
        return True
    except Exception as e:
        print(f"      ⚠️ Failed to delete folder {folder_id}: {e}")
        return False

def run_cleanup():
    print("🧹 Starting Discarded Folder Cleanup...")
    
    sheet = get_sheet()
    drive_service = get_drive_service()
    records = sheet.get_all_records()
    
    discarded_count = 0
    
    for idx, row in enumerate(records, start=2):  # Row 2 is first data row
        status = str(row.get("Status", "")).strip().lower()
        
        # Target rows marked Discarded or Discard
        if status in ["discarded", "discard"]:
            company = row.get("Company", "Unknown")
            role = row.get("Role", "Unknown")
            folder_link = row.get("Folder Link", "")
            linkedin_id = row.get("LinkedIn ID", "")
            
            print(f"\n🗑️ Found Discarded Job: {linkedin_id} - {company} - {role} (Row {idx})")
            
            if folder_link:
                folder_id = extract_id(folder_link)
                print(f"   Deleting Google Drive folder: {linkedin_id} - {folder_id}...")
                deleted = delete_drive_folder(drive_service, folder_id)
                # deleted = True  # Simulate deletion for safety
                if deleted:
                    print("   ✅ Drive folder deleted successfully.")
            else:
                print("   ℹ️ No Folder Link found for this row. Skipping Drive deletion.")
            
            # Clear out the links from the sheet and mark as Purged
            # Clear CV Link (Col 8), Cover Letter Link (Col 9), Scraped Info (Col 7)
            update_job_status(idx, "Deleted")
            discarded_count += 1
            time.sleep(1)  # Avoid Google API rate limits

    print(f"\n✨ Cleanup completed! Purged {discarded_count} discarded job folders.")

if __name__ == "__main__":
    run_cleanup()