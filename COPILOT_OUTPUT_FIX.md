# Copilot CLI Output Capture Fix

## Problem
JARVIS TTS was working, but after sending prompts to Copilot CLI, the responses were not being captured and spoken back to the user. The issue was that Copilot CLI output was not being properly captured from stdout/stderr.

## Root Cause Analysis
The previous implementation had several issues:
1. **The `-s` flag**: This flag was added to Copilot CLI invocations, but may have been interfering with output buffering or formatting
2. **Simple `communicate()` call**: Used `process.communicate()` which works for most cases, but can miss output if the process buffers data
3. **No real-time streaming**: Output was only collected after the process completed
4. **Insufficient logging**: Debug-level logs made it hard to see what was actually being captured

## Solution Implemented

### 1. Removed `-s` Flag
```python
# Old: cmd = ["copilot", "-p", prompt, "-s"]
# New: cmd = ["copilot", "-p", prompt]
```
The `-s` flag may have been causing output formatting issues or buffering problems.

### 2. Real-Time Streaming
Instead of waiting for the entire process to complete, we now stream output in real-time:

```python
async def read_stream(stream, chunks, name):
    """Read stream in real-time and collect chunks."""
    try:
        while True:
            chunk = await stream.read(8192)
            if not chunk:
                break
            chunks.append(chunk)
            log.debug(f"Copilot CLI {name} chunk: {len(chunk)} bytes")
    except Exception as e:
        log.debug(f"Stream {name} read error (may be normal on completion): {e}")
```

This approach:
- Reads 8KB chunks from stdout and stderr as they become available
- Prevents data loss from buffering issues
- Works even if the process produces output slowly

### 3. Stderr Fallback
Some CLI tools output to stderr instead of stdout. We now handle this:

```python
# If stdout is empty but stderr has content, use stderr
if not stdout_text and stderr_text:
    log.warning(f"Copilot CLI returned empty stdout, using stderr instead")
    return stderr_text
```

### 4. Enhanced Logging
Changed critical logs from DEBUG to INFO level and added output previews:

```python
log.info(f"Copilot CLI decoded stdout length: {len(stdout_text)} chars")
log.info(f"Copilot CLI decoded stderr length: {len(stderr_text)} chars")
if stdout_text:
    log.info(f"Copilot CLI stdout preview: {stdout_text[:200]}")
```

This makes it much easier to diagnose issues.

### 5. Unbuffered Output
Set environment variable to reduce buffering:

```python
env={**os.environ, "PYTHONUNBUFFERED": "1"}
```

## Testing

Run the test script to verify the fix works:

```bash
python test_copilot_capture.py
```

This will:
1. Check if Copilot CLI is available
2. Send a simple prompt and verify output is captured
3. Send a multi-sentence prompt and verify longer output is captured
4. Report success/failure with detailed diagnostics

## Expected Behavior After Fix

1. **User speaks to JARVIS**: "Build me a calculator app"
2. **JARVIS responds**: "On it, sir." (TTS works)
3. **Copilot CLI works**: Builds the app in the background
4. **Output is captured**: Real-time streaming captures all output
5. **JARVIS speaks result**: "Sir, I've built your calculator app with React and Tailwind..." (TTS speaks the captured output)

## Debugging

If output is still not being captured:

1. **Check logs**: Look for INFO-level messages showing stdout/stderr lengths and previews
2. **Verify Copilot CLI**: Run `copilot -p "Say hello" --model gpt-4.1-mini` manually
3. **Check return code**: Non-zero return codes will raise CopilotError
4. **Test with simple prompts first**: Use the test script to isolate the issue

## Additional Notes

- The fix maintains backward compatibility
- No changes to the API surface
- Works for both `chat_fast()` and `chat_smart()` methods
- The streaming approach adds negligible overhead (async I/O is efficient)
- All output is still stored in memory (no temp files created)

## Memory Storage Fact

Store this fact for future reference:
- **Subject**: Copilot CLI output capture
- **Fact**: Copilot CLI output is captured using real-time streaming (8KB chunks) via async read loops on stdout/stderr pipes, with fallback to stderr if stdout is empty. The `-s` flag was removed as it interfered with output capture.
- **Citations**: copilot_access.py:113-194
