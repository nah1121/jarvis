# Piper TTS with High-Quality Models and GPU Acceleration

## Overview

This guide shows you how to upgrade from the standard 25MB Piper models to high-quality models (50MB+) and enable NVIDIA GPU acceleration for faster synthesis.

## Benefits of High-Quality Models + GPU

**High-Quality Models:**
- Better naturalness and expressiveness
- More realistic intonation and prosody
- Clearer articulation
- Richer voice timbre

**GPU Acceleration:**
- 2-5x faster synthesis (especially for high-quality models)
- Lower CPU usage
- Better for real-time applications
- Smooth performance even with 50MB+ models

## Step 1: Install onnxruntime-gpu

### Prerequisites
- NVIDIA GPU (GTX 1050 or newer, 2GB+ VRAM)
- CUDA 11.x or 12.x installed
- Windows 11 (or Windows 10)

### Install CUDA (if not already installed)

**Option A: CUDA 12.x (Latest)**
```powershell
# Download from NVIDIA:
# https://developer.nvidia.com/cuda-downloads

# After installation, verify:
nvcc --version
nvidia-smi
```

**Option B: CUDA 11.8 (Stable, widely supported)**
```powershell
# Download from:
# https://developer.nvidia.com/cuda-11-8-0-download-archive

nvcc --version
```

### Install onnxruntime-gpu

```powershell
# Remove CPU version first (if installed)
pip uninstall onnxruntime

# Install GPU version
pip install onnxruntime-gpu

# Verify GPU support
python -c "import onnxruntime as ort; print(ort.get_available_providers())"
# Should show: ['CUDAExecutionProvider', 'CPUExecutionProvider', ...]
```

## Step 2: Download High-Quality Voice Models

### Recommended High-Quality Models

Visit: https://github.com/rhasspy/piper/releases/tag/2023.11.14-2

**Best for JARVIS (British Butler Style):**

1. **en_GB-jenny_dioco-medium** (~30MB)
   - British female, very natural
   - Excellent for formal assistant
   - Download: `en_GB-jenny_dioco-medium.onnx` + `.onnx.json`

2. **en_GB-northern_english_male-medium** (~25-30MB)
   - British male, professional tone
   - Good alternative to alan

**American High-Quality:**

1. **en_US-libritts-high** (~50-60MB) ⭐ **Best Quality**
   - Multi-speaker, excellent quality
   - Most natural-sounding option
   - Download: `en_US-libritts-high.onnx` + `.onnx.json`

2. **en_US-ryan-high** (~40-50MB)
   - Deep male voice (already default)
   - Great quality, authoritative tone

### Download Instructions

```powershell
cd voices

# Example: Download en_US-libritts-high (best quality)
curl -L -O https://github.com/rhasspy/piper/releases/download/2023.11.14-2/en_US-libritts-high.onnx
curl -L -O https://github.com/rhasspy/piper/releases/download/2023.11.14-2/en_US-libritts-high.onnx.json

# Or download British high-quality
curl -L -O https://github.com/rhasspy/piper/releases/download/2023.11.14-2/en_GB-jenny_dioco-medium.onnx
curl -L -O https://github.com/rhasspy/piper/releases/download/2023.11.14-2/en_GB-jenny_dioco-medium.onnx.json

cd ..
```

## Step 3: Configure for GPU + High-Quality Model

Edit `.env`:

```env
# Use Piper TTS
TTS_ENGINE=piper

# Set high-quality voice
PIPER_VOICE=en_US-libritts-high
# Or: PIPER_VOICE=en_GB-jenny_dioco-medium

# Enable GPU acceleration
PIPER_USE_GPU=true

# Optional: explicit model path
# PIPER_MODEL_PATH=./voices/en_US-libritts-high.onnx
```

## Step 4: Test GPU Acceleration

Run the test script:

```powershell
python test_tts.py
```

**Expected output with GPU:**
```
INFO: Loading Piper model with CUDA GPU acceleration
INFO: Piper voice loaded with GPU: ./voices/en_US-libritts-high.onnx
✅ Piper TTS Success!
   Engine used: piper
   Audio size: 67890 bytes
```

**If you see "Falling back to CPU":**
- Check CUDA installation: `nvidia-smi`
- Verify onnxruntime-gpu: `pip show onnxruntime-gpu`
- Check providers: `python -c "import onnxruntime as ort; print(ort.get_available_providers())"`

## Step 5: Start JARVIS

```powershell
python server.py
# In another terminal:
cd frontend && npm run dev
```

Open http://localhost:5173 and test voice commands.

## Performance Comparison

