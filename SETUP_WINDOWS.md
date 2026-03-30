# JARVIS — Windows 11 Setup Guide

This guide shows you how to run JARVIS on **Windows 11** using **local** LLM and TTS servers instead of cloud APIs.

## Overview

The Windows version of JARVIS uses:
1. **free-claude-code** proxy running locally (replaces Anthropic API)
2. **Fish Speech** local TTS server (replaces Fish Audio cloud API)
3. **Stubbed system integration** (Calendar, Mail, Notes features disabled on Windows)

## Prerequisites

- Windows 11
- Python 3.10 or newer
- Git
- At least 8GB RAM (16GB+ recommended for local LLM)
- NVIDIA GPU with CUDA support (optional but recommended for faster inference)

---

## SECTION 1: Step-by-Step Windows 11 Setup

### Step 1: Install Required Software

#### 1.1 Install Python
```powershell
# Download Python 3.11+ from python.org or use winget
winget install Python.Python.3.11

# Verify installation
python --version
pip --version
```

#### 1.2 Install Git
```powershell
winget install Git.Git

# Restart your terminal after installation
```

#### 1.3 Install uv (Optional, for faster Python package management)
```powershell
pip install uv
```

### Step 2: Set Up free-claude-code Proxy

The free-claude-code proxy lets you use local LLMs (LM Studio, NVIDIA NIM, etc.) with the Anthropic SDK.

#### 2.1 Clone and Install free-claude-code
```powershell
# Clone the proxy
cd C:\
git clone https://github.com/nah1121/free-claude-code.git
cd free-claude-code

# Install dependencies
pip install -r requirements.txt
```

#### 2.2 Configure free-claude-code

Create or edit `.env` in the free-claude-code directory:
```env
# For LM Studio (recommended for beginners)
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_API_KEY=lm-studio

# Model mappings (free-claude-code will translate Anthropic model names)
# MODEL_HAIKU -> fast local model (e.g., Qwen2.5-7B-Instruct)
# MODEL_OPUS -> stronger local model (e.g., Qwen2.5-14B-Instruct)

# Proxy will run on port 8082
PORT=8082
```

**Recommended LM Studio Models for JARVIS:**
- **Fast (Haiku)**: `bartowski/Qwen2.5-7B-Instruct-GGUF` (Q4_K_M)
- **Strong (Opus)**: `bartowski/Qwen2.5-14B-Instruct-GGUF` (Q4_K_M)
- **Alternative**: `TheBloke/Mistral-7B-Instruct-v0.2-GGUF`

#### 2.3 Install and Start LM Studio

1. Download LM Studio from https://lmstudio.ai
2. Install and launch LM Studio
3. Download a model from the "Search" tab (e.g., Qwen2.5-7B-Instruct Q4_K_M)
4. Go to "Local Server" tab
5. Select your model and click "Start Server"
6. Verify it's running on `http://localhost:1234`

#### 2.4 Start free-claude-code Proxy
```powershell
# In the free-claude-code directory
cd C:\free-claude-code
python proxy.py

# You should see: "Proxy running on http://localhost:8082"
```

**Alternative: Using NVIDIA NIM (Faster, requires NVIDIA GPU)**
```powershell
# Install NVIDIA NIM CLI
pip install nvidia-nim

# Run a model
nim run meta/llama3-8b-instruct

# Update free-claude-code .env with NIM endpoint
# OPENAI_BASE_URL=http://localhost:8000/v1
```

### Step 3: Set Up Fish Speech Local TTS

Fish Speech provides a local TTS server with voice cloning capabilities.

#### 3.1 Clone Fish Speech
```powershell
cd C:\
git clone https://github.com/fishaudio/fish-speech.git
cd fish-speech
```

#### 3.2 Install Fish Speech Dependencies
```powershell
# Create a virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install PyTorch with CUDA support (if you have NVIDIA GPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install Fish Speech
pip install -e .

# Download required models
python tools/download_models.py
```

#### 3.3 Download JARVIS-like Voice Model

