# JARVIS — Voice AI Assistant

## Overview
JARVIS (Just A Rather Very Intelligent System) is a voice-first AI assistant for Windows and macOS. It runs locally on your machine, connecting to Apple Calendar, Mail, Notes (macOS), and can spawn Copilot CLI sessions for development tasks.

## Quick Start
When a user clones this repo and uses GitHub Copilot CLI, help them:
1. Copy .env.example to .env
2. Install GitHub Copilot CLI: npm install -g @github/copilot
3. Install Piper TTS: pip install piper-tts onnxruntime
4. Download a Piper voice model from https://github.com/rhasspy/piper/releases (e.g., en_GB-alan-medium.onnx)
5. Place voice model in ./voices/ directory
6. Install Python dependencies: pip install -r requirements.txt
7. Install frontend dependencies: cd frontend && npm install
8. (Optional for macOS) Generate SSL certs: openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes -subj '/CN=localhost'
9. Run the backend: python server.py
10. Run the frontend: cd frontend && npm run dev
11. Open Chrome to http://localhost:5173
12. Click to enable audio, speak to JARVIS

## Architecture
- **Backend**: FastAPI + Python (server.py, ~2300 lines)
- **Frontend**: Vite + TypeScript + Three.js (audio-reactive orb)
- **Communication**: WebSocket (JSON messages + binary audio)
- **AI**: Copilot CLI (fast and smart models)
- **TTS**: Piper (local neural TTS) with pyttsx3 (Windows SAPI5) fallback
- **System**: AppleScript for Calendar, Mail, Notes (macOS), PowerShell automation (Windows)

## Key Files
- `server.py` — Main server, WebSocket handler, LLM integration, action system
- `tts_access.py` — Piper TTS + pyttsx3 integration with automatic fallback
- `frontend/src/orb.ts` — Three.js particle orb visualization
- `frontend/src/voice.ts` — Web Speech API + audio playback
- `frontend/src/main.ts` — Frontend state machine
- `memory.py` — SQLite memory system with FTS5 search
- `calendar_access.py` — Apple Calendar integration via AppleScript (macOS)
- `mail_access.py` — Apple Mail integration (READ-ONLY, macOS)
- `notes_access.py` — Apple Notes integration (macOS)
- `actions.py` — System actions (Terminal/PowerShell, Chrome, Copilot CLI)
- `browser.py` — Playwright web automation
- `work_mode.py` — Persistent Copilot CLI sessions

## Environment Variables
- `COPILOT_CLI_ENABLED` — toggle Copilot CLI usage
- `COPILOT_MODEL_FAST` / `COPILOT_MODEL_SMART` — model choices for fast vs deep responses
- `COPILOT_TIMEOUT` — CLI call timeout in seconds
- `TTS_ENGINE` — `piper` (default, local neural TTS) or `pyttsx3` (Windows SAPI5)
- `PIPER_VOICE` — Piper voice name (e.g., en_GB-alan-medium, en_US-ryan-high)
- `PIPER_MODEL_PATH` — Optional explicit path to .onnx model file
- `PIPER_SAMPLE_RATE` — Audio sample rate (default: 22050)
- `PYTTSX3_VOICE` — Windows SAPI5 voice name (optional, empty = default)
- `PYTTSX3_RATE` — Speech rate in words per minute (default: 180)
- `TTS_VOICE` — Legacy fallback voice setting
- `USER_NAME` (optional) — Your name for JARVIS to use
- `CALENDAR_ACCOUNTS` (optional) — Comma-separated calendar emails (macOS only)

## Conventions
- JARVIS personality: British butler, dry wit, economy of language
- Max 1-2 sentences per voice response
- Action tags: [ACTION:BUILD], [ACTION:BROWSE], [ACTION:RESEARCH], etc.
- AppleScript for all macOS integrations (no OAuth needed)
- PowerShell for Windows terminal automation
- Read-only for Mail (safety by design)
- SQLite for all local data storage
