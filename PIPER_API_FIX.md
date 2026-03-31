# Piper TTS API Fix - Correct Generator Usage

## Problem
Piper TTS was crashing with:
```
AttributeError: '_io.BytesIO' object has no attribute 'speaker_id'
File "tts_access.py", line 314, in _render
    for audio_chunk in voice_obj.synthesize(sanitized_text, audio_stream):
```

## Root Cause
The Piper API was being used incorrectly. The `voice_obj.synthesize()` method:
- **Correct signature**: `synthesize(text)` - takes only text parameter
- **Returns**: Generator that yields numpy audio arrays (float32)
- **Does NOT**: Write directly to a stream (that was a misunderstanding of the API)

The previous code attempted to pass a `BytesIO` stream as the second parameter, which caused Piper to think it was a speaker_id parameter.

## Solution
Changed from incorrect streaming approach to correct manual WAV construction:

### Before (Broken):
```python
audio_stream = io.BytesIO()
for audio_chunk in voice_obj.synthesize(sanitized_text, audio_stream):
    pass  # Stream was supposed to be filled automatically
audio_bytes = audio_stream.getvalue()  # Always returned 0 bytes
```

### After (Fixed):
```python
# 1. Collect audio chunks from generator
audio_chunks = []
for audio_chunk in voice_obj.synthesize(sanitized_text):  # Only text parameter
    audio_chunks.append(audio_chunk)

# 2. Concatenate numpy arrays
import wave
import numpy as np
audio_data = np.concatenate(audio_chunks)

# 3. Manually create WAV file
audio_stream = io.BytesIO()
with wave.open(audio_stream, 'wb') as wav_file:
    wav_file.setnchannels(1)  # Mono
    wav_file.setsampwidth(2)   # 16-bit
    wav_file.setframerate(22050)  # Sample rate

    # Convert float32 to int16
    audio_int16 = (audio_data * 32767).astype(np.int16)
    wav_file.writeframes(audio_int16.tobytes())

audio_bytes = audio_stream.getvalue()
```

## Technical Details

### Piper Output Format
- Returns generator yielding numpy arrays
- Audio data type: `float32` (values range -1.0 to 1.0)
- Must be converted to `int16` for WAV format (values range -32768 to 32767)
- Default sample rate: 22050 Hz
- Mono audio (1 channel)

### WAV File Construction
The `wave` module requires:
- `setnchannels(1)` - mono audio
- `setsampwidth(2)` - 2 bytes = 16-bit
- `setframerate(22050)` - sample rate in Hz
- Audio data as `int16` bytes

### Conversion Formula
```python
audio_int16 = (audio_data * 32767).astype(np.int16)
```
This converts float32 range [-1.0, 1.0] to int16 range [-32768, 32767]

## Files Changed
- `tts_access.py` - `_synthesize_piper()` function (lines 305-357)

## Testing
User should test by:
1. Restart JARVIS server: `python server.py`
2. Speak to JARVIS
3. Check logs for:
   - "Piper: Starting synthesis for text: ..."
   - "Piper: Collected N audio chunks"
   - "Piper: Created WAV file with X bytes"
   - "Piper synthesis SUCCESS: X bytes"

## Expected Behavior
- No more AttributeError
- Logs show successful audio generation with byte count
- User hears JARVIS speak responses through Piper TTS

## Fallback
If Piper still fails, pyttsx3 automatically takes over (Windows SAPI5 voices).
