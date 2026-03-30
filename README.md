# JARVIS

**Just A Rather Very Intelligent System.**

A voice-first AI assistant that runs on your Mac or Windows PC. Talk to it, and it talks back -- with a British accent, dry wit, and an audio-reactive particle orb straight out of the MCU.

JARVIS connects to your Apple Calendar, Mail, and Notes (macOS only). It can browse the web, spawn Copilot CLI sessions to build entire projects, and plan your day -- all through natural voice conversation.

> "Will do, sir."

<!-- TODO: Add demo GIF or screenshot here -->
<!-- ![JARVIS Demo](docs/demo.gif) -->

---

## Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| **macOS** | ✅ Full support | All features including Calendar, Mail, Notes integration |
| **Windows 11** | ✅ Supported | Voice, browser, memory work. Calendar/Mail/Notes disabled. Uses local LLM + TTS. |
| **Linux** | 🚧 Experimental | Core features work, system integrations need platform-specific implementations |

### Windows 11 Setup

The Windows version uses **GitHub Copilot CLI** plus lightweight, fully offline TTS:
- **Piper TTS** (neural-quality, CPU-friendly, ~25MB models) - Primary engine
- **pyttsx3** (Windows SAPI5 native voices) - Automatic fallback

**See [SETUP_WINDOWS.md](SETUP_WINDOWS.md) for complete Windows setup guide.**

Quick Windows start:
```powershell
# After setting up local services (see SETUP_WINDOWS.md)
.\start-jarvis.ps1
```

---

## What It Does

- **Voice conversation** -- speak naturally, get spoken responses with a JARVIS voice
- **Builds software** -- say "build me a landing page" and watch Copilot CLI do the work
- **Reads your calendar** -- "What's on my schedule today?" (macOS only)
- **Reads your email** -- "Any unread messages?" (read-only, by design, macOS only)
- **Browses the web** -- "Search for the best restaurants in Austin"
- **Manages tasks** -- "Remind me to call the client tomorrow"
- **Takes notes** -- "Save that as a note"
- **Remembers things** -- "I prefer React over Vue" (it remembers next time)
- **Plans your day** -- combines calendar, tasks, and priorities into a plan
- **Sees your screen** -- knows what apps are open for context-aware responses
- **Audio-reactive orb** -- a Three.js particle visualization that pulses with JARVIS's voice

## Requirements

### macOS
- **macOS** (uses AppleScript for Calendar, Mail, Notes integration)
- **Python 3.11+**
- **Node.js 18+**
- **Google Chrome** (required for Web Speech API)
- **GitHub Copilot CLI** (`npm install -g @github/copilot`) — powers the AI brain
- **Edge-TTS** (included via `edge-tts` package) or optional Kokoro local TTS

### Windows 11
- **Windows 11**
- **Python 3.10+**
- **Node.js 18+**
- **Google Chrome or Edge**
- **GitHub Copilot CLI** (`npm install -g @github/copilot`)
- **TTS**: default Edge neural voices; optional local Kokoro for offline/low-latency

## Manual Setup (macOS)

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/jarvis.git
cd jarvis

# 2. Set up environment
cp .env.example .env
# Edit .env with your API keys (see below)

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install frontend dependencies
cd frontend && npm install && cd ..

# 5. Generate SSL certificates (needed for secure WebSocket)
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes -subj '/CN=localhost'

# 6. Start the backend (Terminal 1)
python server.py

# 7. Start the frontend (Terminal 2)
cd frontend && npm run dev

# 8. Open Chrome
open http://localhost:5173
```

Click the page once to enable audio, then speak. JARVIS will respond.

## Configuration

### macOS (Cloud APIs)
Edit your `.env` file:

```env
# Copilot CLI
COPILOT_CLI_ENABLED=true
COPILOT_MODEL_FAST=gpt-4.1-mini
COPILOT_MODEL_SMART=gpt-4.1
COPILOT_TIMEOUT=60

# TTS (Edge by default, set kokoro for local)
TTS_ENGINE=edge
TTS_VOICE=en-GB-RyanNeural
# TTS_KOKORO_VOICE=af_bella
# TTS_KOKORO_LANG=b
# TTS_KOKORO_DEVICE=cpu

# Optional -- your name (JARVIS will address you personally)
USER_NAME=Tony

# Optional -- specific calendar accounts (comma-separated)
# Leave empty to auto-discover all calendars
CALENDAR_ACCOUNTS=you@gmail.com,work@company.com
```

### Windows 11 (Local LLM + TTS)
Edit your `.env` file:

```env
# Copilot CLI
COPILOT_CLI_ENABLED=true
COPILOT_MODEL_FAST=gpt-4.1-mini
COPILOT_MODEL_SMART=gpt-4.1
COPILOT_TIMEOUT=60

