# Quick Start: Piper TTS Setup

## 1. Install Piper TTS
```powershell
pip install piper-tts onnxruntime pyttsx3 pypiwin32
```

## 2. Download Voice Model
```powershell
mkdir voices
cd voices

# British voice (recommended for JARVIS)
curl -L -O https://github.com/rhasspy/piper/releases/download/2023.11.14-2/en_GB-alan-medium.onnx
curl -L -O https://github.com/rhasspy/piper/releases/download/2023.11.14-2/en_GB-alan-medium.onnx.json

cd ..
```

## 3. Configure .env
```env
TTS_ENGINE=piper
PIPER_VOICE=en_GB-alan-medium
```

## 4. Run Test
```powershell
python test_tts.py
```

## 5. Start JARVIS
```powershell
python server.py
# In another terminal:
cd frontend && npm run dev
```

## Troubleshooting

**Piper model not found?**
- Check files exist: `dir voices\en_GB-alan-medium.onnx*`
- Set explicit path: `PIPER_MODEL_PATH=./voices/en_GB-alan-medium.onnx`

**Import error?**
- Install: `pip install piper-tts onnxruntime`

**No audio?**
- Check fallback is working: Set `TTS_ENGINE=pyttsx3` in .env
- Restart server: `python server.py`

## Voice Options

**British (JARVIS-style):**
- `en_GB-alan-medium` - Classic British butler
- `en_GB-southern_english_male-medium` - Upper-class British

**American:**
- `en_US-ryan-high` - Deep male voice
- `en_US-amy-medium` - Female

Download from: https://github.com/rhasspy/piper/releases/tag/2023.11.14-2

## Performance

- **Latency:** ~0.5-1s per sentence
- **Memory:** ~100-150MB RAM
- **CPU:** 10-20% during synthesis
- **GPU:** Not required (CPU-only)
- **Quality:** Neural, professional

See [PIPER_INTEGRATION_GUIDE.md](PIPER_INTEGRATION_GUIDE.md) for complete details.