Fish Speech supports voice cloning. For a JARVIS-like British voice:

```powershell
# Option 1: Use a pre-trained voice (fast)
# Fish Speech comes with several voices in models/voices/

# Option 2: Clone a JARVIS voice (advanced)
# Place a 10-30 second audio sample of JARVIS voice in:
# C:\fish-speech\references\jarvis.wav

# Then use it with reference_audio parameter
```

**Recommended Pre-trained Voice for JARVIS:**
- Use the "male_en" voice for a British-style accent
- Voice ID: Just reference the audio file path

#### 3.4 Start Fish Speech Server
```powershell
cd C:\fish-speech
.\venv\Scripts\activate

# Start the API server (runs on http://localhost:8080 by default)
python -m fish_speech.api_server

# Or specify a different port
python -m fish_speech.api_server --port 8080

# You should see: "Server running on http://localhost:8080"
```

**Fish Speech API Endpoints:**
- POST `/v1/tts` - Generate speech (similar to Fish Audio cloud API)
- GET `/v1/voices` - List available voices

### Step 4: Clone and Set Up JARVIS

#### 4.1 Clone JARVIS (Windows Fork)
```powershell
cd C:\
git clone https://github.com/nah1121/jarvis.git
cd jarvis
```

#### 4.2 Install Python Dependencies
```powershell
pip install -r requirements.txt

# Or using uv (faster)
uv pip install -r requirements.txt
```

#### 4.3 Install Frontend Dependencies
```powershell
cd frontend
npm install
cd ..
```

#### 4.4 Generate SSL Certificates (for HTTPS)
```powershell
# Using OpenSSL (install via: winget install OpenSSL.OpenSSL)
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/CN=localhost"

# Files key.pem and cert.pem will be created in the current directory
```

#### 4.5 Configure Environment Variables

Copy `.env.example` to `.env`:
```powershell
copy .env.example .env
```

Edit `.env` with your settings:
```env
# Local Anthropic Proxy (free-claude-code)
ANTHROPIC_BASE_URL=http://localhost:8082
ANTHROPIC_API_KEY=freecc

# Local Fish Speech TTS
TTS_BASE_URL=http://localhost:8080
TTS_VOICE_ID=male_en
# Or use a custom reference audio file:
# TTS_REFERENCE_AUDIO=C:\fish-speech\references\jarvis.wav

# Optional: Your name
USER_NAME=Tony

# Note: Calendar, Mail, Notes features are disabled on Windows
```

### Step 5: Run JARVIS

#### 5.1 Start the Backend
```powershell
# In the jarvis directory
python server.py

# You should see:
# INFO: JARVIS server starting
# INFO: Uvicorn running on https://0.0.0.0:8443
```

#### 5.2 Start the Frontend (in a new terminal)
```powershell
cd C:\jarvis\frontend
npm run dev

# You should see:
# VITE ready in Xms
# Local: http://localhost:5173
```

#### 5.3 Open in Browser
1. Open Google Chrome or Edge
2. Navigate to `http://localhost:5173`
3. Click "Enable Audio" when prompted
4. **Speak to JARVIS!**

### Step 6: Using PowerShell Launch Script (Recommended)

Use the included PowerShell script to start everything at once:

```powershell
# From the jarvis directory
.\start-jarvis.ps1
```

This will:
1. Check if LM Studio is running (warns if not)
2. Check if free-claude-code proxy is running (warns if not)
3. Check if Fish Speech server is running (warns if not)
4. Start JARVIS backend server
5. Start JARVIS frontend server
6. Open browser to http://localhost:5173

---

## SECTION 2: Technical Details

### Anthropic Client Configuration

The Windows version uses these environment variables for the local proxy:

```python
# In server.py (lines ~63-68)
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "http://localhost:8082")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "freecc")

# Client initialization (line ~1318)
anthropic_client = anthropic.AsyncAnthropic(
    base_url=ANTHROPIC_BASE_URL,
    api_key=ANTHROPIC_API_KEY
)
```

