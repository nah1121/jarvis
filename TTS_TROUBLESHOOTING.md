# TTS Troubleshooting Guide

## Problem
User reports "still not fixed" - TTS is not producing sound after Copilot CLI responses.

## Previous Fixes Applied
1. ✓ Improved Copilot CLI output capture with real-time streaming
2. ✓ Added text sanitization to handle special characters (ù, °, —, etc.)
3. ✓ Added comprehensive logging

## Diagnostic Steps

### Step 1: Run the Diagnostic Test
```bash
python test_tts_full.py
```

This will test:
- Simple ASCII text synthesis
- Complex text with special characters
- Full sanitization → synthesis flow
- Save audio to `/tmp/test_tts_output.wav` for verification

### Step 2: Check Server Logs
Look for these key log messages when you interact with JARVIS:

#### When text is being processed:
```
synthesize_speech called with text length: X chars
Text preview: ...
```
**What to check:** Is the text reaching the TTS function?

#### When Piper processes text:
```
Piper: Original text length: X, Sanitized: Y
Piper: Sanitized text preview: ...
```
**What to check:** Is sanitization removing too much text?

#### When synthesis succeeds:
```
Piper synthesis SUCCESS: X bytes
TTS SUCCESS: generated using piper: X bytes
```
**What to check:** Is audio being generated?

#### When synthesis fails:
```
Piper synthesis produced empty audio
TTS FAILED: unavailable (Piper/pyttsx3 both failed)
```
**What to check:** Why is Piper failing?

### Step 3: Common Issues and Solutions

#### Issue 1: Text Not Reaching TTS
**Symptoms:**
- No "synthesize_speech called" log message
- Response text is displayed but not spoken

**Possible causes:**
- Response is empty or None
- Exception before TTS call
- WebSocket disconnected

**Solution:**
Check for exceptions in the logs around line 2188-2196 in server.py

#### Issue 2: Sanitization Removes All Text
**Symptoms:**
```
Text became empty after sanitization
```

**Possible causes:**
- Text contains only non-ASCII characters
- Text is too short after sanitization

**Solution:**
Check the sanitized text preview. If it's empty, we may need to be less aggressive with sanitization.

#### Issue 3: Piper TTS Not Installed
**Symptoms:**
```
piper-tts not installed
```

**Solution:**
```bash
pip install piper-tts onnxruntime
```

#### Issue 4: Piper Voice Model Missing
**Symptoms:**
```
Piper model unavailable
```

**Solution:**
- Model should auto-download on first use
- Or manually download from https://github.com/rhasspy/piper/releases
- Place in `./voices/` directory
- Or set `PIPER_MODEL_PATH` in .env

#### Issue 5: Piper Synthesis Fails Silently
**Symptoms:**
```
Piper synthesis produced empty audio
```

**Possible causes:**
- Corrupted voice model
- Incompatible onnxruntime version
- Memory issues
- Threading issues

**Solution:**
1. Try pyttsx3 fallback:
   ```bash
   # In .env file:
   TTS_ENGINE=pyttsx3
   ```

2. Reinstall Piper:
   ```bash
   pip uninstall piper-tts onnxruntime
   pip install piper-tts onnxruntime
   ```

3. Check available disk space and memory

#### Issue 6: Audio Generated But Not Played
**Symptoms:**
- Logs show "TTS SUCCESS: generated using X"
- No sound from speakers

**Possible causes:**
- Frontend audio player issue
- WebSocket not sending audio data
- Browser audio context not initialized

**Solution:**
1. Check browser console for errors
2. Verify WebSocket connection is open
3. Check that user has clicked to enable audio
4. Verify audio data is being sent:
   ```
   await ws.send_json({"type": "audio", "data": base64.b64encode(audio).decode(), ...})
   ```

### Step 4: Test Individual Components

#### Test Copilot CLI Output Capture:
```bash
python test_copilot_capture.py
```

#### Test Text Sanitization:
```bash
python test_tts_sanitization.py
```

#### Test Full TTS Flow:
```bash
python test_tts_full.py
```

#### Test Piper Directly:
```python
from piper import PiperVoice
import io

voice = PiperVoice.load("./voices/en_US-ryan-high.onnx")
audio_stream = io.BytesIO()
voice.synthesize("Hello world", audio_stream)
audio_bytes = audio_stream.getvalue()
print(f"Generated {len(audio_bytes)} bytes")
```

## Enhanced Logging Added

### In server.py (line 1018-1031):
- Shows text length and preview before TTS
- Shows clear SUCCESS/FAILED messages
- Uses INFO level (always visible)

### In tts_access.py (line 283-329):
- Shows original vs sanitized text
- Shows sanitized text preview
- Shows SUCCESS when audio is generated
- Uses INFO level for critical steps

## Next Steps for User

1. **Run the server** with these new logs
2. **Try speaking to JARVIS** with a simple phrase like "good evening"
3. **Look at the console logs** and identify which step is failing:
   - [ ] Is text reaching synthesize_speech?
   - [ ] Is sanitization working?
   - [ ] Is Piper generating audio?
   - [ ] Is audio being sent to frontend?

4. **Share the relevant log lines** showing:
   ```
   synthesize_speech called with text length: ...
   Piper: Original text length: ...
   Piper synthesis SUCCESS/FAILED: ...
   TTS SUCCESS/FAILED: ...
   ```

5. **Run diagnostic test**:
   ```bash
   python test_tts_full.py
   ```

This will definitively show if TTS is working at all, or if there's a deeper issue with Piper/pyttsx3 installation.

## Expected Working Flow

When everything works correctly, logs should show:
```
[jarvis.copilot] Copilot CLI final response length: 124 chars
[jarvis] synthesize_speech called with text length: 124 chars
[jarvis] Text preview: Good evening, sir. 72.5 degrees and calm...
[jarvis.tts] Piper: Original text length: 124, Sanitized: 124
[jarvis.tts] Piper: Sanitized text preview: Good evening, sir. 72.5 degrees and calm...
[jarvis.tts] Piper synthesis SUCCESS: 45678 bytes
[jarvis] TTS SUCCESS: generated using piper: 45678 bytes
[jarvis] JARVIS: Good evening, sir. 72.5 degrees and calm...
```

## Alternative: Direct Output Capture

If the current approach still doesn't work, we can try a completely different approach:

### Option A: Capture and Store Output Explicitly
Instead of relying on the current flow, we could:
1. Store Copilot output in a variable immediately after capture
2. Log it explicitly
3. Pass it directly to TTS without any intermediate steps

### Option B: Use Shell Redirection
```python
# Redirect output to a file
process = await asyncio.create_subprocess_shell(
    f'copilot -p "{prompt}" > /tmp/copilot_output.txt 2>&1',
    ...
)
# Read from file
output = Path('/tmp/copilot_output.txt').read_text()
```

But the current approach should work. Let's see what the logs show first.
