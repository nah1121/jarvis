"""
Copilot CLI access layer.

Replaces direct Anthropic/Claude API usage with the GitHub Copilot CLI.
All LLM calls go through `copilot -p ...` (non-interactive mode) using subprocess.
"""

import asyncio
import logging
import os
import shutil
from dataclasses import dataclass
from typing import List, Dict, Optional

log = logging.getLogger("jarvis.copilot")


class CopilotError(Exception):
    """Raised when the Copilot CLI call fails."""


def _check_copilot_available() -> bool:
    """Check if copilot command is available in PATH."""
    return shutil.which("copilot") is not None


def _format_prompt(system: str, messages: List[Dict[str, str]]) -> str:
    """Build a plain-text prompt containing system instructions + chat history."""
    parts: list[str] = []
    if system:
        parts.append(system.strip())
    if messages:
        parts.append("Conversation:")
        for msg in messages:
            role = msg.get("role", "user").upper()
            content = msg.get("content", "").strip()
            parts.append(f"{role}: {content}")
    parts.append("ASSISTANT:")
    return "\n\n".join(parts)


@dataclass
class CopilotRunner:
    """Thin wrapper around the Copilot CLI for async calls."""

    fast_model: str = os.getenv("COPILOT_MODEL_FAST", "gpt-4.1-mini")
    smart_model: str = os.getenv("COPILOT_MODEL_SMART", "gpt-4.1")
    timeout: int = int(os.getenv("COPILOT_TIMEOUT", "120"))  # Increased from 60 to 120 seconds
    enabled: bool = os.getenv("COPILOT_CLI_ENABLED", "true").lower() == "true"

    def __post_init__(self):
        self.copilot_available = _check_copilot_available()
        if not self.copilot_available:
            log.warning("Copilot CLI not found in PATH.")
        else:
            log.info("Copilot CLI found in PATH.")

    @property
    def available(self) -> bool:
        return self.enabled and self.copilot_available

    async def chat(
        self,
        system: str,
        messages: List[Dict[str, str]],
        *,
        use_smart: bool = False,
        cwd: str | None = None,
        timeout: int | None = None,
    ) -> str:
        """Call `copilot -p ...` and return the text response.

        Uses -p (--prompt) flag to provide prompt programmatically in non-interactive mode.
        """
        if not self.available:
            raise CopilotError("Copilot CLI not available or disabled.")

        prompt = _format_prompt(system, messages)
        model = self.smart_model if use_smart else self.fast_model

        # Use -p for prompt (non-interactive mode)
        cmd = ["copilot", "-p", prompt]
        if model:
            cmd.extend(["--model", model])

        # Log the exact command for debugging (excluding full prompt for brevity)
        log.debug(f"Executing Copilot CLI: copilot -p <prompt> {f'--model {model}' if model else ''}")
        log.debug(f"Working directory: {cwd or 'current'}")

        # Log the full command list structure for debugging unknown option errors
        cmd_preview = [cmd[0], cmd[1], f"<{len(prompt)} chars>"] + cmd[3:]
        log.debug(f"Full command structure: {cmd_preview}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
        except FileNotFoundError as e:
            log.error(f"Copilot CLI executable not found in PATH")
            raise CopilotError("Copilot CLI not found on system.") from e
        except Exception as e:
            log.error(f"Failed to start Copilot CLI subprocess: {e}")
            raise CopilotError(f"Failed to start Copilot CLI: {e}") from e

        wait_timeout = timeout or self.timeout
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=wait_timeout)
        except asyncio.TimeoutError:
            process.kill()
            log.error(f"Copilot CLI timed out after {wait_timeout}s")
            raise CopilotError(f"Copilot CLI timed out after {wait_timeout}s")

        if process.returncode != 0:
            error_text = stderr.decode(errors="ignore").strip()
            # Log full stderr for debugging
            log.error(f"Copilot CLI failed (exit code {process.returncode})")
            log.error(f"stderr: {error_text}")

            # Check for common errors and provide helpful guidance
            if "--no-warnings" in error_text or "unknown option" in error_text.lower():
                log.error(
                    "Copilot CLI reported an unknown option error. "
                    "This may indicate:\n"
                    "  1. A PowerShell alias or function is wrapping the copilot command\n"
                    "  2. An environment variable is adding extra flags\n"
                    "  3. The copilot binary is a wrapper script with incompatible options\n"
                    f"  Command being executed: {cmd_preview}"
                )

            raise CopilotError(error_text or "Copilot CLI returned a non-zero exit code.")

        result = stdout.decode(errors="ignore").strip()
        log.debug(f"Copilot CLI response length: {len(result)} chars")
        return result

    async def chat_fast(self, system: str, messages: List[Dict[str, str]], **kwargs) -> str:
        return await self.chat(system, messages, use_smart=False, **kwargs)

    async def chat_smart(self, system: str, messages: List[Dict[str, str]], **kwargs) -> str:
        return await self.chat(system, messages, use_smart=True, **kwargs)

