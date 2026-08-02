import json
from datetime import datetime
from .config import LOG_DIR

HISTORY_FILE = LOG_DIR / "history.json"

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