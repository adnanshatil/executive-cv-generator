# 🤖 Autonomous ATS Resume & Cover Letter Intelligence Engine

An automated, local AI-driven recruitment and application generation pipeline. The system monitors job targets, scrapes postings from LinkedIn via Apify, indexes metadata and descriptions in Google Sheets and Google Drive, executes a multi-agent generation pipeline via local LLM inference (Ollama), and compiles tailored, ATS-optimized CVs and Cover Letters formatted into production-ready PDFs.

Besides you can connect it to your telegram and post LinkedIn link to it for producing CV and Cover Letter for youo.


---

> ### ⚠️ System Hardware Disclaimer
> **Target Platform:** Designed and benchmarked specifically for **Apple Silicon (macOS Sonoma / Sequoia)** with a baseline requirement of an **Apple Mac Mini M4 (16GB Unified Memory minimum)**.
> 
> Local LLM inference utilizes Apple Metal acceleration for models like `gemma4:12b`. Running on systems with less than 16GB unified memory or non-Metal architectures will lead to significant inference latency or memory pressure.

---

## 📑 Table of Contents
1. [Architecture Overview](#-architecture-overview)
2. [Project Structure](#-project-structure)
3. [Prerequisites & System Toolchain Setup](#-prerequisites--system-toolchain-setup)
4. [Ollama & Model Initialization](#-ollama--model-initialization)
5. [Environment Variables & Configuration](#-environment-variables--configuration)
6. [Google Cloud Platform & OAuth Setup](#-google-cloud-platform--oauth-setup)
7. [Apify LinkedIn Scraper Configuration](#-apify-linkedin-scraper-configuration)
8. [Telegram Bot Integration](#-telegram-bot-integration)
9. [Git Setup & Ignore Rules](#-git-setup--ignore-rules)
10. [Command-Line Usage & Execution Modes](#-command-line-usage--execution-modes)
11. [24/7 Automation via macOS launchd](#-247-automation-via-macos-launchd)
12. [Performance Tuning & Troubleshooting](#-performance-tuning--troubleshooting)

---

## 🏛 Architecture Overview

========================================================================================================
                              AUTONOMOUS ATS INTELLIGENCE ENGINE ARCHITECTURE
========================================================================================================

 [ 1. DAILY JOB INGESTION ]                     [ 2. CLOUD DASHBOARD & STORAGE ]
 ┌────────────────────────┐                    ┌──────────────────────────────────────────────┐
 │   LinkedIn Postings    │                    │  📊 Google Sheets Tracking Dashboard        │
 └───────────┬────────────┘                    │  - Status: "Scraped" ➔ "Generate CV"         │
             │ (3:00 AM Cron)                  │  - LinkedIn ID / URLs / PDF Artifact Links   │
             ▼                                 └──────────────────────┬───────────────────────┘
 ┌────────────────────────┐                                           │
 │  🕷️ Apify Actor        │                                           │ Polls "Generate CV"
 │ (cheap_scraper/actor)  │                                           │ every 30 mins
 └───────────┬────────────┘                                           ▼
             │ Scraped JSON Feed               ┌──────────────────────────────────────────────┐
             ▼                                 │  📁 Google Drive Storage System              │
 ┌────────────────────────┐                    │  - Root: /ATS_Resumes/                       │
 │  scraper_sync.py       │───────────────────►│  - Subfolder: /[LinkedIn_ID]/                │
 │  - Deduplication       │  Batch Appends &   │    ├── description.txt                       │
 │  - Link Sanitization   │  Folder Creation   │    ├── Tailored_CV.pdf                       │
 └────────────────────────┘                    │    └── Cover_Letter.pdf                      │
                                               └──────────────────────┬───────────────────────┘
                                                                      │ Fetches Job Spec
                                                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 3. ORCHESTRATION & SCHEDULING (master_loop.py / macOS launchd + caffeinate)                         │
│   ├── 03:00 AM: cleanup_discarded.py ➔ Purges Drive folders for rows marked "Discarded" / "Deleted" │
│   ├── 03:05 AM: scraper_sync.py      ➔ Ingests fresh postings from Apify & batch updates Sheet      │
│   └── Every 30m: main_controller.py  ➔ Executes 5-agent generation pipeline for "Generate CV" jobs  │
└──────────────────────────────────────────────────┬──────────────────────────────────────────────────┘
                                                   │
                                                   ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 4. LOCAL MULTI-AGENT INFERENCE ENGINE (Apple Silicon M4 Metal Accelerated)                            │
│                                                                                                       │
│    Local Ollama Server (localhost:11434) ◄──────► Model: gemma4:12b (num_ctx: 4096 / keep_alive: 1h)  │
│                                                                                                       │
│    Candidate Source Base (source/):                                                                   │
│    [titlesummary.md]   [corecompetencies.md]   [technicalcompetencies.md]   [experiences.md]          │
│                                │                          │                        │                  │
│                                ▼                          ▼                        ▼                  │
│    ┌──────────────────┐  ┌──────────────────┐   ┌──────────────────┐   ┌───────────────────────┐      │
│    │ Agent 1:         │  │ Agent 2:         │   │ Agent 3:         │   │ Agent 4:              │      │
│    │ Target Metadata  │  │ Core Functional  │   │ Tech Skills &    │   │ Impact-Quantified     │      │
│    │ & Exec Summary   │  │ Competencies     │   │ Category Stacks  │   │ Bullet Experience     │      │
│    │                  │  │ **eliminated**   │   │                  │   │                       │      │  
│    └────────┬─────────┘  └────────┬─────────┘   └────────┬─────────┘   └───────────┬───────────┘      │
│             │                     │                      │                         │                  │
│             └─────────────────────┴──────────┬───────────┴─────────────────────────┘                  │
│                                              ▼                                                        │
│                                ┌──────────────────────────┐                                           │
│                                │ Agent 5:                 │                                           │
│                                │ Targeted Cover Letter    │                                           │
│                                └─────────────┬────────────┘                                           │
└──────────────────────────────────────────────┼────────────────────────────────────────────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 5. COMPILATION, EXPORT & ALERT NOTIFICATIONS                                                        │
│                                                                                                     │
│   ┌───────────────────────────┐         ┌───────────────────────────┐       ┌───────────────────┐   │
│   │ 📑 WeasyPrint & Jinja2    │────────►│ 📄 Tailored_CV.pdf        │──────► │ 📁 Upload to Drive│   │
│   │ CSS Print Stylesheet      │         │ 📄 Cover_Letter.pdf       │       │ 📊 Mark Generated │    │
│   └───────────────────────────┘         └─────────────┬─────────────┘       └───────────────────┘   │
│                                                       │                                             │
│                                                       ▼                                             │
│                                         ┌───────────────────────────┐                               │
│                                         │ 📱 Telegram Bot Delivery   │                               │
│                                         │ - /generate <linkedin_id> │                               │
│                                         │ - Instant PDF Dispatch    │                               │
│                                         └───────────────────────────┘                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘


---

## 📂 Project Structure

```text
├── client_secret_xxx.json      # Google OAuth 2.0 Client credentials
├── token.json                  # Auto-generated authorized OAuth token cache
├── requirements.txt            # Python dependencies
├── main_cli.py                 # Interactive terminal runner for ad-hoc generation
├── main_controller.py          # Google Sheets polling processor for "Generate CV"
├── main_bot.py                 # Telegram Bot polling worker
├── master_loop.py              # 24/7 background scheduler[cite: 4, 5]
│
├── source/                     # Master Candidate Context Sources
│   ├── titlesummary.mdux               # Baseline Title Line and Executive Summary
│   ├── corecompetencies.mdux           # Master Core Functional Skills List
│   ├── technicalcompetencies.mdux      # Master Tools, Languages, and Tech Stack
│   ├── professionalexperiences.mdux    # Full Career History and Bullet Bank
│   ├── coverletter.mdux                # Baseline Cover Letter Structure
│   ├── staticcontent.mdux              # Education, Certifications, and Contact Info
│   ├── style.css                       # PDF Styling Sheet for WeasyPrint
│   └── AdnanShatilCV.docx              # Baseline Template Document
│
├── src/                        # Core Engine Modules
│   ├── __init__.py             # Module initialization
│   ├── config.py               # Environment configuration and path loader
│   ├── db.py                   # Local state tracking / caching
│   ├── utils.py                # Text normalization and token utilities
│   ├── agents.py               # Multi-agent prompt orchestrator for Ollama[cite: 1, 5]
│   ├── pipeline.py             # Resume & Cover Letter synthesis pipelines
│   ├── docx_utils.py           # Document transformations & PDF export tools
│   ├── google_services.py      # Google Sheets & Google Drive API connectors
│   ├── scraper_sync.py         # Apify LinkedIn sync & Drive ingestion worker
│   ├── cleanup_discarded.py    # Auto-purger for rejected/discarded job artifacts[cite: 3, 5]
│   └── scraper.py              # Raw HTML/URL scraper fallback utilities
│
├── output/                     # Local artifact destination (PDF/DOCX/MD)
├── log/                        # System runtime logs and execution histories
└── tests/                      # Automated suite for Google APIs and Agents
```

---

## 🛠 Prerequisites & System Toolchain Setup

### 1. Install Xcode Command Line Tools & Homebrew
Open Terminal on your Mac Mini M4:

Bash
```text
# Install Apple Developer Command Line Tools
xcode-select --install

# Install Homebrew package manager
/bin/bash -c "$(curl -fsSL [https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh](https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh))"

# Add Homebrew to your PATH
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### 2. Install System Dependencies & PDF Engines
Bash
```text
brew update
brew install python@3.11 git curl pango cairo libffi glib
```

### 3. Clone Repository & Setup Virtual Environment
Bash
```text
git clone <your-repository-url> ats-engine
cd ats-engine

# Initialize Python 3.11 venv
python3.11 -m venv .venv
source .venv/bin/activate

# Upgrade packaging tools
pip install --upgrade pip setuptools wheel

# Install required Python packages
pip install -r requirements.txt
```

## 🧠 Ollama & Model Initialization
The generation engine uses local inference to keep all candidate data private and avoid external per-token costs.

### 1. Install & Launch Ollama
Bash
```text
# Install Ollama via Homebrew
brew install --cask ollama

# Start the Ollama local background daemon
ollama serve &
```

### 2. Pull Target Model
Pull the verified model weight:

Bash
```text
ollama pull gemma4:12b
```

### 3. Verify Local Model Installation
Run:

Bash
```text
ollama list
```

Confirm that gemma4:12b appears in the list.

### 4. Enable Metal Acceleration & Persistent Memory
Add these environment variables to ~/.zshrc to optimize inference on Apple Silicon:

Bash
```text
# Force model persistence in Unified RAM
export OLLAMA_KEEP_ALIVE=-1

# Enable Metal attention optimizations
export OLLAMA_FLASH_ATTENTION=1

# Allow multiple concurrent context evaluations
export OLLAMA_NUM_PARALLEL=2
```

Apply the changes:

Bash
```text
source ~/.zshrc
```

## ⚙️ Environment Variables & Configuration
Create a .env file in the project root:

Bash
```text
touch .env
```

Populate .env with the following variables:

Code snippet
```text
# ==============================================================================
# LLM ENGINE CONFIGURATION
# ==============================================================================
OLLAMA_MODEL=gemma4:12b
OLLAMA_URL=http://localhost:11434/api/chat

# ==============================================================================
# GOOGLE CLOUD INTEGRATION
# ==============================================================================
# Google Sheet ID from URL: [https://docs.google.com/spreadsheets/d/](https://docs.google.com/spreadsheets/d/)<ID>/edit
GOOGLE_SHEET_ID=1a2B3c4D5e6F7g8H9i0JkLmNoPqRsTuVwXyZ

# Root Google Drive Folder ID for "ATS_Resumes"
GOOGLE_DRIVE_FOLDER_ID=1ZyxWvUtSrQpOnMlKjIhGfEdCbA

# Google OAuth file paths (resolved automatically by src/config.py)
GOOGLE_CLIENT_SECRET_PATH=client_secret_xxx.apps.googleusercontent.com.json
GOOGLE_TOKEN_PATH=token.json

# ==============================================================================
# APIFY LINKEDIN SCRAPER CONFIGURATION
# ==============================================================================
APIFY_TOKEN=apify_api_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ==============================================================================
# TELEGRAM BOT INTEGRATION
# ==============================================================================
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=987654321
```

## ☁️ Google Cloud Platform & OAuth Setup
The engine reads job statuses from Google Sheets and organizes job folders, parsed descriptions, and generated PDFs inside Google Drive.

### Step 1: Enable APIs in Google Cloud Console
Navigate to the Google Cloud Console.
- Create a new project named ATS-Resume-Engine.
- Go to APIs & Services > Library.
- Search for and Enable both:
- - Google Sheets API
- - Google Drive API
### Step 2: Configure OAuth Consent Screen
- Go to APIs & Services > OAuth consent screen.
- Select External and click Create.
- Set App Name to ATS Engine and enter your user support email.
- Under Scopes, add:
- - https://www.googleapis.com/auth/spreadsheets
- - https://www.googleapis.com/auth/drive
- Under Test Users, add your personal Google account email.
### Step 3: Download Credentials
- Go to APIs & Services > Credentials.
- Click Create Credentials > OAuth Client ID.
- Choose Desktop App as the Application Type.
- Download the resulting JSON file and save it in your project root as: client_secret_xxx.apps.googleusercontent.com.json[cite: 5].
### Step 4: First-Time Authentication
Run the test script to trigger the one-time browser login flow:

Bash
```text
python -c "from src.google_services import get_sheet; s = get_sheet(); print('Connected to Sheet:', s.title)"
```
A browser window will open. Authorize your Google account. The generated session token is cached as token.json for all future automated runs[cite: 2, 5].

## 🕵️‍♂️ Apify LinkedIn Scraper Configuration
- Create a free account on Apify.
- Navigate to Settings > Integrations > API Tokens.
- Copy your API Token and assign it to APIFY_TOKEN in .env.
- The system uses the cheap_scraper/linkedin-job-scraper Actor to extract job titles, company metadata, direct links, and full text descriptions.
- Search parameters (SEARCH_QUERIES, LOCATIONS, MAX_JOBS) can be configured directly inside src/scraper_sync.py.

## 📱 Telegram Bot Integration
Control the pipeline, trigger manual generations, and receive completed PDFs via Telegram.
1. Create Your Bot
- Open Telegram and search for @BotFather.
- Send /newbot, assign a name and username (e.g., MyATSCVBot).
- Copy the HTTP API token provided by BotFather into TELEGRAM_BOT_TOKEN in .env.
2. Retrieve Your Personal Chat ID
- Search for @userinfobot on Telegram and send /start.
- Copy the numeric Id returned and assign it to TELEGRAM_CHAT_ID in .env.
3. Launch the Bot Worker

Bash
```text
python main_bot.py
```

Supported Bot Commands
- /start – Displays system health, active LLM model, and connected Google Sheet.
- /pending – Lists all jobs in Google Sheets currently set to Generate CV.
- /generate <linkedin_id> – Manually triggers the 5-step agent pipeline for a specific job ID and returns the compiled PDF directly to the chat.
- /status – Displays daily sync stats, generated counts, and memory usage.

## 🛡 Git Setup & Ignore Rules
To prevent leaking OAuth credentials, tokens, or compiled artifacts, ensure .gitignore contains the following rules:

Code snippet
```text
# Python Bytecode & Environments
__pycache__/
*.py[cod]
*$py.class
.venv/
env/
venv/

# Environment Variables & API Secrets
.env
client_secret*.json
token.json

# Local System & OS Files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes

# Runtime Logs & Locks
log/*.log
log/history.json
*.lock

# Output Artifacts & Cache
output/*
!output/.gitkeep
linkedin/
```

## 💻 Command-Line Usage & Execution Modes
1. Interactive Local Mode (main_cli.py)
Run an interactive session in your terminal to test prompt generations against any job description:

Bash
```text
python main_cli.py
```

Prompts you for a company name, target role, and raw job description. Outputs Markdown and compiled PDFs directly to the output/ folder[cite: 5].

2. Manual Scraper Sync (src/scraper_sync.py)
Trigger a standalone scrape and sheet sync on demand:

Bash
```text
python -m src.scraper_sync
```

3. Discarded Jobs Cleanup (src/cleanup_discarded.py)
Scan the Google Sheet for rows marked Discarded or Discard, purge their Google Drive folders, and mark the rows Deleted:

Bash
```text
python -m src.cleanup_discarded
```

4. Cloud Controller Polling (main_controller.py)
Run a single pass of the controller to process any jobs marked Generate CV in Google Sheets:

Bash
```text
python main_controller.py
```

## ⏰ 24/7 Automation via macOS launchd
To run the entire engine continuously in the background on your Mac Mini M4 without keeping a terminal window open:

1. Create a launchd Service Definition
Create the file ~/Library/LaunchAgents/com.ats.masterloop.plist:

XML
```text
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "[http://www.apple.com/DTDs/PropertyList-1.0.dtd](http://www.apple.com/DTDs/PropertyList-1.0.dtd)">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ats.masterloop</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/caffeinate</string>
        <string>-dimsu</string>
        <string>/Users/YOUR_USERNAME/ats-engine/.venv/bin/python</string>
        <string>/Users/YOUR_USERNAME/ats-engine/master_loop.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/YOUR_USERNAME/ats-engine</string>
    <key>StandardOutPath</key>
    <string>/Users/YOUR_USERNAME/ats-engine/log/master_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/ats-engine/log/master_stderr.log</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

(Replace /Users/YOUR_USERNAME/ats-engine with your actual project path).

2. Load & Activate the Daemon

Bash
```text
# Load and start daemon
launchctl load ~/Library/LaunchAgents/com.ats.masterloop.plist

# Check running status
launchctl list | grep com.ats.masterloop
```

3. To Stop the Service

Bash
```text
launchctl unload ~/Library/LaunchAgents/com.ats.masterloop.plist
```

## 🚀 Performance Tuning & Troubleshooting
Optimization Settings for Apple Silicon (M4 / 16GB)
Inside src/agents.py, token boundaries are balanced to maximize speed while maintaining output quality:

Python
```text
# Optimal inference options for 12B model on M4 Unified RAM
payload = {
    "model": OLLAMA_MODEL,
    "messages": messages,
    "options": {
        "num_ctx": 4096,          # Optimal context window per agent pass
        "num_predict": 600,        # Prevents unnecessary generation loops
        "temperature": 0.20,       # Low temperature for strict factual alignment
        "top_p": 0.95,
        "thinking": False
    },
    "keep_alive": "1h",            # Avoids reloading model weights into VRAM
    "stream": False
}
```

## Common Issues & Solutions

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **`404 Not Found: /api/chat`** | Target model tag does not match local Ollama registry. | Run `ollama list` and verify `OLLAMA_MODEL` in `.env` matches the tag exactly. |
| **`Read timed out. (read timeout=120)`** | Prompt processing exceeded the HTTP read deadline. | In `src/agents.py`, update the requests timeout to `timeout=(30, 600)`. |
| **Only 1 row appears in Google Sheet** | Synchronous per-row API updates overwritten due to latency. | Use `append_scraped_jobs_batch()` in `src/google_services.py` to write rows in a single batch. |
| **Mac Mini sleep interrupts execution** | macOS deep sleep suspended background network sockets. | Run using `caffeinate -dimsu` or disable system sleep in **System Settings > Displays > Advanced**. |
| **Google Sheet appends to Row 1001** | Default Google Sheet was created with 1,000 empty rows. | Select and delete empty rows 2–1000 in your browser, then run the sync again. |


## 📄 License
This project is proprietary and intended for personal career automation.