### Standard Medium Model (25MB) on CPU
- Synthesis time: ~1.0-1.5s
- CPU usage: 15-20%
- Quality: Good

### High-Quality Model (50MB) on CPU
- Synthesis time: ~2.0-3.0s
- CPU usage: 25-35%
- Quality: Excellent

### High-Quality Model (50MB) on GPU
- Synthesis time: ~0.5-0.8s ⚡ **2-4x faster**
- GPU usage: 10-20%
- CPU usage: 5-10%
- Quality: Excellent

## Troubleshooting

### GPU Not Detected

**Error:** "CUDA GPU not available"

**Solutions:**
1. Install CUDA Toolkit: https://developer.nvidia.com/cuda-downloads
2. Install onnxruntime-gpu: `pip install onnxruntime-gpu`
3. Check CUDA version compatibility:
   - onnxruntime-gpu 1.16+: Requires CUDA 11.8 or 12.x
   - Check compatibility: https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html

### Import Error

**Error:** "Cannot import onnxruntime"

**Solution:**
```powershell
pip uninstall onnxruntime onnxruntime-gpu
pip install onnxruntime-gpu
```

### Slow Synthesis Even with GPU

**Possible causes:**
1. Model not actually using GPU (check logs)
2. CUDA drivers outdated
3. Other GPU-intensive applications running

**Solutions:**
- Close other GPU apps (games, video editing, etc.)
- Update NVIDIA drivers: `nvidia-smi` → Check driver version
- Monitor GPU usage: Task Manager → Performance → GPU

### Out of Memory

**Error:** "CUDA out of memory"

**Solution:**
```env
# Force CPU mode if GPU has insufficient memory
PIPER_USE_GPU=false
```

Or close other GPU applications.

## Voice Model Quality Comparison

| Model | Size | Quality | Speed (CPU) | Speed (GPU) | Best For |
|-------|------|---------|-------------|-------------|----------|
| en_US-ryan-low | 10MB | Basic | Very fast | N/A | Testing |
| en_US-ryan-medium | 25MB | Good | Fast | Fast | General use |
| en_US-ryan-high | 40MB | Excellent | Medium | Very fast | High quality |
| en_US-libritts-high | 60MB | Outstanding | Slow | Fast | Best quality |
| en_GB-jenny_dioco-medium | 30MB | Excellent | Fast | Very fast | British, natural |

## Recommended Setup for Your GPU

**For 8GB VRAM (your system):**
- ✅ Use high-quality models (50-60MB)
- ✅ Enable GPU: `PIPER_USE_GPU=true`
- ✅ Recommended: `en_US-libritts-high` or `en_GB-jenny_dioco-medium`
- ⚡ Expect ~0.5-0.8s synthesis time (2-4x faster than CPU)

**For 4GB VRAM:**
- ✅ Use medium-high models (30-40MB)
- ✅ Enable GPU: `PIPER_USE_GPU=true`
- ⚠️ Monitor GPU memory usage

**For 2GB VRAM:**
- ⚠️ Stick with medium models (25MB)
- ✅ GPU still helps, but less dramatic improvement

## Advanced: Multiple Voice Models

Keep several models for different scenarios:

```powershell
cd voices
# Download multiple models
curl -L -O https://github.com/rhasspy/piper/releases/download/2023.11.14-2/en_US-libritts-high.onnx
curl -L -O https://github.com/rhasspy/piper/releases/download/2023.11.14-2/en_US-libritts-high.onnx.json

curl -L -O https://github.com/rhasspy/piper/releases/download/2023.11.14-2/en_GB-jenny_dioco-medium.onnx
curl -L -O https://github.com/rhasspy/piper/releases/download/2023.11.14-2/en_GB-jenny_dioco-medium.onnx.json
```

Switch in `.env`:
```env
# Use American high-quality
PIPER_VOICE=en_US-libritts-high

# Or British natural
# PIPER_VOICE=en_GB-jenny_dioco-medium
```

Restart server to apply changes.

## Summary

✅ **You've upgraded to:**
- High-quality voice models (50MB+)
- GPU acceleration (2-4x faster)
- Professional-grade audio quality
- Smooth real-time performance

**Next steps:**
1. Download your preferred high-quality model
2. Install onnxruntime-gpu
3. Set `PIPER_USE_GPU=true` in .env
4. Test with `python test_tts.py`
5. Enjoy faster, better-quality TTS!

For more info, see:
- [SETUP_WINDOWS.md](SETUP_WINDOWS.md) - General setup
- [PIPER_INTEGRATION_GUIDE.md](PIPER_INTEGRATION_GUIDE.md) - Implementation details
