🚀 Executive CV & Cover Letter Generator (Local AI + Telegram + Google Workspace)An automated, local-first Applicant Tracking System (ATS) and document generation pipeline designed for macOS. It processes LinkedIn job postings, extracts key technical and executive requirements, and creates tailored CVs (.docx, .md, .pdf) and Cover Letters (.md, .pdf) using local LLM inference via Ollama, LibreOffice, and optional cloud automation.The system supports three operating modes:CLI Mode: Quick, one-off local document generation from the terminal.  Telegram Bot Mode: Interactive on-demand generation from mobile or desktop.  Auto-Pilot Mode: 24/7 background scraping via Apify, Google Sheets status tracking, automated generation via master_loop.py, and Google Drive storage.  📁 Project Directory StructurePlaintextexecutive-cv-generator/
│
├── .env                        # 🔒 API keys, bot tokens, and Google IDs
├── .gitignore                  # Prevents committing secrets, venv, and tokens
├── requirements.txt            # Python package dependencies
├── README.md                   # System documentation
├── client_secret.json          # 🔑 Google Cloud OAuth credentials (DO NOT COMMIT)
├── token.json                  # 🔑 Generated Google Cloud session token
│
├── main_cli.py                 # 🚀 Mode 1: Terminal Command Line Interface
├── main_bot.py                 # 🚀 Mode 2: Telegram Bot listener
├── main_controller.py          # 🚀 Mode 3: Google Sheet watcher & generation trigger
├── master_loop.py              # 🚀 24/7 Master Scheduler (3 AM Scraper + 30-min Controller)
├── 
│
├── source/                     # 📄 Candidate Master Source Data & Styles
│   ├── titlesummary.md         # Master summary & target title configurations
│   ├── corecompetencies.md     # Core competencies inventory
│   ├── technicalcompetencies.md# Raw technical skills matrix
│   ├── professionalexperiences.md # Career achievements and role metrics
│   ├── coverletter.md          # Cover letter base template
│   ├── staticcontent.md        # Static employment history & education footer[cite: 1, 5]
│   └── styles.css              # Print stylesheet for PDF rendering[cite: 5]
│
├── output/                     # 📁 Local output directory (.docx, .md, .pdf)[cite: 1, 5]
├── log/                        # 📁 Logs, lockfiles, and run history[cite: 4, 5]
│   ├── history.json            # 📊 Generation history database[cite: 1, 5]
│   ├── controller.lock         # 🔒 File lock to prevent process overlaps
│   └── controller_empty_runs.log # 📜 Polling heartbeat log
│
└── src/                        # 🧠 Core Application Package
    ├── __init__.py             # Package initializer[cite: 5]
    ├── config.py               # Paths and environment variable loader[cite: 1, 5]
    ├── utils.py                # File I/O, timers, and PDF compilers[cite: 1, 5]
    ├── docx_utils.py           # DOCX templating and grid formatting
    ├── scraper.py              # Single LinkedIn URL parser[cite: 1, 5]
    ├── scraper_sync.py         # Apify batch scraper & Google Sheet synchronizer
    ├── google_services.py      # Google Sheets & Google Drive API handlers
    ├── agents.py               # Ollama prompt engineering chains[cite: 1, 5]
    ├── db.py                   # History logging manager[cite: 1, 5]
    └── pipeline.py             # Orchestration pipeline[cite: 1, 5]
    └── cleanup_discarded.py    # 🧹 Sheet cleaner & Drive folder deletion script

# 🛠️ Phase 0: Base macOS SetupOpen the macOS Terminal and execute the following steps in order.1. Install Package Manager & System DependenciesBash# 1. Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install Python, Ollama, and LibreOffice (required for background PDF conversion)
brew install python@3.10
brew install --cask ollama
brew install --cask libreoffice
2. Download and Run Local AI ModelStart the Ollama app from your Applications folder, then pull the target model:Bashollama run gemma4:e4b
(Type /bye to exit the Ollama prompt once loaded).3. Setup Python Virtual EnvironmentBash# Clone or navigate to the repository directory
cd /path/to/executive-cv-generator

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip and install all required packages
pip install --upgrade pip
pip install -r requirements.txt
⚙️ Environment Variables (.env)Create a .env file in the root project folder:Code snippet# ==========================================
# 1. LOCAL LLM PARAMETERS
# ==========================================
OLLAMA_MODEL=gemma4:e4b
OLLAMA_URL=http://localhost:11434/api/chat