### Local TTS Configuration

The `synthesize_speech` function now calls the local Fish Speech server:

```python
# In server.py (lines ~1037-1066)
TTS_BASE_URL = os.getenv("TTS_BASE_URL", "http://localhost:8080")
TTS_VOICE_ID = os.getenv("TTS_VOICE_ID", "male_en")
TTS_REFERENCE_AUDIO = os.getenv("TTS_REFERENCE_AUDIO", "")

async def synthesize_speech(text: str) -> Optional[bytes]:
    """Generate speech using local Fish Speech server."""
    if not TTS_BASE_URL:
        log.warning("TTS_BASE_URL not set, skipping TTS")
        return None

    # Call local Fish Speech API
    # POST http://localhost:8080/v1/tts
    # ...
```

### Windows Compatibility

#### Disabled Features
The following macOS-specific features are **disabled on Windows** (with graceful fallbacks):

- **Calendar Access** (`calendar_access.py`) - All AppleScript calls return empty results
- **Mail Access** (`mail_access.py`) - All AppleScript calls return empty results
- **Notes Access** (`notes_access.py`) - All AppleScript calls return empty results
- **Terminal Actions** (`actions.py`) - Terminal/Finder automation disabled

#### What Still Works
✅ Voice conversation loop (speech-to-text → LLM → TTS)
✅ Three.js particle orb visualization
✅ Web browser automation (Playwright)
✅ Claude Code task management (if Claude Code installed on Windows)
✅ Memory system (SQLite-based)
✅ Research mode
✅ Work mode / planning mode

---

## SECTION 3: Additional Recommendations

### Best Model Combinations in free-claude-code

For optimal JARVIS experience:

**Fast Response (Haiku equivalent):**
- Qwen2.5-7B-Instruct (Q4_K_M) - Excellent instruction following
- Mistral-7B-Instruct-v0.2 - Very fast, good for conversations
- Phi-3-mini - Ultra-fast for simple queries

**Strong Reasoning (Opus equivalent):**
- Qwen2.5-14B-Instruct (Q4_K_M) - Best overall quality
- Llama-3-8B-Instruct - Good balance
- Mixtral-8x7B-Instruct - Strongest reasoning (requires 32GB RAM)

**free-claude-code .env example:**
```env
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_API_KEY=lm-studio
PORT=8082

# Model routing (optional, proxy auto-detects)
MODEL_HAIKU=qwen2.5-7b-instruct
MODEL_OPUS=qwen2.5-14b-instruct
```

### Recommended Fish Speech Settings

For best JARVIS voice quality:

1. **Use a reference audio sample:**
   - Find a 10-30 second clip of JARVIS from MCU films
   - Convert to WAV format (16kHz, mono)
   - Place in `C:\fish-speech\references\jarvis.wav`
   - Set `TTS_REFERENCE_AUDIO=C:\fish-speech\references\jarvis.wav`

2. **Adjust TTS parameters** (in server.py if needed):
   ```python
   {
       "text": text,
       "reference_audio": TTS_REFERENCE_AUDIO,
       "format": "mp3",
       "top_p": 0.7,        # Lower = more consistent voice
       "temperature": 0.7,   # Lower = more stable
       "repetition_penalty": 1.2
   }
   ```

3. **Fish Speech voices included:**
   - `male_en` - British male voice (closest to JARVIS)
   - `female_en` - Female voice
   - Custom cloned voices in `models/voices/`

### Performance Tips for Windows 11

#### GPU Acceleration (NVIDIA)
```powershell
# Verify CUDA is working
python -c "import torch; print(torch.cuda.is_available())"

# Should print: True

# Fish Speech automatically uses GPU if available
# LM Studio automatically uses GPU if available
```

#### RAM Requirements
- **Minimum**: 8GB (7B models)
- **Recommended**: 16GB (14B models)
- **Optimal**: 32GB (Mixtral, multiple models)

