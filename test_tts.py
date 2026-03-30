#!/usr/bin/env python3
"""
Simple test script for Piper TTS integration.
Tests both Piper and pyttsx3 engines.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tts_access import synthesize


async def test_piper():
    """Test Piper TTS engine."""
    print("\n=== Testing Piper TTS ===")
    text = "Hello, I am JARVIS, your personal AI assistant."

    audio, engine = await synthesize(text, preferred_engine="piper")

    if audio:
        print(f"✅ Piper TTS Success!")
        print(f"   Engine used: {engine}")
        print(f"   Audio size: {len(audio)} bytes")
        return True
    else:
        print(f"❌ Piper TTS Failed")
        print(f"   Engine attempted: {engine}")
        return False


async def test_pyttsx3():
    """Test pyttsx3 fallback engine."""
    print("\n=== Testing pyttsx3 TTS ===")
    text = "Testing Windows SAPI5 speech synthesis."

    audio, engine = await synthesize(text, preferred_engine="pyttsx3")

    if audio:
        print(f"✅ pyttsx3 TTS Success!")
        print(f"   Engine used: {engine}")
        print(f"   Audio size: {len(audio)} bytes")
        return True
    else:
        print(f"❌ pyttsx3 TTS Failed")
        print(f"   Engine attempted: {engine}")
        return False


async def test_automatic_fallback():
    """Test automatic fallback mechanism."""
    print("\n=== Testing Automatic Fallback ===")
    text = "Testing automatic engine fallback."

    # Use default engine (should be Piper, falls back to pyttsx3 if needed)
    audio, engine = await synthesize(text)

    if audio:
        print(f"✅ Automatic fallback Success!")
        print(f"   Engine used: {engine}")
        print(f"   Audio size: {len(audio)} bytes")
        return True
    else:
        print(f"❌ All engines failed")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("JARVIS TTS Integration Test")
    print("=" * 60)

    print("\nEnvironment Configuration:")
    print(f"  TTS_ENGINE: {os.getenv('TTS_ENGINE', 'piper')}")
    print(f"  PIPER_VOICE: {os.getenv('PIPER_VOICE', 'en_US-ryan-high')}")
    print(f"  PIPER_MODEL_PATH: {os.getenv('PIPER_MODEL_PATH', '(auto-detect)')}")
    print(f"  PYTTSX3_RATE: {os.getenv('PYTTSX3_RATE', '180')}")

    results = []

    # Test each engine
    results.append(await test_piper())
    results.append(await test_pyttsx3())
    results.append(await test_automatic_fallback())

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    success_count = sum(results)
    total_count = len(results)
    print(f"Passed: {success_count}/{total_count}")

    if success_count == 0:
        print("\n⚠️  All tests failed. Check installation:")
        print("   - Piper: pip install piper-tts onnxruntime")
        print("   - Voice model: Download .onnx file to ./voices/")
        print("   - pyttsx3: pip install pyttsx3 pypiwin32")
    elif success_count < total_count:
        print("\n⚠️  Some tests failed. At least one engine is working.")
    else:
        print("\n✅ All tests passed! TTS integration is working correctly.")

    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
