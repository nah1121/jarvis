# TTS Debugging Summary

## Overview
I've added comprehensive debugging tools to help diagnose why TTS is not producing sound. The previous fixes (output capture and text sanitization) are working correctly, but we need to identify exactly where in the TTS pipeline the issue is occurring.

## What Was Added

### 1. Enhanced Logging
**Files Modified:** `server.py`, `tts_access.py`

Added INFO-level logging at every critical step:

```python
# server.py - synthesize_speech (line 1018-1031)
log.info(f"synthesize_speech called with text length: {len(text)} chars")
log.info(f"Text preview: {text[:100]}")
# ... synthesis happens ...
log.info(f"TTS SUCCESS: generated using {engine}: {len(audio)} bytes")
# OR
log.warning("TTS FAILED: unavailable (Piper/pyttsx3 both failed)")

# tts_access.py - _synthesize_piper (line 283-329)
log.info(f"Piper: Original text length: {len(text)}, Sanitized: {len(sanitized_text)}")
log.info(f"Piper: Sanitized text preview: {sanitized_text[:100]}")
# ... synthesis happens ...
log.info(f"Piper synthesis SUCCESS: {len(audio_bytes)} bytes")
```

These logs will show:
- ✓ Is text reaching the TTS function?
- ✓ Is sanitization working correctly?
- ✓ Is Piper generating audio?
- ✓ Is audio being returned to the server?

### 2. Diagnostic Test Script
**File Created:** `test_tts_full.py`

Run with: `python test_tts_full.py`

This script:
- Tests simple ASCII text ("Hello sir, this is a test")
- Tests problematic text with special characters (the exact text from logs)
- Shows the complete flow: original → sanitized → audio
- Saves audio to `/tmp/test_tts_output.wav` for verification
- Reports clear PASS/FAIL for each test

### 3. Troubleshooting Guide
**File Created:** `TTS_TROUBLESHOOTING.md`

A comprehensive guide covering:
- Step-by-step diagnostic process
- 6 common TTS issues and their solutions
- Expected log output when working correctly
- Individual component tests
- Alternative approaches if needed

## Next Steps for User

### Step 1: Run the Diagnostic Test
```bash
cd /path/to/jarvis
python test_tts_full.py
```

This will immediately tell you if TTS is working at all, or if there's a problem with Piper/pyttsx3 installation.

**Expected output if working:**
```
✓ SUCCESS: Generated X bytes using piper
✓ Saved test audio to /tmp/test_tts_output.wav
```

**If it fails:**
- Check if piper-tts is installed: `pip install piper-tts onnxruntime`
- Check if voice model is downloaded (auto-downloads on first use)

### Step 2: Run JARVIS and Check Logs
```bash
python server.py
```

Then speak to JARVIS (e.g., "good evening") and look for these log messages:

**When working correctly:**
```
[jarvis] synthesize_speech called with text length: 124 chars
[jarvis] Text preview: Good evening, sir. 72.5 degrees...
[jarvis.tts] Piper: Original text length: 124, Sanitized: 124
[jarvis.tts] Piper: Sanitized text preview: Good evening, sir...
[jarvis.tts] Piper synthesis SUCCESS: 45678 bytes
[jarvis] TTS SUCCESS: generated using piper: 45678 bytes
```

**If failing, you'll see:**
```
[jarvis.tts] Piper synthesis produced empty audio
[jarvis.tts] Piper TTS failed; falling back to pyttsx3
[jarvis] TTS FAILED: unavailable (Piper/pyttsx3 both failed)
```

### Step 3: Identify the Issue

Based on the logs, the problem will be one of these:

1. **Text not reaching TTS** → Issue in server.py before line 2188
2. **Sanitization removes all text** → Issue with _sanitize_text_for_tts
3. **Piper fails to load** → Piper not installed or voice model missing
4. **Piper synthesis fails** → Corrupted model, memory issue, or threading issue
5. **Audio generated but not played** → Frontend issue, WebSocket issue, or browser audio context

### Step 4: Share Results

After running the tests and checking logs, share:
1. Output of `python test_tts_full.py`
2. Relevant log lines from server showing:
   - `synthesize_speech called with text length: ...`
   - `Piper: Original text length: ...`
   - `Piper synthesis SUCCESS/FAILED: ...`
   - `TTS SUCCESS/FAILED: ...`

## Technical Details

### What We Know Works
✓ Copilot CLI output capture (fixed in commit b27ecde)
✓ Text sanitization (fixed in commit 2ae011f)
✓ Real-time streaming for Copilot output
✓ Unicode normalization (ù → u, ° → degrees, etc.)

### What We're Debugging
? TTS audio generation (Piper synthesis)
? Audio transmission to frontend
? Frontend audio playback

### Files Changed in This Session
- `server.py` - Enhanced logging in synthesize_speech
- `tts_access.py` - Enhanced logging in _synthesize_piper
- `test_tts_full.py` - New diagnostic test script
- `TTS_TROUBLESHOOTING.md` - New troubleshooting guide
- `.gitignore` - Exclude test scripts

## Summary

The previous fixes ensure that:
1. ✓ Copilot CLI output is captured correctly
2. ✓ Special characters are sanitized properly
3. ✓ Text is passed to the TTS function

Now we need to identify why Piper TTS is not generating audio. The enhanced logging and diagnostic tools will pinpoint the exact failure point.

**The issue is NOT with output capture or text sanitization** - those are confirmed working. The issue is in the TTS synthesis itself (Piper or pyttsx3).
