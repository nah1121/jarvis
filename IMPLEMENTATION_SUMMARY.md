# JARVIS — Copilot CLI Migration (Windows-ready)

## Overview
- Replaced Anthropic/Claude usage with GitHub Copilot CLI subprocess calls (`copilot chat --message ...`).
- Centralized Copilot invocation in `copilot_access.py` with async subprocess execution, timeouts, and Windows-friendly command discovery (`copilot` / `copilot.cmd`).
- Retained Windows adaptations: PowerShell automation, local Fish Speech TTS, and stubbed macOS-only integrations (Calendar/Mail/Notes).

## Key Files
- `copilot_access.py` — CopilotRunner wrapper around the Copilot CLI, builds prompts from system + history, handles timeouts/errors.
- `server.py` — All LLM calls (chat, summaries, intent classification, research, task dispatch) now route through CopilotRunner; settings/test endpoints updated for Copilot variables.
- `planner.py`, `memory.py`, `screen.py`, `work_mode.py`, `qa.py` — Switched to CopilotRunner instead of Anthropic SDK or Claude CLI.
- `actions.py` — Terminal automation opens Copilot CLI sessions; build/research actions no longer invoke Claude.
- `frontend/src/settings.ts` — Settings panel shows Copilot status/test instead of Anthropic key input.
- `.env.example` — New Copilot variables (`COPILOT_CLI_ENABLED`, `COPILOT_MODEL_FAST`, `COPILOT_MODEL_SMART`, `COPILOT_TIMEOUT`); Anthropic entries removed.
- `SETUP_WINDOWS.md`, `start-jarvis.ps1`, `README` references updated to Copilot CLI and local Fish Speech.

## Behavior Notes
- Two model tiers selectable via environment (`COPILOT_MODEL_FAST`, `COPILOT_MODEL_SMART`).
- No streaming from Copilot CLI; responses gathered fully then sent to TTS, preserving conversational flow.
- Research/build dispatches run Copilot CLI asynchronously and summarize results with the fast model.
- Memory extraction and planning fall back to heuristics when Copilot CLI is unavailable.
