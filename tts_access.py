import asyncio
import io
import logging
import os
import tempfile
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional, Tuple

log = logging.getLogger("jarvis.tts")

# TTS switched to Piper for 8GB VRAM Windows 11 - Kokoro failed to install
# Piper supports high-quality models with GPU acceleration for faster synthesis
# pyttsx3 (Windows SAPI5) used as simple offline fallback if Piper fails

DEFAULT_ENGINE = os.getenv("TTS_ENGINE", "piper").lower()
PIPER_VOICE = os.getenv("PIPER_VOICE", "en_US-ryan-high")
PIPER_MODEL_PATH = os.getenv("PIPER_MODEL_PATH", "")  # Auto-downloads to ./voices/ if empty
PIPER_USE_GPU = os.getenv("PIPER_USE_GPU", "false").lower() in ("true", "1", "yes")
PYTTSX3_VOICE = os.getenv("PYTTSX3_VOICE", "")  # Empty = default Windows voice
PYTTSX3_RATE = int(os.getenv("PYTTSX3_RATE", "180"))  # Words per minute

_piper_voice = None
_piper_lock = asyncio.Lock()
_pyttsx3_engine = None
_pyttsx3_lock = asyncio.Lock()

# Dedicated single-thread executors to guarantee thread affinity:
#   Piper  – prevents concurrent onnxruntime synthesis calls on the shared voice object.
#   pyttsx3 – keeps Windows SAPI5 COM objects on the thread that created them; a pool
#             with more than one worker would allow concurrent calls to COM, which is
#             unsafe on Windows.
_piper_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="piper-tts")
_pyttsx3_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="pyttsx3-tts")

# HuggingFace base URL for official Piper voice models
_PIPER_HF_BASE = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"
)


def _download_piper_model(voice_name: str, voices_dir: Path) -> Optional[str]:
    """Download a Piper voice model from HuggingFace if not already present.

    Voice name format: ``{locale}-{speaker}-{quality}``
    e.g. ``en_US-ryan-high``, ``en_GB-alan-medium``

    Downloads both the ``.onnx`` model and its ``.onnx.json`` config to
    *voices_dir*, creating the directory if necessary.

    Returns the path to the downloaded ``.onnx`` file, or ``None`` on failure.
    """
    parts = voice_name.rsplit("-", 1)  # split off quality suffix
    if len(parts) != 2:
        log.warning(
            "Cannot parse voice name %r for auto-download "
            "(expected format: locale-speaker-quality, e.g. en_US-ryan-high)",
            voice_name,
        )
        return None

    locale_speaker, quality = parts  # e.g. "en_US-ryan", "high"
    locale_parts = locale_speaker.split("-", 1)
    if len(locale_parts) != 2:
        log.warning("Cannot parse locale/speaker from %r", locale_speaker)
        return None

    locale, speaker = locale_parts  # e.g. "en_US", "ryan"
    lang = locale.split("_")[0].lower()  # e.g. "en"

    # Construct URL path:
    # {lang}/{locale}/{speaker}/{quality}/{voice_name}.onnx
    rel = f"{lang}/{locale}/{speaker}/{quality}/{voice_name}"
    onnx_url = f"{_PIPER_HF_BASE}/{rel}.onnx"
    json_url = f"{_PIPER_HF_BASE}/{rel}.onnx.json"

    voices_dir.mkdir(parents=True, exist_ok=True)
    onnx_path = voices_dir / f"{voice_name}.onnx"
    json_path = voices_dir / f"{voice_name}.onnx.json"

    if onnx_path.exists() and json_path.exists():
        log.info("Piper model already cached at %s", onnx_path)
        return str(onnx_path)

    log.info(
        "Auto-downloading Piper voice %r from HuggingFace (~25-60 MB)...",
        voice_name,
    )
    for url, dest in [(onnx_url, onnx_path), (json_url, json_path)]:
        if dest.exists():
            continue
        try:
            log.info("  Downloading %s -> %s", url, dest)
            urllib.request.urlretrieve(url, dest)  # noqa: S310 - URL is known-safe constant
        except (urllib.error.URLError, OSError) as exc:
            log.warning("Failed to download %s: %s", url, exc)
            # Remove any partial file so a future attempt can retry cleanly
            try:
                dest.unlink(missing_ok=True)
            except OSError:
                pass
            return None

    log.info("Piper voice %r downloaded to %s", voice_name, onnx_path)
    return str(onnx_path)


