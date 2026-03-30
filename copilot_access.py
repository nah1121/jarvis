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


def _find_copilot_command() -> Optional[str]:
    """Locate the Copilot CLI binary on the system."""
    for name in ("copilot", "copilot.cmd"):
        path = shutil.which(name)
        if path:
            return path
    return None


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
    timeout: int = int(os.getenv("COPILOT_TIMEOUT", "60"))
    enabled: bool = os.getenv("COPILOT_CLI_ENABLED", "true").lower() == "true"

    def __post_init__(self):
        self.command = _find_copilot_command()
        if not self.command:
            log.warning("Copilot CLI not found on PATH (copilot/copilot.cmd).")

    @property
    def available(self) -> bool:
        return self.enabled and bool(self.command)

    async def chat(
        self,
        system: str,
        messages: List[Dict[str, str]],
        *,
        use_smart: bool = False,
        cwd: str | None = None,
        timeout: int | None = None,
    ) -> str:
        """Call `copilot -p ...` and return the text response."""
        if not self.available:
            raise CopilotError("Copilot CLI not available or disabled.")

        prompt = _format_prompt(system, messages)
        model = self.smart_model if use_smart else self.fast_model
        cmd = [self.command, "-p", prompt]
        if model:
            cmd.extend(["--model", model])

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
        except FileNotFoundError as e:
            raise CopilotError("Copilot CLI not found on system.") from e
        except Exception as e:
            raise CopilotError(f"Failed to start Copilot CLI: {e}") from e

        wait_timeout = timeout or self.timeout
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=wait_timeout)
        except asyncio.TimeoutError:
            process.kill()
            raise CopilotError(f"Copilot CLI timed out after {wait_timeout}s")

        if process.returncode != 0:
            error_text = stderr.decode(errors="ignore").strip()
            raise CopilotError(error_text or "Copilot CLI returned a non-zero exit code.")

        return stdout.decode(errors="ignore").strip()

    async def chat_fast(self, system: str, messages: List[Dict[str, str]], **kwargs) -> str:
        return await self.chat(system, messages, use_smart=False, **kwargs)

    async def chat_smart(self, system: str, messages: List[Dict[str, str]], **kwargs) -> str:
        return await self.chat(system, messages, use_smart=True, **kwargs)

