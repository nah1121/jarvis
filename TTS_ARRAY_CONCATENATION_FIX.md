# TTS Array Concatenation Fix

## Problem
Both Piper TTS and pyttsx3 engines were failing to produce audible sound:

1. **Piper TTS Error:**
   ```
   ValueError: zero-dimensional arrays cannot be concatenated
   File "tts_access.py", line 331, in _render
       audio_data = np.concatenate(audio_chunks)
   ```
   - Piper collected 1 audio chunk but failed during concatenation
   - Error indicates the audio chunks are 0-dimensional numpy scalars, not 1D arrays

2. **pyttsx3 Fallback Issue:**
   - Logs showed `Imported existing` from comtypes and then stopped
   - No clear error, but no sound was produced
   - Likely hanging or slow, with no visibility into progress

## Root Causes

### Piper TTS
The `voice_obj.synthesize()` generator can yield either:
- **1D numpy arrays** containing multiple audio samples (typical for longer text)
- **0D numpy scalars** containing single audio samples (typical for very short text like "Good evening, sir.")

The previous code assumed all chunks would be 1D arrays and used `np.concatenate()` directly, which fails on 0D scalars:
```python
audio_data = np.concatenate(audio_chunks)  # FAILS if chunks are 0D
```

### pyttsx3
The fallback engine lacked detailed logging, making it impossible to diagnose where it was hanging or failing. The user couldn't tell if the issue was:
- Engine initialization
- `runAndWait()` hanging (known issue in async contexts)
- File I/O problems
- Audio generation failure

## Solutions

### 1. Piper TTS: Handle 0D Arrays with `np.atleast_1d()`

**Changed from:**
```python
audio_data = np.concatenate(audio_chunks)
```

**To:**
```python
# Handle both 1D arrays and 0D scalars by ensuring all chunks are at least 1D
if len(audio_chunks) == 1:
    # Single chunk - ensure it's at least 1D
    audio_data = np.atleast_1d(audio_chunks[0])
else:
    # Multiple chunks - ensure each is 1D before concatenating
    audio_data = np.concatenate([np.atleast_1d(chunk) for chunk in audio_chunks])
```

**How `np.atleast_1d()` works:**
- 0D scalar (value `42`) → 1D array `[42]`
- 1D array `[1, 2, 3]` → unchanged `[1, 2, 3]`
- 2D+ arrays → unchanged

This ensures `np.concatenate()` always receives 1D or higher-dimensional arrays.

### 2. Enhanced Piper Logging

Added detailed logging to diagnose issues:

```python
# Log first chunk details
log.info(f"Piper: First chunk type={type(first_chunk)}, shape={getattr(first_chunk, 'shape', 'no shape')}, dtype={getattr(first_chunk, 'dtype', 'no dtype')}")

# Log concatenated result
log.info(f"Piper: Concatenated audio_data shape={audio_data.shape}, dtype={audio_data.dtype}, size={audio_data.size}")

# Validate audio data
if audio_data.size == 0:
    log.warning("Piper synthesis produced empty audio data array")
    return None
```

**Example output:**
```
Piper: First chunk type=<class 'numpy.ndarray'>, shape=(0,), dtype=float32
Piper: Concatenated audio_data shape=(48000,), dtype=float32, size=48000
```

### 3. Enhanced pyttsx3 Logging

Added step-by-step logging to trace execution:

```python
log.info("pyttsx3: Creating fresh engine...")
log.info("pyttsx3: Setting rate...")
log.info(f"pyttsx3: Setting voice to {PYTTSX3_VOICE}...")
log.info("pyttsx3: Creating temp file...")
log.info(f"pyttsx3: Saving to temp file {tmp_path}...")
log.info("pyttsx3: Running engine (this may take a moment)...")
log.info("pyttsx3: Engine completed, reading audio bytes...")
log.info(f"pyttsx3: Read {len(audio_bytes)} bytes from temp file")
log.info("pyttsx3: Cleaned up temp file")
log.info("pyttsx3: Engine stopped")
```