#### CPU-Only Mode (No NVIDIA GPU)
```powershell
# Install CPU-only PyTorch for Fish Speech
pip install torch torchvision torchaudio

# Use smaller quantized models in LM Studio (Q4_K_S instead of Q4_K_M)
```

#### Whisper Local (Optional, for offline speech-to-text)

The browser uses Web Speech API by default. For fully offline operation:

```powershell
pip install openai-whisper

# Then modify frontend to send audio to /api/transcribe endpoint
# (requires additional server.py changes)
```

### Firewall Configuration

If you have issues connecting to local servers:

```powershell
# Allow Python through Windows Firewall
netsh advfirewall firewall add rule name="Python" dir=in action=allow program="C:\Python311\python.exe" enable=yes

# Or disable firewall for private networks (not recommended for public networks)
```

### Troubleshooting

#### Issue: "Connection refused" errors

**Solution:**
1. Verify all services are running:
   ```powershell
   # Check LM Studio: http://localhost:1234
   curl http://localhost:1234/v1/models

   # Check free-claude-code: http://localhost:8082
   curl http://localhost:8082/health

   # Check Fish Speech: http://localhost:8080
   curl http://localhost:8080/v1/voices
   ```

2. Check if ports are in use:
   ```powershell
   netstat -ano | findstr "1234"
   netstat -ano | findstr "8082"
   netstat -ano | findstr "8080"
   ```

#### Issue: TTS is slow or not working

**Solution:**
1. Enable GPU acceleration in Fish Speech
2. Use a faster voice model
3. Reduce TTS quality settings
4. Check Fish Speech logs for errors

#### Issue: LLM responses are slow

**Solution:**
1. Use smaller models (7B instead of 14B)
2. Use higher quantization (Q4 instead of Q8)
3. Enable GPU acceleration in LM Studio
4. Reduce context window in free-claude-code

#### Issue: "Module not found" errors

**Solution:**
```powershell
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Or use uv
uv pip sync requirements.txt
```

---

## Quick Start Summary

```powershell
# 1. Start LM Studio with a model (http://localhost:1234)
# 2. Start free-claude-code proxy
cd C:\free-claude-code
python proxy.py

# 3. Start Fish Speech server
cd C:\fish-speech
.\venv\Scripts\activate
python -m fish_speech.api_server

# 4. Start JARVIS (use the PowerShell script)
cd C:\jarvis
.\start-jarvis.ps1

# 5. Open http://localhost:5173 and talk to JARVIS!
```

---

## Differences from macOS Version

| Feature | macOS | Windows |
|---------|-------|---------|
| LLM | Anthropic API (cloud) | free-claude-code + local LLM |
| TTS | Fish Audio API (cloud) | Fish Speech (local) |
| Calendar | Apple Calendar (AppleScript) | ❌ Disabled |
| Mail | Apple Mail (AppleScript) | ❌ Disabled |
| Notes | Apple Notes (AppleScript) | ❌ Disabled |
| Terminal | Terminal.app automation | ❌ Disabled |
| Browser | Playwright ✅ | Playwright ✅ |
| Voice Loop | ✅ | ✅ |
| Memory | SQLite ✅ | SQLite ✅ |
| Frontend | Three.js orb ✅ | Three.js orb ✅ |

---

## Next Steps

- **Add Outlook integration** for Windows Mail/Calendar (future)
- **Add Windows Terminal automation** (PowerShell-based)
- **Optimize for AMD GPUs** (ROCm support)
- **Add offline Whisper STT** (fully local speech recognition)

## Support

For issues specific to:
- **JARVIS**: Open issue at https://github.com/nah1121/jarvis
- **free-claude-code**: Open issue at https://github.com/nah1121/free-claude-code
- **Fish Speech**: Open issue at https://github.com/fishaudio/fish-speech
- **LM Studio**: Visit https://lmstudio.ai/docs

---

**Marvel/Disney Legal Notice**: "JARVIS" and related character elements are trademarks of Marvel/Disney. This is an independent fan project not affiliated with or endorsed by Marvel or Disney.
