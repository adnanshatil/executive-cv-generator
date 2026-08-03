import json
from datetime import datetime
from .config import LOG_DIR

HISTORY_FILE = LOG_DIR / "history.json"

def is_url_already_processed(linkedin_url: str) -> tuple[bool, dict | None]:
    """
    Checks if a LinkedIn URL has already been generated.
    Returns (True, entry_dict) if found, else (False, None).
    """
    if not HISTORY_FILE.exists():
        return False, None
        
    try:
        history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        target_url = linkedin_url.strip().lower()
        
        for entry in history:
            if entry.get("linkedin_url", "").strip().lower() == target_url:
                return True, entry
    except Exception:
        pass
        
    return False, None

def log_generation(company: str, role: str, linkedin_url: str, cv_md: str, cv_pdf: str, cover_md: str, cover_pdf: str, exec_time: str):
    """Appends a completed job generation record to output/history.json."""
    history = []
    
    if HISTORY_FILE.exists():
        try:
            history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            history = []

    entry = {
        "id": len(history) + 1,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "company": company,
        "role": role,
        "linkedin_url": linkedin_url,
        "files": {
            "cv_md": cv_md,
            "cv_pdf": cv_pdf,
            "cover_md": cover_md,
            "cover_pdf": cover_pdf
        },
        "execution_time_min": exec_time
    }

    history.append(entry)
    HISTORY_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")