**Benefits:**
- See exactly where pyttsx3 hangs or fails
- Know when `runAndWait()` completes (often slow on Windows)
- Confirm audio bytes are actually read from temp file
- Verify cleanup happens correctly

## Technical Details

### NumPy Array Dimensionality
- **0D (scalar)**: `np.array(42)` → shape `()`
- **1D (vector)**: `np.array([1, 2, 3])` → shape `(3,)`
- **2D (matrix)**: `np.array([[1, 2], [3, 4]])` → shape `(2, 2)`

### Piper Audio Format
- **Type**: numpy.ndarray
- **dtype**: float32 (audio samples normalized to -1.0 to 1.0)
- **Shape**: Usually 1D `(N,)` but can be 0D `()` for very short text
- **Sample Rate**: 22050 Hz
- **Channels**: Mono (1)

### WAV Conversion Process
1. Collect chunks from Piper generator
2. Ensure all chunks are at least 1D with `np.atleast_1d()`
3. Concatenate into single 1D array
4. Validate `audio_data.size > 0`
5. Convert float32 to int16: `(audio_data * 32767).astype(np.int16)`
6. Write to WAV file with proper headers (22050 Hz, mono, 16-bit PCM)

## Files Changed
- `tts_access.py` - `_synthesize_piper()` function (lines 328-349)
- `tts_access.py` - `_synthesize_pyttsx3()` function (lines 446-503)

## Testing

### Expected Success Logs for Piper:
```
[jarvis.tts] Piper: Starting synthesis for text: Good evening, sir....
[jarvis.tts] Piper: Collected 1 audio chunks
[jarvis.tts] Piper: First chunk type=<class 'numpy.ndarray'>, shape=(48000,), dtype=float32
[jarvis.tts] Piper: Concatenated audio_data shape=(48000,), dtype=float32, size=48000
[jarvis.tts] Piper: Created WAV file with 96044 bytes
[jarvis.tts] Piper synthesis SUCCESS: 96044 bytes
```

### Expected Success Logs for pyttsx3:
```
[jarvis.tts] Piper TTS failed; falling back to pyttsx3
[jarvis.tts] pyttsx3: Creating fresh engine...
[jarvis.tts] pyttsx3: Setting rate...
[jarvis.tts] pyttsx3: Creating temp file...
[jarvis.tts] pyttsx3: Saving to temp file C:\Users\...\tmpXXXX.wav...
[jarvis.tts] pyttsx3: Running engine (this may take a moment)...
[jarvis.tts] pyttsx3: Engine completed, reading audio bytes...
[jarvis.tts] pyttsx3: Read 45678 bytes from temp file
[jarvis.tts] pyttsx3: Cleaned up temp file
[jarvis.tts] pyttsx3: Engine stopped
[jarvis.tts] pyttsx3 synthesis SUCCESS: 45678 bytes
```

## User Instructions

1. Restart JARVIS server:
   ```bash
   python server.py
   ```

2. Speak to JARVIS and check the console logs

3. **If Piper works**, you should see:
   - No concatenation error
   - Chunk shape logged (might be 0D or 1D)
   - Audio data size > 0
   - WAV file created with bytes
   - **HEAR SOUND** through speakers

4. **If Piper fails and pyttsx3 takes over**, you should see:
   - Detailed step-by-step progress logs
   - Engine completion message
   - Audio bytes read from temp file
   - **HEAR SOUND** through speakers

5. **If still no sound**, check:
   - Frontend WebSocket connection (should see `Voice WebSocket connected`)
   - Browser audio context (might need user interaction to enable)
   - System volume and audio output device
   - Browser console for JavaScript errors

## Prevention

This fix handles the variability in Piper's output format and provides comprehensive logging for both TTS engines, making future debugging much easier.
