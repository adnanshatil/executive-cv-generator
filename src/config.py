import os
from pathlib import Path
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

# Define Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_DIR = BASE_DIR / "source"
OUTPUT_DIR = BASE_DIR / "output"
LINKEDIN_DIR = BASE_DIR / "linkedin"
LOG_DIR = BASE_DIR / "log"

# Ensure output directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LINKEDIN_DIR.mkdir(parents=True, exist_ok=True)

# Environment Variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:12b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://192.168.2.2:11434/api/chat")

# soffice path for LibreOffice CLI (if needed)
SOFFICE_PATH = os.getenv("SOFFICE_PATH", "")

# APIfy token
APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")

# Google Credentials path
GOOGLE_CLIENT_SECRET_PATH = BASE_DIR / os.getenv("GOOGLE_CLIENT_SECRET_FILE", "client_secret_xxx.apps.googleusercontent.com.json")
GOOGLE_TOKEN_PATH = BASE_DIR / "token.json"

# Google API email
GOOGLE_API_EMAIL = os.getenv("GOOGLE_API_EMAIL", "")

# GoogleDrive folder ID for storing generated files
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")

# GoogleSheet ID for storing generated files
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")

# Screening & Confidence Configuration
SCREENING_COOLDOWN_SECONDS = int(os.getenv("SCREENING_COOLDOWN_SECONDS", "300"))
MIN_CONFIDENCE_THRESHOLD = int(os.getenv("MIN_CONFIDENCE_THRESHOLD", "60"))

# Feature Flags
CHECK_MANDATORY_FINNISH = os.getenv("CHECK_MANDATORY_FINNISH", "True").lower() in ("true", "1", "yes")