# ==========================================
# 2. MODE 2: TELEGRAM CONFIGURATION
# ==========================================
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_from_botfather
ALLOWED_USER_ID=your_numeric_telegram_user_id

# ==========================================
# 3. MODE 3: AUTO-PILOT & GOOGLE WORKSPACE
# ==========================================
APIFY_API_TOKEN=your_apify_api_token
GOOGLE_SHEET_ID=your_google_sheet_id_here
GOOGLE_DRIVE_PARENT_FOLDER_ID=your_google_drive_folder_id_here
🖥️ Mode 1: Run via Command Line (CLI)Best for rapid, single-job testing directly on your Mac.How to RunBashsource .venv/bin/activate
python main_cli.py "https://www.linkedin.com/jobs/view/4429205456/"
(You can also pass raw job description text inside quotes instead of a URL).Expected OutputThe script fetches requirements, extracts metadata, and executes prompt chains.  Documents are generated directly into the output/ directory[cite: 1, 5]:output/cv_<company>_<role>.docx[cite: 1]output/cv_<company>_<role>.pdf[cite: 1, 5]output/cover_letter_<company>_<role>.md[cite: 1, 5]output/cover_letter_<company>_<role>.pdf[cite: 1, 5]The transaction is recorded in log/history.json[cite: 1, 5].📱 Mode 2: Run via Telegram BotGenerate documents on the fly by sending LinkedIn URLs to a private Telegram bot.1. Telegram Credentials SetupOpen Telegram and search for @BotFather.Send /newbot, follow prompts for display name and username, and copy the HTTP API Token into TELEGRAM_BOT_TOKEN in your .env.Search for @userinfobot on Telegram and send a message. Copy the numeric Id into ALLOWED_USER_ID in your .env to restrict access to your account.2. How to RunBashsource .venv/bin/activate
python main_bot.py
3. Usage & BehaviorInitial Greeting: Send /start to verify connectivity.  Input Validation: Sending non-LinkedIn links (e.g., [https://google.com](https://google.com)) or plain text is rejected immediately by input guardrails.  Deduplication: If the URL already exists in log/history.json, the bot prevents duplicate generation and returns existing file references.  Generation: Sending a valid link triggers the pipeline, updates message state, and outputs .docx, .md, and .pdf files to output/.  🤖 Mode 3: Auto-Pilot Mode (Google Workspace & Apify)Full automation workflow: crawls LinkedIn daily, syncs jobs to Google Sheets, allows one-tap mobile triggering, stores output files on Google Drive, and provides garbage cleanup.1. Apify API SetupCreate an account at Apify.com.Navigate to Settings > Integrations and copy your Personal API Token.Add the token to APIFY_API_TOKEN in your .env.2. Google Cloud Platform (OAuth Setup)Go to the Google Cloud Console.Create a new project and enable both the Google Sheets API and Google Drive API.Go to APIs & Services > OAuth consent screen:Set User Type to External.Under Test Users, add your personal Google email address.Under Publishing status, click PUBLISH APP (switch to "In Production") to ensure refresh tokens do not expire after 7 days.Go to APIs & Services > Credentials:Click Create Credentials > OAuth client ID.Select Application type: Desktop App.Download the JSON credential file, rename it to client_secret.json, and place it in the project root folder.3. Google Drive & Google Sheet StructureGoogle Drive: Create a main folder named ATS Jobs. Copy the folder ID from the URL ([https://drive.google.com/drive/folders/](https://drive.google.com/drive/folders/)<FOLDER_ID>) into GOOGLE_DRIVE_PARENT_FOLDER_ID in your .env.Google Sheet: Create a spreadsheet and paste the ID from its URL ([https://docs.google.com/spreadsheets/d/](https://docs.google.com/spreadsheets/d/)<SHEET_ID>/edit) into GOOGLE_SHEET_ID in your .env.Set the first row (headers) of your sheet to:Col ACol BCol CCol DCol ECol FCol GCol HCol ICol JStatusDeadlineCompanyRoleLinkedIn IDLinkedIn LinkScraped Info LinkCV LinkCover Letter LinkFolder Link4. Google Sheet Status LifecycleScraped: Added automatically by the Apify scraper script at 3:00 AM with the raw description stored in Google Drive.Generate CV: Set manually (from your phone or browser) to trigger generation.Generating: Set by main_controller.py while the LLM runs.  Generated: Set automatically upon completion. Google Drive links for the generated CV and Cover Letter are inserted into Columns H & I[cite: 4].Discarded / Discard: Set manually on roles you do not want to pursue.5. Running the 24/7 Master Loopmaster_loop.py handles scheduling without memory leaks:Triggers src.scraper_sync daily at 3:00 AM.Polls Google Sheets via main_controller.py every 30 minutes[cite: 4].Enforces fcntl file locking (log/controller.lock) to prevent concurrent process collisions[cite: 4].Run the scheduler:Bashsource .venv/bin/activate
python master_loop.py
(On first execution, a browser will open to complete Google OAuth consent, creating a permanent local token.json).6. Purging Discarded Jobs (cleanup_discarded.py)To delete Google Drive job folders for rejected roles and maintain storage quotas:Bashpython cleanup_discarded.py
The script locates rows marked Discarded or Discard, deletes the linked Google Drive folders, and sets the row status to Deleted.⚙️ Running as a 24/7 Background Daemon (macOS launchd)To keep your bot or master loop running across system restarts without an open terminal window:Bash# 1. Create the launchd service definition file
cat <<EOF > ~/Library/LaunchAgents/com.ats.masterloop.plist
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ats.masterloop</string>

    <key>ProgramArguments</key>
    <array>
        <string>$PWD/.venv/bin/python</string>
        <string>$PWD/master_loop.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$PWD</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>$PWD/log/master_stdout.log</string>

    <key>StandardErrorPath</key>
    <string>$PWD/log/master_stderr.log</string>
</dict>
</plist>
EOF

# 2. Load and start the background service
launchctl load ~/Library/LaunchAgents/com.ats.masterloop.plist
Management Commands:Check Status: launchctl list | grep com.ats.masterloopView Logs: tail -f log/master_stdout.logStop Service: launchctl unload ~/Library/LaunchAgents/com.ats.masterloop.plist









# 🚀 Executive CV & Cover Letter Generator With Ollama + gemma4:12b + Telegram (+ Google Drive & Google Sheet [optional])

An automated, local AI-powered pipeline designed for **macOS**. It ingests LinkedIn job posting URLs, validates input links, extracts key architectural/engineering requirements, and generates tailored, ATS-optimized **Executive CVs** (`.md` & `.pdf`) and **Cover Letters** (`.md` & `.pdf`) using local LLM **(gemma4:e4b)** inference via **Ollama** and **Telegram Bot API**.

> ⚠️ **macOS Disclaimer:**  
> This application is optimized specifically for **macOS (Apple Silicon M-series)**. It relies on local Ollama inference and native macOS `launchd` service management. Ensure your Mac's energy settings prevent full system sleep if running the daemon 24/7.

---

## 📁 Project Directory & Component Overview

```text
executive-cv-generator/
│
├── .env                        # 🔒 Environment secrets (Bot tokens & local LLM endpoints)
├── .gitignore                  # Prevents committing virtualenvs, logs, and generated PDFs
├── requirements.txt            # Python dependencies
├── README.md                   # System documentation & setup guide
│
├── main_cli.py                 # 🚀 Entrypoint 1: Terminal Command Line Interface
├── main_bot.py                 # 🚀 Entrypoint 2: Telegram Bot Listener & Handler
│
├── source/                     # 📄 Candidate Master Source Data & Styles
│   ├── titlesummary.md         # Master summary & title structures
│   ├── corecompetencies.md     # Strategic core competency matrix
│   ├── technicalcompetencies.md# Raw technical skills inventory
│   ├── professionalexperiences.md# Detailed career achievement bullets & metrics
│   ├── coverletter.md          # Cover letter base template
│   ├── staticcontent.md        # Static employment history & education footer
│   └── styles.css              # Custom print CSS for 2-page executive PDF layout
│
├── linkedin/                   # 📁 Storage for raw scraped LinkedIn job descriptions
├── output/                     # 📁 Destination for generated CVs (.md/.pdf) & Cover Letters (.pdf)
├── log/                        # 📁 Logs directory for daemon stdout, stderr & history
│   └── history.json            # 📊 JSON log mapping output files to original LinkedIn URLs
│
└── src/                        # 🧠 Core Application Package
    ├── __init__.py             # Package initializer
    ├── config.py               # Path definitions & environment variable loader
    ├── utils.py                # File I/O, timer utilities, PDF compiler & text sanitizers
    ├── scraper.py              # LinkedIn HTML parser & URL validation guardrails
    ├── agents.py               # Ollama prompt engineering & response parsing
    └── pipeline.py             # Main orchestrator connecting scraper, agents & output generator
    ├── db.py                   # 💾 History log manager (writes to log/history.json)
```

## 🛠️ Step-by-Step Environment Setup
1. Prerequisites Check
Install Ollama for macOS: Download and install from ollama.com.

Pull Required Model:
```text
Bash
ollama pull gemma4:e4b
```
Verify Ollama Status:
```text
Bash
curl http://localhost:11434/api/tags
```
2. Workspace & Virtual Environment Setup
Run the following commands in your Mac terminal to set up the environment:
```text
Bash
# 1. Create Python virtual environment
python3 -m venv .venv

# 2. Activate virtual environment
source .venv/bin/activate

# 3. Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

## 🤖 Telegram Bot Configuration

### 1. How to Set Up a Telegram Bot

To run this pipeline interactively via Telegram, you must create a free bot and retrieve an API access token from Telegram’s official **BotFather**.

#### Step 1: Create a Bot via `@BotFather`
1. Open **Telegram** on your mobile device or desktop.
2. Search for `@BotFather` (verify the official blue checkmark) and start a chat.
3. Send the command:
```text
/newbot
```
4. Name Your Bot: Enter a display name when prompted (e.g., Executive CV Generator).
5. Set Username: Choose a unique username ending in bot (e.g., my_executive_cv_bot).
6. Save Your API Key: BotFather will reply with an API access token formatted like:
```text
7123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
```
7. Now configure it in the next step 

## ⚙️ Configuration Setup
Environment File (.env)
Create a .env file in the root project directory:

Code snippet
```text
# Telegram Bot Key from @BotFather
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Ollama Endpoint Parameters
OLLAMA_MODEL=gemma4:e4b
OLLAMA_URL=http://localhost:11434/api/chat
```

Source Files Setup
Ensure all required Markdown files and stylesheet are present inside the source/ folder:
```text
source/titlesummary.md
source/corecompetencies.md
source/technicalcompetencies.md
source/professionalexperiences.md
source/coverletter.md
source/staticcontent.md
source/styles.css
```

## 🖥️ How to Run & Test
### Mode 1: Run via Terminal CLI (Fast Local Testing)
Execute the pipeline directly from your terminal using a test LinkedIn URL:
```text
Bash
source .venv/bin/activate
python main_cli.py "[https://www.linkedin.com/jobs/view/4429205456/](https://www.linkedin.com/jobs/view/4429205456/)"
```
Outputs will be generated directly in the output/ directory.

### Mode 2: Run Interactively via Telegram Bot
Launch the Telegram bot listener interactively in your terminal session:
```text
Bash
source .venv/bin/activate
python main_bot.py
```
Send a valid LinkedIn job URL to your Telegram bot.

Test sending non-LinkedIn links (e.g. https://google.com) or text messages to confirm the input validation guardrail rejects them immediately.

## ⚙️ Setting Up as a 24/7 Background Daemon on macOS
To run the Telegram Bot continuously as a background daemon that starts on boot and auto-restarts on crashes:

### Step 1: Generate launchd Configuration
Run this command in your project root directory. It automatically resolves your current directory path ($PWD):
```text
Bash
cat <<EOF> ~/Library/LaunchAgents/com.user.cvbot.plist
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "[http://www.apple.com/DTDs/PropertyList-1.0.dtd](http://www.apple.com/DTDs/PropertyList-1.0.dtd)">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.cvbot</string>

    <key>ProgramArguments</key>
    <array>
        <string>$PWD/.venv/bin/python</string>
        <string>$PWD/main_bot.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$PWD/</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>$PWD/log/bot_stdout.log</string>

    <key>StandardErrorPath</key>
    <string>$PWD/log/bot_stderr.log</string>
</dict>
</plist>
EOF
```
### Step 2: Load & Management Commands
Start Daemon:
```text
Bash
launchctl load ~/Library/LaunchAgents/com.user.cvbot.plist
```
Check Running Status:
```text
Bash
launchctl list | grep com.user.cvbot
```
Tail Live Output Logs:
```text
Bash
tail -f log/bot_stdout.log
```
Tail Live Error Logs:
```text
Bash
tail -f log/bot_stderr.log
```
Restart Daemon:
```text
Bash
launchctl unload ~/Library/LaunchAgents/com.user.cvbot.plist
launchctl load ~/Library/LaunchAgents/com.user.cvbot.plist
```
Stop Daemon:
```text
Bash
launchctl unload ~/Library/LaunchAgents/com.user.cvbot.plist
```

## Testing through telegram
### How to Test the Telegram Bot
Activate your Python virtual environment and launch the listener script:
```text
Bash
source .venv/bin/activate
python main_bot.py
```
Open Telegram and navigate to your bot's chat.

Send /start to verify connectivity.

Send a valid LinkedIn Job Posting URL (e.g., https://www.linkedin.com/jobs/view/4429205456/).

Send an invalid link (e.g., https://google.com or plain text) to verify that the guardrail instantly blocks malformed requests.

### Expected Output in Telegram & Local Filesystem
Interactive Telegram Chat Flow
On /start:
```text
Plaintext
👋 Executive CV Generator Ready!
```
Send a valid LinkedIn Job URL to generate your tailored CV and Cover Letter.
On Invalid Input (e.g., plain text or general URLs):
```text
Plaintext
⚠️ Invalid Link Format!
```
Please send a valid LinkedIn Job URL.
📍 Format: [https://www.linkedin.com/jobs/view/](https://www.linkedin.com/jobs/view/)<JOB_ID>/
On Valid LinkedIn Job Link (Immediate Processing Status):
```text
Plaintext
🚀 Valid LinkedIn URL detected!
⏳ Running local Ollama pipeline...
```
On Completion (Edits status message automatically):
```text
Plaintext
✅ Process Completed Successfully!

🎯 Role: Enterprise Architect
🏢 Company: Posti Group Oyj

⏱️ Total Pipeline Time: 0.45 mins

📁 Files saved locally in output/
Local Output Folder (output/)
```
Upon completion, four documents are automatically compiled and stored in your project's local output/ directory:
```text
📄 output/cv_postigroupoyj_enterprisearchitect.md (Raw Markdown CV)
📕 output/cv_postigroupoyj_enterprisearchitect.pdf (Print-styled 2-page Executive CV)
📄 output/cover_postigroupoyj_enterprisearchitect.md (Raw Markdown Cover Letter)
📕 output/cover_postigroupoyj_enterprisearchitect.pdf (Print-styled Cover Letter PDF)
📊 log/history.json (Structured history log)
```

# 📊 Job History (history.json) Sample Output
```JSON
[
  {
    "id": 1,
    "timestamp": "2026-08-01 15:32:25",
    "company": "ABB",
    "role": "Systems Operations Specialist",
    "linkedin_url": "https://www.linkedin.com/jobs/view/4447505488/",
    "files": {
      "cv_md": "cv_abb_systems_operations_specialist.md",
      "cv_pdf": "cv_abb_systems_operations_specialist.pdf",
      "cover_md": "cover_letter_abb_systems_operations_specialist.md",
      "cover_pdf": "cover_letter_abb_systems_operations_specialist.pdf"
    },
    "execution_time_min": "6.22"
  },
  {
    "id": 2,
    "timestamp": "2026-08-01 15:37:03",
    "company": "ABB",
    "role": "Business Analyst Senior Manager",
    "linkedin_url": "https://www.linkedin.com/jobs/view/4444343007/",
    "files": {
      "cv_md": "cv_abb_business_analyst_senior_manager.md",
      "cv_pdf": "cv_abb_business_analyst_senior_manager.pdf",
      "cover_md": "cover_letter_abb_business_analyst_senior_manager.md",
      "cover_pdf": "cover_letter_abb_business_analyst_senior_manager.pdf"
    },
    "execution_time_min": "5.40"
  }
] 
```
