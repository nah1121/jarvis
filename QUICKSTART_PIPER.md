# Quick Start: Piper TTS Setup

## 1. Install Piper TTS
```powershell
pip install piper-tts pyttsx3 pypiwin32

# For GPU acceleration (optional, requires NVIDIA GPU + CUDA):
pip install onnxruntime-gpu
# OR for CPU only:
pip install onnxruntime
```

## 2. Download Voice Model

**Standard Quality (~25-40MB):**
```powershell
mkdir voices
cd voices

# British voice (recommended for JARVIS)
curl -L -O https://github.com/rhasspy/piper/releases/download/2023.11.14-2/en_GB-alan-medium.onnx
curl -L -O https://github.com/rhasspy/piper/releases/download/2023.11.14-2/en_GB-alan-medium.onnx.json

cd ..
```

**High Quality (~50-60MB) - Better for GPU:**
```powershell
mkdir voices
cd voices

# American - Best quality available
curl -L -O https://github.com/rhasspy/piper/releases/download/2023.11.14-2/en_US-libritts-high.onnx
curl -L -O https://github.com/rhasspy/piper/releases/download/2023.11.14-2/en_US-libritts-high.onnx.json

# OR British - Very natural
curl -L -O https://github.com/rhasspy/piper/releases/download/2023.11.14-2/en_GB-jenny_dioco-medium.onnx
curl -L -O https://github.com/rhasspy/piper/releases/download/2023.11.14-2/en_GB-jenny_dioco-medium.onnx.json

cd ..
```

## 3. Configure .env

**Standard Setup:**
```env
TTS_ENGINE=piper
PIPER_VOICE=en_GB-alan-medium
PIPER_USE_GPU=true
```

**High-Quality with GPU:**
```env
TTS_ENGINE=piper
PIPER_VOICE=en_US-libritts-high
PIPER_USE_GPU=true
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

## GPU Setup (for faster synthesis with high-quality models)

**Requirements:**
- NVIDIA GPU (2GB+ VRAM)
- CUDA 11.8 or 12.x

**Installation:**
```powershell
# Install CUDA from: https://developer.nvidia.com/cuda-downloads
# Then install GPU runtime:
pip uninstall onnxruntime
pip install onnxruntime-gpu

# Verify GPU support:
python -c "import onnxruntime as ort; print(ort.get_available_providers())"
# Should show: ['CUDAExecutionProvider', ...]
```

**Performance with GPU:**
- Standard 25MB model: ~0.5s (2x faster)
- High-quality 50MB model: ~0.5-0.8s (2-4x faster than CPU)

See [GPU_SETUP_GUIDE.md](GPU_SETUP_GUIDE.md) for detailed GPU setup instructions.

## Troubleshooting

**Piper model not found?**
- Check files exist: `dir voices\en_GB-alan-medium.onnx*`
- Set explicit path: `PIPER_MODEL_PATH=./voices/en_GB-alan-medium.onnx`

**GPU not working?**
- Check CUDA: `nvidia-smi`
- Check providers: `python -c "import onnxruntime as ort; print(ort.get_available_providers())"`
- Install onnxruntime-gpu: `pip install onnxruntime-gpu`
- Disable GPU: `PIPER_USE_GPU=false` in .env

**Import error?**
- Install: `pip install piper-tts onnxruntime`

**No audio?**
- Check fallback is working: Set `TTS_ENGINE=pyttsx3` in .env
- Restart server: `python server.py`

## Voice Options

**Standard Quality (25-30MB):**
- `en_GB-alan-medium` - British butler (classic)
- `en_GB-southern_english_male-medium` - Upper-class British
- `en_US-ryan-medium` - American male

**High Quality (40-60MB) - Recommended with GPU:**
- `en_US-libritts-high` - Best overall quality ⭐
- `en_GB-jenny_dioco-medium` - British, very natural
- `en_US-ryan-high` - Deep male, authoritative

Download from: https://github.com/rhasspy/piper/releases/tag/2023.11.14-2

## Performance

**CPU (without GPU):**
- Standard model: ~1.0s per sentence
- High-quality model: ~2.0-3.0s per sentence

**GPU (with onnxruntime-gpu):**
- Standard model: ~0.5s per sentence (2x faster)
- High-quality model: ~0.5-0.8s per sentence (2-4x faster)

## Quick Reference

| Setup | Model | GPU | Synthesis Time | Quality |
|-------|-------|-----|----------------|---------|
| Basic | 25MB | No | ~1.0s | Good |
| Standard | 40MB | No | ~2.0s | Excellent |
| **Recommended** | **50MB** | **Yes** | **~0.6s** | **Outstanding** |

For complete GPU setup, see [GPU_SETUP_GUIDE.md](GPU_SETUP_GUIDE.md).
For full details, see [PIPER_INTEGRATION_GUIDE.md](PIPER_INTEGRATION_GUIDE.md).
