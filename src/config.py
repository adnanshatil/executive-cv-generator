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
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e4b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")

# In src/config.py
CSS_FILE = SOURCE_DIR / "styles.css"