async def synthesize(
    text: str, preferred_engine: Optional[str] = None, voice: Optional[str] = None
) -> Tuple[Optional[bytes], str]:
    """Generate audio bytes and return (audio, engine_used).

    Args:
        text: Text to convert to speech
        preferred_engine: "piper" or "pyttsx3" (default from env)
        voice: Currently unused; reserved for future per-call voice selection.

    Returns:
        Tuple of (audio_bytes, engine_name) or (None, engine_name) on failure
    """
    engine = (preferred_engine or DEFAULT_ENGINE or "piper").lower()

    if engine == "piper":
        audio = await _synthesize_piper(text, voice)
        if audio:
            return audio, "piper"
        log.warning("Piper TTS failed; falling back to pyttsx3")
        audio = await _synthesize_pyttsx3(text, voice)
        return (audio, "pyttsx3") if audio else (None, "piper")

    # Default to pyttsx3 first
    audio = await _synthesize_pyttsx3(text, voice)
    if audio:
        return audio, "pyttsx3"
    log.warning("pyttsx3 TTS failed; trying Piper as fallback")
    audio = await _synthesize_piper(text, voice)
    return (audio, "piper") if audio else (None, engine)


async def _ensure_piper_voice():
    """Initialize Piper voice model (lazy loading with thread safety)."""
    global _piper_voice
    if _piper_voice is not None:
        return _piper_voice

    async with _piper_lock:
        if _piper_voice is not None:
            return _piper_voice

        loop = asyncio.get_event_loop()

        def _load_voice():
            try:
                from piper import PiperVoice
            except ImportError:
                log.warning(
                    "piper-tts not installed. Run `pip install piper-tts` "
                    "and download a voice model."
                )
                return None

            # Determine model path
            model_path = PIPER_MODEL_PATH
            if not model_path:
                # Try to auto-locate in common paths
                voice_name = PIPER_VOICE or "en_US-ryan-high"
                possible_paths = [
                    Path.home() / ".local/share/piper/voices" / f"{voice_name}.onnx",
                    Path("voices") / f"{voice_name}.onnx",
                    Path("piper_voices") / f"{voice_name}.onnx",
                ]
                for p in possible_paths:
                    if p.exists():
                        model_path = str(p)
                        log.info(f"Found Piper model at {model_path}")
                        break

                if not model_path:
                    # Auto-download from HuggingFace
                    log.info(
                        "Piper model not found locally; attempting auto-download for %r",
                        voice_name,
                    )
                    voices_dir = Path("voices")
                    model_path = _download_piper_model(voice_name, voices_dir)

                if not model_path:
                    log.warning(
                        "Piper model unavailable. Set PIPER_MODEL_PATH, place "
                        "%s.onnx in ./voices/, or ensure internet access for "
                        "auto-download from HuggingFace.",
                        voice_name,
                    )
                    return None

            try:
                # Configure GPU acceleration if enabled
                if PIPER_USE_GPU:
                    try:
                        import onnxruntime as ort
                        providers = ort.get_available_providers()

                        if 'CUDAExecutionProvider' in providers:
                            log.info("Loading Piper model with CUDA GPU acceleration")
                            voice = PiperVoice.load(
                                model_path,
                                use_cuda=True
                            )
                            log.info(f"Piper voice loaded with GPU: {model_path}")
                            return voice
                        else:
                            log.warning(
                                "CUDA GPU not available. Install onnxruntime-gpu for GPU support. "
                                "Falling back to CPU."
                            )
                    except Exception as gpu_error:
                        log.warning(f"GPU initialization failed: {gpu_error}. Using CPU.")

                # Fall back to CPU
                voice = PiperVoice.load(model_path)
                log.info(f"Piper voice loaded (CPU): {model_path}")
                return voice
            except Exception as e:
                log.warning(f"Failed to load Piper voice from {model_path}: {e}")
                return None

        try:
            _piper_voice = await loop.run_in_executor(_piper_executor, _load_voice)
        except Exception as e:
            log.warning(f"Piper voice initialization failed: {e}")
            _piper_voice = None

        return _piper_voice