# Local-friendly TTS
TTS_ENGINE=edge
TTS_VOICE=en-GB-RyanNeural
# Switch to Kokoro for local/offline synthesis:
# TTS_ENGINE=kokoro
# TTS_KOKORO_VOICE=af_bella
# TTS_KOKORO_LANG=b
# TTS_KOKORO_DEVICE=cpu

# Optional
USER_NAME=Tony
```

## Architecture

```
Microphone -> Web Speech API -> WebSocket -> FastAPI -> Copilot CLI (fast/smart) -> Kokoro (local) or Edge-TTS -> WebSocket -> Speaker
                                                |
                                                v
                                        Copilot CLI Tasks
                                        (spawns real dev work)
                                                |
                                                v
                                        AppleScript Bridge
                                        (Calendar, Mail, Notes, Terminal)
```

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Python (`server.py`, ~2300 lines) |
| Frontend | Vite + TypeScript + Three.js |
| Communication | WebSocket (JSON messages + binary audio) |
| AI (fast) | Copilot fast model (`COPILOT_MODEL_FAST`) |
| AI (deep) | Copilot smart model (`COPILOT_MODEL_SMART`) |
| TTS | Kokoro (local) or Edge neural voices |
| System | AppleScript for all macOS integrations |

## How the Voice Loop Works

1. You speak into your microphone
2. Chrome's Web Speech API transcribes your speech in real-time
3. The transcript is sent to the server via WebSocket
4. JARVIS detects intent -- conversation, action, or build request
5. For actions: spawns a Copilot CLI subprocess or runs AppleScript
6. Generates a response via Copilot CLI (optimized for speed)
7. TTS converts the response to speech (Edge-TTS by default, Kokoro if configured)
8. Audio streams back to the browser via WebSocket
9. The Three.js orb deforms and pulses in response to the audio
10. Background tasks notify you proactively when they complete

## Key Files

| File | Purpose |
|------|---------|
| `server.py` | Main server -- WebSocket handler, LLM, action system |
| `frontend/src/orb.ts` | Three.js particle orb visualization |
| `frontend/src/voice.ts` | Web Speech API + audio playback |
| `frontend/src/main.ts` | Frontend state machine |
| `memory.py` | SQLite memory system with FTS5 full-text search |
| `calendar_access.py` | Apple Calendar integration via AppleScript |
| `mail_access.py` | Apple Mail integration (read-only) |
| `notes_access.py` | Apple Notes integration |
| `actions.py` | System actions (Terminal, Chrome, Copilot CLI) |
| `browser.py` | Playwright web automation |
| `work_mode.py` | Persistent Copilot CLI sessions |
| `planner.py` | Multi-step task planning with smart questions |

## Features in Detail

### Action System
JARVIS uses action tags to trigger real system actions:
- `[ACTION:BUILD]` -- spawns Copilot CLI to build a project
- `[ACTION:BROWSE]` -- opens Chrome to a URL or search query
- `[ACTION:RESEARCH]` -- deep research with Copilot CLI, outputs an HTML report
- `[ACTION:PROMPT_PROJECT]` -- connects to an existing project via Copilot CLI
- `[ACTION:ADD_TASK]` -- creates a tracked task with priority and due date
- `[ACTION:REMEMBER]` -- stores a fact for future context

### Memory System
JARVIS remembers things you tell it using SQLite with FTS5 full-text search. Preferences, decisions, and facts persist across sessions.

### Calendar & Mail
All macOS integrations use AppleScript -- no OAuth flows, no token management. Just native system access. Mail is intentionally read-only for safety.

## Contributing

Contributions are welcome. Some areas that could use work:

- **Linux support** -- add Linux-specific system integrations (D-Bus, etc.)
- **Windows enhancements** -- add Outlook integration, PowerShell automation
- **Alternative TTS engines** -- add ElevenLabs, OpenAI TTS support
- **Alternative LLMs** -- add OpenAI, Gemini support
- **Mobile client** -- a companion app for voice interaction on the go
- **Plugin system** -- make it easy to add new actions and integrations

Please open an issue before submitting large PRs so we can discuss the approach.

## License

Free for personal, non-commercial use. Commercial use requires a license — visit [ethanplus.ai](https://ethanplus.ai) for inquiries. See [LICENSE](LICENSE) for details.

## Credits

Built by [Ethan Rogers](https://ethanplus.ai).

Powered by GitHub Copilot CLI with Kokoro or Edge neural TTS.

Inspired by the AI that started it all -- Tony Stark's JARVIS.

> **Disclaimer:** This is an independent fan project and is not affiliated with, endorsed by, or connected to Marvel Entertainment, The Walt Disney Company, or any related entities. The JARVIS name and character are property of Marvel Entertainment.
