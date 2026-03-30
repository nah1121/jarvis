import asyncio
import logging
import os
from typing import Optional, Tuple

log = logging.getLogger("jarvis.tts")

# TTS changed for 8GB VRAM Windows 11 - using Kokoro or Edge-TTS instead of Fish Speech
DEFAULT_ENGINE = os.getenv("TTS_ENGINE", "edge").lower()
EDGE_VOICE = os.getenv("TTS_EDGE_VOICE", os.getenv("TTS_VOICE", "en-GB-RyanNeural"))
KOKORO_VOICE = os.getenv("TTS_KOKORO_VOICE", os.getenv("TTS_VOICE", "af_bella"))
KOKORO_LANG = os.getenv("TTS_KOKORO_LANG", (KOKORO_VOICE or "b")[0])
KOKORO_DEVICE = os.getenv("TTS_KOKORO_DEVICE", "cpu")
KOKORO_SPEED = float(os.getenv("TTS_KOKORO_SPEED", "1.0"))

_kokoro_pipeline = None
_kokoro_lock = asyncio.Lock()


async def synthesize(text: str, preferred_engine: Optional[str] = None, voice: Optional[str] = None) -> Tuple[Optional[bytes], str]:
    """Generate audio bytes and return (audio, engine_used)."""
    engine = (preferred_engine or DEFAULT_ENGINE or "edge").lower()

    if engine == "kokoro":
        audio = await _synthesize_kokoro(text, voice)
        if audio:
            return audio, "kokoro"
        log.warning("Kokoro TTS failed; falling back to Edge TTS")
        audio = await _synthesize_edge(text, voice)
        return audio, "edge" if audio else (None, "kokoro")

    audio = await _synthesize_edge(text, voice)
    if audio:
        return audio, "edge"
    log.warning("Edge TTS failed; trying Kokoro as fallback")
    audio = await _synthesize_kokoro(text, voice)
    return audio, "kokoro" if audio else (None, engine)


async def _synthesize_edge(text: str, voice: Optional[str]) -> Optional[bytes]:
    voice_to_use = voice or EDGE_VOICE or "en-GB-RyanNeural"
    try:
        import edge_tts
    except ImportError:
        log.warning("edge-tts not installed. Run `pip install edge-tts`.")
        return None

    audio = b""
    try:
        communicate = edge_tts.Communicate(text, voice_to_use)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio += chunk["data"]
    except Exception as e:
        log.warning(f"Edge TTS error: {e}")
        return None

    return audio or None


async def _ensure_kokoro_pipeline():
    global _kokoro_pipeline
    if _kokoro_pipeline is not None:
        return _kokoro_pipeline

    async with _kokoro_lock:
        if _kokoro_pipeline is not None:
            return _kokoro_pipeline

        loop = asyncio.get_event_loop()

        def _build_pipeline():
            from kokoro import KPipeline
            return KPipeline(lang_code=KOKORO_LANG, device=KOKORO_DEVICE)

        try:
            _kokoro_pipeline = await loop.run_in_executor(None, _build_pipeline)
        except Exception as e:
            log.warning(f"Kokoro init failed: {e}")
            _kokoro_pipeline = None
        return _kokoro_pipeline


async def _synthesize_kokoro(text: str, voice: Optional[str]) -> Optional[bytes]:
    try:
        pipeline = await _ensure_kokoro_pipeline()
    except ImportError:
        log.warning("Kokoro not installed. Run `pip install kokoro numpy torch --upgrade`.")
        return None

    if pipeline is None:
        return None

    voice_to_use = voice or KOKORO_VOICE or "af_bella"
    loop = asyncio.get_event_loop()

    def _render():
        import numpy as np

        audio_chunks = []
        for result in pipeline(text, voice=voice_to_use, speed=KOKORO_SPEED):
            if result.audio is None:
                continue
            audio_chunks.append(result.audio.detach().cpu().numpy())

        if not audio_chunks:
            return None

        merged = np.concatenate(audio_chunks)
        merged = np.clip(merged, -1.0, 1.0)
        return (merged * 32767).astype("<i2").tobytes()

    try:
        return await loop.run_in_executor(None, _render)
    except Exception as e:
        log.warning(f"Kokoro synthesis error: {e}")
        return None
