import os
from pathlib import Path
import gspread
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io

# 1. Import the new paths from config
from .config import (
    GOOGLE_CLIENT_SECRET_PATH, 
    GOOGLE_TOKEN_PATH, 
    GOOGLE_SHEET_ID, 
    GOOGLE_DRIVE_FOLDER_ID
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_google_credentials():
    """Authenticates as YOU via a one-time browser login, then uses token.json."""
    creds = None
    
    # Check if we already logged in before
    if GOOGLE_TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(GOOGLE_TOKEN_PATH), SCOPES)
        
    # If no valid token, authenticate via browser
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not GOOGLE_CLIENT_SECRET_PATH.exists():
                raise FileNotFoundError(f"Missing {GOOGLE_CLIENT_SECRET_PATH}! Ensure it is saved in your project folder.")
            
            # Opens Safari on your Mac Mini for a 1-time login
            flow = InstalledAppFlow.from_client_secrets_file(str(GOOGLE_CLIENT_SECRET_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open(GOOGLE_TOKEN_PATH, "w") as token:
            token.write(creds.to_json())
            
    return creds

def get_sheet():
    """Returns the gspread sheet instance."""
    creds = get_google_credentials()
    client = gspread.authorize(creds)
    return client.open_by_key(GOOGLE_SHEET_ID).sheet1

def get_drive_service():
    """Returns the Google Drive API service client."""
    creds = get_google_credentials()
    return build("drive", "v3", credentials=creds)

# ---------------------------------------------------------------------------
# Drive Operations
# ---------------------------------------------------------------------------

def create_job_folder_in_drive(linkedin_id: str) -> tuple[str, str]:
    """
    Creates a folder inside ATS_Resumes named [linkedin_id].
    Returns (folder_id, web_view_link).
    """
    service = get_drive_service()
    
    file_metadata = {
        "name": str(linkedin_id),
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [GOOGLE_DRIVE_FOLDER_ID]
    }
    
    folder = service.files().create(
        body=file_metadata,
        fields="id, webViewLink"
    ).execute()
    
    return folder.get("id"), folder.get("webViewLink")

def upload_file_to_drive(file_path: Path, folder_id: str) -> str:
    """
    Uploads a file to a specific Drive folder.
    Returns the webViewLink of the uploaded file.
    """
    service = get_drive_service()
    
    file_metadata = {
        "name": file_path.name,
        "parents": [folder_id]
    }
    
    media = MediaFileUpload(str(file_path), resumable=True)
    
    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webViewLink"
    ).execute()
    
    return uploaded_file.get("webViewLink")

def download_text_from_drive(file_link_or_id: str) -> str:
    """Downloads raw text content from a Google Drive file link or file ID."""
    service = get_drive_service()
    file_id = extract_id(file_link_or_id)
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    return fh.getvalue().decode("utf-8")

# ---------------------------------------------------------------------------
# Sheet Operations
# ---------------------------------------------------------------------------

def fetch_all_job_ids() -> set[str]:
    """Fetches all existing LinkedIn IDs from the Sheet for deduplication."""
    sheet = get_sheet()
    records = sheet.get_all_records()
    return {str(r.get("LinkedIn ID")).strip() for r in records if r.get("LinkedIn ID")}

def append_scraped_job(
    status: str,
    deadline: str,
    company: str,
    role: str,
    linkedin_id: str,
    linkedin_link: str,
    scraped_info_link: str,
    folder_link: str,
    scraped_date: str,
    confidence: str = ""
):
    """Appends a new scraped job row to the Google Sheet (12-column layout)."""
    sheet = get_sheet()
    row = [
        status,              # A (Col 1)
        deadline,            # B (Col 2)
        company,             # C (Col 3)
        role,                # D (Col 4)
        confidence,          # E (Col 5) - Confidence score
        str(linkedin_id),    # F (Col 6)
        linkedin_link,       # G (Col 7)
        scraped_info_link,   # H (Col 8)
        "",                  # I (Col 9) - CV PDF Link
        "",                  # J (Col 10) - Cover Letter Link
        folder_link,         # K (Col 11)
        scraped_date         # L (Col 12)
    ]
    sheet.append_row(row)

def get_jobs_pending_generation() -> list[dict]:
    """Returns rows where Status == 'Generate CV'."""
    sheet = get_sheet()
    records = sheet.get_all_records()
    
    pending = []
    for idx, row in enumerate(records, start=2):  # Row 1 is header
        if row.get("Status") == "Generate CV":
            row["_row_number"] = idx
            pending.append(row)
            
    return pending

def get_jobs_pending_screening() -> list[dict]:
    """Returns rows where Status == 'Scraped'."""
    sheet = get_sheet()
    records = sheet.get_all_records()
    
    pending = []
    for idx, row in enumerate(records, start=2):  # Row 1 is header
        if row.get("Status") == "Scraped":
            row["_row_number"] = idx
            pending.append(row)
            
    return pending

def update_job_confidence_and_status(row_number: int, confidence: str, status: str):
    """Updates Confidence (Col 5 / E) and Status (Col 1 / A)."""
    sheet = get_sheet()
    sheet.update_cell(row_number, 5, confidence)
    sheet.update_cell(row_number, 1, status)

def update_job_generation_success(
    row_number: int,
    cv_pdf_link: str,
    cover_pdf_link: str
):
    """Updates row status to 'Generated' and attaches output PDF links."""
    sheet = get_sheet()
    sheet.update_cell(row_number, 1, "Generated")        # Column A (Status)
    sheet.update_cell(row_number, 9, cv_pdf_link)       # Column I (CV PDF Link)
    sheet.update_cell(row_number, 10, cover_pdf_link)   # Column J (Cover Letter Link)

def update_job_status(row_number: int, status: str):
    """Updates the status cell of a specific row."""
    sheet = get_sheet()
    sheet.update_cell(row_number, 1, status)

def get_or_create_test_folder() -> tuple[str, str]:
    """
    Finds or creates a '_test_sandbox' subfolder inside GOOGLE_DRIVE_FOLDER_ID.
    Returns (folder_id, web_view_link).
    """
    service = get_drive_service()
    
    # Check if _test_sandbox already exists
    query = f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and name = '_test_sandbox' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q=query, fields="files(id, webViewLink)").execute()
    files = results.get("files", [])
    
    if files:
        return files[0]["id"], files[0]["webViewLink"]
        
    # If not found, create it
    file_metadata = {
        "name": "_test_sandbox",
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [GOOGLE_DRIVE_FOLDER_ID]
    }
    
    folder = service.files().create(
        body=file_metadata,
        fields="id, webViewLink"
    ).execute()
    
    return folder.get("id"), folder.get("webViewLink")

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

def purge_discarded_job_row(row_number: int):
    """
    Updates status to 'Deleted' and clears Scraped Info (H), CV Link (I),
    Cover Letter Link (J), and Folder Link (K).
    """
    sheet = get_sheet()
    sheet.update_cell(row_number, 1, "Deleted")  # Column A (Status)
    
    # Batch clear columns H to K (Columns 8, 9, 10, 11)
    sheet.update(f"H{row_number}:K{row_number}", [["", "", "", ""]])