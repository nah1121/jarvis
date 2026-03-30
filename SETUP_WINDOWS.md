# JARVIS — Windows 11 Setup Guide (Piper TTS + pyttsx3)

This guide targets Windows 11 with ~8GB VRAM (or CPU-only). The default TTS uses **Piper** (local neural-quality TTS, CPU-friendly), with **pyttsx3** (Windows SAPI5) as a simple fallback.

**Why Piper?**
- Lightweight (~25MB models), runs great on CPU or low-VRAM GPUs
- Neural-quality voices rivaling cloud services
- No heavy dependencies (unlike Kokoro which requires spacy/blis/build tools)
- Fully offline, no internet required
- Simple ONNX runtime, no CUDA required

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

## 2) Install Piper TTS (Primary Engine)

Piper is a fast, neural-quality TTS that runs well on 8GB systems. Two installation methods:

### Method A: Install via pip (Recommended)

```powershell
pip install piper-tts onnxruntime
```

### Method B: Download pre-built binaries (Alternative)

Download from: https://github.com/rhasspy/piper/releases
- Get the Windows binary release (piper.exe + dependencies)
- Extract to a folder (e.g., `C:\piper\`)
- Add to PATH or reference directly in code

## 3) Download a Piper Voice Model

Visit: https://github.com/rhasspy/piper/releases/tag/2023.11.14-2

**Recommended voices for JARVIS (British butler style):**
- `en_GB-alan-medium.onnx` (British English, male, good quality)
- `en_GB-southern_english_male-medium.onnx` (British, formal)
- `en_US-ryan-high.onnx` (American, deep male voice - Ryan Reynolds style)

**Other quality voices:**
- `en_US-amy-medium.onnx` (American female)
- `en_US-joe-medium.onnx` (American male, neutral)

Download both the `.onnx` model file and `.onnx.json` config file (same name).

**Where to place voice models:**
- Option 1: Create `./voices/` folder in JARVIS root directory
- Option 2: Place in `C:\Users\<YourName>\.local\share\piper\voices\`
- Option 3: Specify custom path via `PIPER_MODEL_PATH` in .env

Example download:
```powershell
# Create voices directory
mkdir voices
cd voices

# Download en_GB-alan-medium (British voice)
curl -L -O https://github.com/rhasspy/piper/releases/download/2023.11.14-2/en_GB-alan-medium.onnx
curl -L -O https://github.com/rhasspy/piper/releases/download/2023.11.14-2/en_GB-alan-medium.onnx.json

cd ..
```

## 4) Install pyttsx3 Fallback (Windows SAPI5)

pyttsx3 uses Windows built-in voices as a simple offline fallback:

```powershell
pip install pyttsx3 pypiwin32
```

No additional setup needed - uses Windows default voices.

## 5) Configure JARVIS

```powershell
git clone https://github.com/nah1121/jarvis.git
cd jarvis
copy .env.example .env
```

Edit `.env`:

```env
COPILOT_CLI_ENABLED=true
COPILOT_MODEL_FAST=gpt-4.1-mini
COPILOT_MODEL_SMART=gpt-4.1
COPILOT_TIMEOUT=60

# TTS Configuration
TTS_ENGINE=piper
PIPER_VOICE=en_GB-alan-medium
# PIPER_MODEL_PATH=./voices/en_GB-alan-medium.onnx
# PIPER_SAMPLE_RATE=22050

# Fallback pyttsx3 settings (optional)
# PYTTSX3_VOICE=David
# PYTTSX3_RATE=180

USER_NAME=Tony
```

## 6) Install Dependencies

```powershell
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

## 7) Run JARVIS

```powershell
python server.py
# In another terminal
cd frontend
npm run dev
```

Open http://localhost:5173 and allow microphone access.

## Voice Selection Guide

### Best Voices for JARVIS Character

**British Butler Style (Recommended):**
1. `en_GB-alan-medium` - Classic British, formal tone
2. `en_GB-southern_english_male-medium` - Upper-class British

**Deep/Authoritative:**
1. `en_US-ryan-high` - Deep American male (similar to Ryan Reynolds)
2. `en_US-hfc_male-medium` - Authoritative male

**Testing Different Voices:**
```powershell
# Download multiple voices to ./voices/
# Update PIPER_VOICE in .env
# Restart server.py
```

## Performance on 8GB VRAM Systems

**Piper TTS Performance:**
- Model size: ~25MB (vs 82MB for Kokoro, 1GB+ for Fish Speech)
- CPU usage: Low (~10-20% on modern CPUs)
- GPU usage: Optional (can use GPU acceleration but CPU works great)
- Latency: ~0.5-1s for typical sentences
- Memory: ~100MB RAM during synthesis
- Quality: Neural-quality, indistinguishable from cloud services

**pyttsx3 Fallback:**
- Near-instant (uses Windows native SAPI5)
- Zero GPU/VRAM usage
- Lower quality than Piper but acceptable for fallback

**Recommended for 8GB VRAM:**
- Use `TTS_ENGINE=piper` (default)
- Place model in `./voices/` directory
- Piper will run on CPU by default (no CUDA needed)
- pyttsx3 automatically falls back if Piper fails

## Troubleshooting

### Piper model not loading
**Error:** `Piper model not found`
- Ensure `.onnx` and `.onnx.json` files are in `./voices/` directory
- Check file names match exactly (e.g., `en_GB-alan-medium.onnx`)
- Verify PIPER_VOICE in .env matches the downloaded model name (without .onnx extension)
- Try setting explicit path: `PIPER_MODEL_PATH=./voices/en_GB-alan-medium.onnx`

### pyttsx3 not working
**Error:** `pyttsx3 initialization failed`
- Install Windows speech components: `pip install pypiwin32`
- Restart Windows Speech Runtime service
- Try different voice: List available voices with test script

### Low audio quality
- Download "high" quality models instead of "low" or "medium"
- Example: `en_US-ryan-high.onnx` instead of `en_US-ryan-low.onnx`
- Higher quality = larger file but better sound (~50MB vs 25MB)

### Slow TTS generation
- Piper should be fast (~0.5-1s). If slow:
  - Close other GPU applications
  - Use CPU mode (default, no changes needed)
  - Try a "medium" quality model instead of "high"

### Import errors with piper-tts
- Ensure onnxruntime is installed: `pip install onnxruntime`
- On some systems you may need: `pip install onnxruntime-gpu` (if using GPU)

## Windows-Specific Notes
- Copilot CLI binary is `copilot` (PowerShell may also show `copilot.cmd`)
- If Copilot prompts for interactive confirmation, re-run `copilot auth login`
- Calendar/Mail/Notes remain stubbed on Windows (macOS-only features)
- Piper works perfectly on CPU - no GPU/CUDA required
- pyttsx3 uses Windows narrator voices (install more via Windows Settings)

## Advanced: Custom Voice Configuration

### List available pyttsx3 voices
```python
import pyttsx3
engine = pyttsx3.init()
voices = engine.getProperty('voices')
for voice in voices:
    print(f"ID: {voice.id}")
    print(f"Name: {voice.name}")
    print(f"Languages: {voice.languages}")
    print("---")
```

### Download more Piper voices
Visit: https://huggingface.co/rhasspy/piper-voices/tree/main
- Browse by language
- Download `.onnx` + `.onnx.json` files
- Place in `./voices/` directory
- Update `PIPER_VOICE` in `.env`

## Comparison: Piper vs Kokoro vs Edge-TTS

| Feature | Piper (New) | Kokoro (Failed) | Edge-TTS (Cloud) |
|---------|-------------|-----------------|------------------|
| **Installation** | ✅ Simple pip | ❌ Build errors | ✅ Simple pip |
| **Dependencies** | onnxruntime only | spacy, blis, MSVC++ | None (cloud) |
| **Model Size** | 25-50MB | 82MB | N/A (cloud) |
| **Quality** | Neural-high | Neural-high | Neural-high |
| **Speed** | Fast (0.5-1s) | Fast | Network-dependent |
| **Offline** | ✅ Fully | ✅ Fully | ❌ Requires internet |
| **8GB VRAM** | ✅ CPU-friendly | ⚠️ Works but install issues | ✅ No GPU needed |
| **Windows 11** | ✅ Works perfectly | ❌ MSVC++ build errors | ✅ Works |

**Conclusion:** Piper is the best choice for Windows 11 with limited hardware - reliable installation, great quality, fully offline, and CPU-friendly.
