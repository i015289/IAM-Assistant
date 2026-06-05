# Design: Early .env Scaffold in One-Click Installer

**Date:** 2026-06-05
**Status:** Approved

## Problem

The current installer scaffolds `.env` and `.sapcli.env` in Step 6 (the last step), after all pip installs complete. This means users cannot edit their configuration files during the 2-5 minute installation period — they must wait for everything to finish before they can do anything useful.

## Solution

Move the scaffold step to Step 2 (immediately after the conda check), so users can edit `.env` and `.sapcli.env` in parallel while pip installs run in the background.

## New Step Order

| Step | Action |
|------|--------|
| 1 | Check conda is on PATH |
| 2 | Scaffold `.env` and `.sapcli.env` from `.example` files (**moved here**) |
| 3 | Create `sapcli-env` conda environment (if missing) |
| 4 | Install sapcli into sapcli-env |
| 5 | Install MCP server requirements |
| 6 | Install web app requirements |
| 7 | Print completion message |

## SESSION_SECRET Generation

At Step 2, `sapcli-env` does not yet exist. SESSION_SECRET is generated using:
- `install.sh`: `python3 -c 'import secrets; print(secrets.token_hex(32))'` — always available on macOS/Linux
- `install.bat`: `python -c '...'` — available in Anaconda Prompt / PowerShell with conda base

## User Experience

After Step 2, a prompt is printed:
> "Config files created — edit .env and .sapcli.env while the install continues."

The final "Next steps" message changes steps 1 and 2 from "Edit X" to "If not yet edited, edit X now."

## Files Changed

- `install.sh` — step reorder, scaffold logic moved to Step 2, SECRET uses `python3`
- `install.bat` — same changes, symmetric

## Constraints

- Never overwrite existing `.env` or `.sapcli.env` (idempotent)
- Both files stay in `.gitignore`
- `.env.example` and `.sapcli.env.example` remain unchanged