async def _synthesize_piper(text: str, voice: Optional[str]) -> Optional[bytes]:
    """Generate speech using Piper TTS (local, neural-quality, CPU-friendly)."""
    try:
        voice_obj = await _ensure_piper_voice()
    except Exception as e:
        log.warning(f"Piper voice loading error: {e}")
        return None

    if voice_obj is None:
        return None

    loop = asyncio.get_event_loop()

    def _render():
        try:
            # Synthesize to WAV bytes
            audio_stream = io.BytesIO()
            voice_obj.synthesize(text, audio_stream)
            audio_stream.seek(0)
            audio_bytes = audio_stream.read()

            # Check if synthesis produced empty audio
            if not audio_bytes:
                log.warning("Piper synthesis produced empty audio")
                return None

            return audio_bytes
        except Exception as e:
            log.warning(f"Piper synthesis error: {e}", exc_info=True)
            return None

    try:
        result = await loop.run_in_executor(_piper_executor, _render)
        return result
    except Exception as e:
        log.warning(f"Piper execution error: {e}", exc_info=True)
        return None


async def _ensure_pyttsx3_engine():
    """Initialize pyttsx3 engine (lazy loading with thread safety)."""
    global _pyttsx3_engine
    if _pyttsx3_engine is not None:
        return _pyttsx3_engine

    async with _pyttsx3_lock:
        if _pyttsx3_engine is not None:
            return _pyttsx3_engine

        loop = asyncio.get_event_loop()

        def _init_engine():
            try:
                import pyttsx3
            except ImportError:
                log.warning("pyttsx3 not installed. Run `pip install pyttsx3`.")
                return None

            try:
                engine = pyttsx3.init()
                engine.setProperty("rate", PYTTSX3_RATE)

                # Set voice if specified
                if PYTTSX3_VOICE:
                    voices = engine.getProperty("voices")
                    for v in voices:
                        if PYTTSX3_VOICE.lower() in v.name.lower() or PYTTSX3_VOICE in v.id:
                            engine.setProperty("voice", v.id)
                            log.info(f"pyttsx3 voice set to: {v.name}")
                            break

                log.info("pyttsx3 engine initialized")
                return engine
            except Exception as e:
                log.warning(f"pyttsx3 initialization failed: {e}")
                return None

        try:
            _pyttsx3_engine = await loop.run_in_executor(_pyttsx3_executor, _init_engine)
        except Exception as e:
            log.warning(f"pyttsx3 engine setup error: {e}")
            _pyttsx3_engine = None

        return _pyttsx3_engine


async def _synthesize_pyttsx3(text: str, voice: Optional[str]) -> Optional[bytes]:
    """Generate speech using pyttsx3 (Windows SAPI5 fallback)."""
    try:
        engine = await _ensure_pyttsx3_engine()
    except Exception as e:
        log.warning(f"pyttsx3 engine error: {e}", exc_info=True)
        return None

    if engine is None:
        return None

    loop = asyncio.get_event_loop()

    def _render():
        try:
            # Save to temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name

            engine.save_to_file(text, tmp_path)
            engine.runAndWait()

            # Read WAV bytes
            with open(tmp_path, "rb") as f:
                audio_bytes = f.read()

            # Clean up
            try:
                os.unlink(tmp_path)
            except OSError as e:
                log.debug("Failed to delete temporary WAV file %s: %s", tmp_path, e)

            # Check if synthesis produced empty audio
            if not audio_bytes:
                log.warning("pyttsx3 synthesis produced empty audio")
                return None

            return audio_bytes
        except Exception as e:
            log.warning(f"pyttsx3 synthesis error: {e}", exc_info=True)
            return None

    try:
        result = await loop.run_in_executor(_pyttsx3_executor, _render)
        return result
    except Exception as e:
        log.warning(f"pyttsx3 execution error: {e}", exc_info=True)
        return None
