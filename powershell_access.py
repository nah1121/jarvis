"""
Cross-platform terminal execution helpers with PowerShell support on Windows.

On Windows: executes commands via powershell.exe with optional execution policy
control. On macOS/Linux: falls back to bash -lc for compatibility.

All commands are logged and checked against a small set of dangerous patterns
to avoid destructive actions being run silently.
"""

import logging
import os
import platform
import re
import subprocess
import time
from pathlib import Path
from typing import Optional

log = logging.getLogger("jarvis.powershell")

DEFAULT_TIMEOUT = int(os.getenv("TERMINAL_TIMEOUT", "30") or 30)
POWERSHELL_ENABLED = os.getenv("POWERSHELL_ENABLED", "true").lower() != "false"
EXECUTION_POLICY = os.getenv("POWERSHELL_EXECUTION_POLICY", "RemoteSigned").strip()
LOG_PATH = Path(os.getenv("TERMINAL_LOG_PATH", Path.home() / ".jarvis_terminal.log"))

# Commands that should never be run automatically
DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/?",
    r"Remove-Item\s+-Recurse\s+-Force\s+[A-Za-z]:\\",
    r"Remove-Item\s+-Recurse\s+-Force\s+/",
    r"format\s+(volume|fs)",
    r"Format-Volume",
    r"mkfs",
    r"diskpart",
    r"bcdedit",
    r"shutdown\s",
    r"Restart-Computer",
    r"Stop-Computer",
    r"Set-ExecutionPolicy\s+Unrestricted",
    r"del\s+/s\s+/q\s+C:\\",
    r"rd\s+/s\s+/q\s+C:\\",
]


def _is_windows() -> bool:
    return platform.system().lower().startswith("win")


def _append_command_log(entry: str) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(entry + "\n")
    except Exception:
        # Logging failure should never break command execution
        pass


def _looks_dangerous(command: str) -> tuple[bool, Optional[str]]:
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, flags=re.IGNORECASE):
            return True, pattern
    return False, None


def _build_ps_args(command: str, use_file: bool = False) -> list[str]:
    args = ["powershell.exe", "-NoProfile"]
    if EXECUTION_POLICY:
        args += ["-ExecutionPolicy", EXECUTION_POLICY]
    if use_file:
        args += ["-File", command]
    else:
        args += ["-Command", command]
    return args


def run_shell_command(
    command: str,
    cwd: str | None = None,
    timeout: Optional[int] = None,
    prefer_file: bool = False,
) -> dict:
    """Execute a shell command cross-platform with safety checks."""
    cleaned = command.strip()
    if not cleaned:
        return {
            "success": False,
            "blocked": True,
            "message": "No command provided.",
            "command": command,
        }

    dangerous, pattern = _looks_dangerous(cleaned)
    if dangerous:
        msg = f"Blocked potentially destructive command (matched '{pattern}')."
        log.warning(msg)
        _append_command_log(f"[BLOCKED] {cleaned} :: {msg}")
        return {
            "success": False,
            "blocked": True,
            "message": msg,
            "command": command,
        }

    effective_timeout = timeout or DEFAULT_TIMEOUT
    start = time.time()
    use_windows = _is_windows()
    runner = "powershell" if use_windows else "bash"

    if use_windows and not POWERSHELL_ENABLED:
        msg = "PowerShell execution is disabled by configuration."
        log.warning(msg)
        _append_command_log(f"[DISABLED] {cleaned} :: {msg}")
        return {
            "success": False,
            "blocked": True,
            "message": msg,
            "command": command,
        }

    args: list[str]
    if use_windows:
        use_file_mode = prefer_file and Path(cleaned).suffix.lower() == ".ps1" and Path(cleaned).exists()
        args = _build_ps_args(cleaned, use_file=use_file_mode)
    else:
        args = ["/bin/bash", "-lc", cleaned]

    log.info(f"Executing {runner} command: {cleaned}")
    try:
        completed = subprocess.run(
            args,
            capture_output=True,
            text=True,
            cwd=cwd or None,
            timeout=effective_timeout,
        )
        duration = round(time.time() - start, 2)
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        success = completed.returncode == 0
        entry = (
            f"[{runner.upper()}][EXIT {completed.returncode}][{duration}s] {cleaned} "
            f":: stdout={len(stdout)} chars stderr={len(stderr)} chars"
        )
        _append_command_log(entry)
        return {
            "success": success,
            "blocked": False,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": completed.returncode,
            "duration": duration,
            "command": command,
            "runner": runner,
        }
    except subprocess.TimeoutExpired:
        msg = f"Command timed out after {effective_timeout}s."
        log.warning(msg)
        _append_command_log(f"[TIMEOUT] {cleaned} :: {msg}")
        return {
            "success": False,
            "blocked": False,
            "stdout": "",
            "stderr": msg,
            "exit_code": None,
            "duration": effective_timeout,
            "command": command,
            "runner": runner,
        }
    except Exception as exc:
        msg = f"Command failed: {exc}"
        log.error(msg)
        _append_command_log(f"[ERROR] {cleaned} :: {msg}")
        return {
            "success": False,
            "blocked": False,
            "stdout": "",
            "stderr": str(exc),
            "exit_code": None,
            "duration": round(time.time() - start, 2),
            "command": command,
            "runner": runner,
        }


def format_command_output(result: dict, max_chars: int = 500) -> str:
    """Create a compact, voice-friendly summary of a command result."""
    if result.get("blocked"):
        return result.get("message") or "Command blocked for safety."

    exit_code = result.get("exit_code")
    stdout = (result.get("stdout") or "").strip()
    stderr = (result.get("stderr") or "").strip()

    if stdout and len(stdout) > max_chars:
        stdout = stdout[: max_chars - 3] + "..."
    if stderr and len(stderr) > max_chars:
        stderr = stderr[: max_chars - 3] + "..."

    if exit_code is None:
        status = "did not finish"
    elif exit_code == 0:
        status = "succeeded"
    else:
        status = f"failed with exit code {exit_code}"

    if stdout and stderr:
        body = f"Output: {stdout} | Errors: {stderr}"
    elif stdout:
        body = f"Output: {stdout}"
    elif stderr:
        body = f"Errors: {stderr}"
    else:
        body = "No output."

    return f"Command {status}. {body}"
