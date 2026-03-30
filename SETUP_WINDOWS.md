# JARVIS — Windows 11 Setup Guide (Kokoro + Edge-TTS)

This guide targets Windows 11 with ~8GB VRAM (or CPU-only). The default TTS uses Edge neural voices, with optional local **Kokoro** for offline, low-latency speech.

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

## 2) Choose Your TTS

- **Edge-TTS (default, easiest):** No GPU required, great quality. Already included via `edge-tts`.
- **Kokoro (local, lightweight):** ~82M params, works on CPU or small GPUs.

Kokoro install (optional):

```powershell
pip install "kokoro==0.9.4" numpy
# If you have CUDA and want GPU, install torch with your CUDA version first:
# pip install torch --index-url https://download.pytorch.org/whl/cu121
```

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

# TTS (choose one)
TTS_ENGINE=edge
TTS_VOICE=en-GB-RyanNeural        # Edge neural British voice
# For local Kokoro:
# TTS_ENGINE=kokoro
# TTS_KOKORO_VOICE=af_bella
# TTS_KOKORO_LANG=b
# TTS_KOKORO_DEVICE=cpu
```

## 4) Install Dependencies

```powershell
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

## 5) Run JARVIS

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
- For lowest VRAM use Kokoro on CPU (`TTS_KOKORO_DEVICE=cpu`); switch to GPU if available.
