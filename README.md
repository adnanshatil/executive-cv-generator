# 🚀 Executive CV & Cover Letter Generator (Ollama + gemma4:e4b + Telegram)

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
├── log/                        # 📁 Logs directory for daemon stdout & stderr
│
└── src/                        # 🧠 Core Application Package
    ├── __init__.py             # Package initializer
    ├── config.py               # Path definitions & environment variable loader
    ├── utils.py                # File I/O, timer utilities, PDF compiler & text sanitizers
    ├── scraper.py              # LinkedIn HTML parser & URL validation guardrails
    ├── agents.py               # Ollama prompt engineering & response parsing
    └── pipeline.py             # Main orchestrator connecting scraper, agents & output generator
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