# Logging HTML Escape Fix

## Problem

The Piper TTS logs were being cut off when displaying chunk type information:

```
2026-03-31 21:49:34,466 [jarvis.tts] Piper: First chunk type=
```

The log line was incomplete and stopped right after `type=`.

## Root Cause

The logging statement was using `type(first_chunk)` directly in the f-string:

```python
log.info(f"Piper: First chunk type={type(first_chunk)}, shape={...}, dtype={...}")
```

This produces output like:
```
Piper: First chunk type=<class 'numpy.ndarray'>, shape=(48000,), dtype=float32
```

The angle brackets `<` and `>` in `<class 'numpy.ndarray'>` were being interpreted as HTML entities in the console output, causing the log message to be truncated or escaped as `&lt;` and `&gt;`.

Evidence from the logs shows HTML escaping was occurring:
```
[FRONTEND] &gt; jarvis-frontend@0.1.0 dev &gt; vite
```

The `&gt;` indicates that the console or logging output is being HTML-escaped.

## Solution

Changed the logging to use `type(first_chunk).__name__` instead of `type(first_chunk)`:

```python
chunk_type = type(first_chunk).__name__
chunk_shape = getattr(first_chunk, 'shape', 'no shape')
chunk_dtype = getattr(first_chunk, 'dtype', 'no dtype')
log.info(f"Piper: First chunk type={chunk_type}, shape={chunk_shape}, dtype={chunk_dtype}")
```

This produces output without angle brackets:
```
Piper: First chunk type=ndarray, shape=(48000,), dtype=float32
```

### Benefits

1. **No HTML escaping issues**: Output contains no `<` or `>` characters
2. **More readable**: Just the class name instead of full representation
3. **Consistent**: Works across different console/logging contexts
4. **Debuggable**: Still provides all necessary type information

## Technical Details

### Python Type Representation

- `type(obj)` returns the type object (e.g., `<class 'numpy.ndarray'>`)
- `type(obj).__name__` returns just the class name string (e.g., `'ndarray'`)
- `type(obj).__module__` returns the module name (e.g., `'numpy'`)

### HTML Entity Escaping

When console output is captured or displayed in HTML contexts, special characters are escaped:
- `<` becomes `&lt;`
- `>` becomes `&gt;`
- `&` becomes `&amp;`

This can cause log messages with type representations to be truncated or garbled.

## Files Changed

- `tts_access.py` - Line 331-334: Changed chunk type logging to use `__name__`

## Expected Output After Fix

Before:
```
Piper: First chunk type=
```
(truncated)

After:
```
Piper: First chunk type=ndarray, shape=(48000,), dtype=float32
Piper: Concatenated audio_data shape=(48000,), dtype=float32, size=48000
Piper: Created WAV file with 96044 bytes
Piper synthesis SUCCESS: 96044 bytes
```
(complete with all information)

## Testing

User should restart JARVIS server and observe complete log messages:

```bash
python server.py
```

The logs should now show the complete chunk type information without truncation.
