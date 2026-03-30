# JARVIS — Windows 11 Setup Guide (Copilot CLI)

This guide walks through running JARVIS on **Windows 11** with the GitHub Copilot CLI and local Fish Speech TTS.

## Prerequisites
- Windows 11
- Python 3.10+ and pip
- Node.js (for frontend)  
- Git
- GitHub Copilot CLI (`npm install -g @github/copilot`)

## 1) Install Required Tools

```powershell
# Python
winget install Python.Python.3.11
python --version

# Git
winget install Git.Git

# Node.js
winget install OpenJS.NodeJS
node --version

# Copilot CLI
npm install -g @github/copilot
copilot auth status   # login if prompted
```

Ensure PowerShell scripts can run locally:
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned -Force
```

## 2) Set Up Local Fish Speech (TTS)
```powershell
git clone https://github.com/fishaudio/fish-speech.git
cd fish-speech
python -m venv venv
.\venv\Scripts\activate
pip install -e .
python tools/download_models.py
python -m fish_speech.api_server --port 8080
```
Note the server URL: `http://localhost:8080`.

## 3) Configure JARVIS
```powershell
git clone https://github.com/nah1121/jarvis.git
cd jarvis
copy .env.example .env
```
Edit `.env`:
```
COPILOT_CLI_ENABLED=true
COPILOT_MODEL_FAST=gpt-4.1-mini
COPILOT_MODEL_SMART=gpt-4.1
COPILOT_TIMEOUT=60
TTS_BASE_URL=http://localhost:8080
USER_NAME=Your Name
```

Install Python deps and frontend deps:
```powershell
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

## 4) Run JARVIS
```powershell
python server.py
# In another terminal
cd frontend
npm run dev
```
Open http://localhost:5173 and allow microphone access.

## Windows Notes
- Copilot CLI binary is `copilot` (PowerShell may also show `copilot.cmd`).
- If Copilot prompts for interactive confirmation, re-run `copilot auth login`.
- Calendar/Mail/Notes remain stubbed on Windows.
