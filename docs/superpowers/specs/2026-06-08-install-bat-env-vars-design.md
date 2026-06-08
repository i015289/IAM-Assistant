# Design: install.bat — Interactive .env Configuration & Windows User Env Vars

**Date:** 2026-06-08
**Status:** Approved
**Scope:** `install.bat` only. `install.sh` is unchanged.

## Problem

Current `install.bat` creates `.env` and `.sapcli.env` from templates with placeholder values. Users must edit two files by hand before the app runs. Three pain points:

1. **Fresh Miniconda installs are not ready out-of-the-box** — `conda` may not be on `cmd.exe` PATH (depends on whether the user ticked "Add to PATH" during install), and `conda init cmd.exe` has not run, so even when conda is found, future `cmd` shells won't auto-activate. The current installer just exits with an error and tells the user to re-launch from Anaconda Prompt.
2. **`ANTHROPIC_API_KEY` is the only mandatory secret with no usable default** — every user has to edit `.env` to paste it in. The installer could just ask.
3. **Windows-specific env quirks** — `sapcli-env\Scripts` is not on user PATH (so `uvicorn`/`sapcli` need `conda run -n sapcli-env` every time), and Python defaults to legacy code page on Windows (recurring `UnicodeEncodeError` with Chinese / non-ASCII output).

## Goals

- Auto-bootstrap a fresh Miniconda install: locate `conda.exe` even when it's not on PATH, add it to user PATH if missing, and run `conda init cmd.exe` if not yet initialized.
- Optionally prompt for `ANTHROPIC_API_KEY` at install time and write it directly to `.env`.
- Set Windows user environment variables (`PYTHONUTF8=1` and `PATH` additions) so future shells work without manual setup.
- Preserve the existing "scaffold early, edit during pip install" UX as the default — interactivity is opt-in.
- Fail-soft on env var setup: warnings, not hard errors.

## Non-Goals

- Prompting for OIDC values, `BASE_URL`, or any `.sapcli.env` field. Defaults in templates are usable for the common dev case; users edit those files manually.
- Changing `install.sh`. macOS/Linux users typically use `.envrc` / shell rc; setx has no equivalent need.
- Introducing a separate Python helper script. Keep changes inside `install.bat` to match existing style and avoid new files.
- Modifying registry directly via PowerShell. `setx` is sufficient for this scope.
- **Writing `.condarc`.** Corporate proxy / mirror channel settings vary per environment and may be governed by IT policy. install.bat will detect a missing `.condarc` and print a hint, but never write to it.
- Installing Miniconda itself. If conda is not found anywhere known, the installer still aborts with a download link.

## Step Order (6 → 7 steps)

| Step | Action | Status |
|------|--------|--------|
| **1/7** | **Conda bootstrap (find conda → setx PATH if missing → conda init cmd.exe → .condarc hint)** | **modified** |
| **2/7** | **Scaffold `.env`/`.sapcli.env` + optional interactive `ANTHROPIC_API_KEY` prompt** | **modified** |
| 3/7 | Create `sapcli-env` conda environment (if missing) | unchanged |
| 4/7 | Install sapcli into `sapcli-env` | unchanged |
| 5/7 | Install MCP server requirements | unchanged |
| 6/7 | Install web app requirements | unchanged |
| **7/7** | **Configure Windows user environment variables (PYTHONUTF8, sapcli-env on PATH)** | **new** |

Step 7 must run after Step 3 because it derives `sapcli-env\Scripts` from the conda base path, which is only meaningful once the env exists.

## Step 1 — Conda Bootstrap

### Detection order

1. **`where conda` first** — fast path; if conda is already on PATH, skip the rest of detection.
2. **Probe known install locations** if not on PATH:
   - `%USERPROFILE%\miniconda3\Scripts\conda.exe`
   - `%USERPROFILE%\anaconda3\Scripts\conda.exe`
   - `%LOCALAPPDATA%\miniconda3\Scripts\conda.exe`
   - `%LOCALAPPDATA%\anaconda3\Scripts\conda.exe`
   - `%PROGRAMDATA%\miniconda3\Scripts\conda.exe`
   - `%PROGRAMDATA%\anaconda3\Scripts\conda.exe`
   - `C:\ProgramData\Miniconda3\Scripts\conda.exe`
3. **If still not found** — abort with the existing error pointing to the Miniconda download URL.

When found via probing (i.e. not on current PATH), set a local `CONDA_EXE` variable to the full path and use it for the remaining commands in this script.

### PATH repair (if conda was found via probing)

When conda was found by probing (not via `where`), it means user PATH lacks the conda Scripts dir. Use the same registry-based user-PATH append pattern as Step 7:

```bat
REM Append <conda_install>\Scripts to user PATH
for /f "tokens=2,*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul ^| findstr /i "Path"') do set "USER_PATH=%%B"
if defined USER_PATH (
  setx PATH "!USER_PATH!;!CONDA_SCRIPTS_DIR!" >nul
) else (
  setx PATH "!CONDA_SCRIPTS_DIR!" >nul
)
```

`!CONDA_SCRIPTS_DIR!` is derived from `!CONDA_EXE!` by stripping `\conda.exe`. setx is fail-soft (WARNING, continue — Step 1 still works because we use `!CONDA_EXE!` directly for the rest of the script).

### `conda init cmd.exe`

Detect whether `conda init cmd.exe` has been run by checking the AutoRun registry value:

```bat
reg query "HKCU\Software\Microsoft\Command Processor" /v AutoRun 2>nul | findstr /i "conda_hook" >nul
if errorlevel 1 (
  REM Not initialized — run it
  "!CONDA_EXE!" init cmd.exe >nul
)
```

If `conda init` fails: print WARNING, continue. install.bat itself does not need cmd auto-activation; this is purely a quality-of-life bootstrap for future `cmd` sessions.

### `.condarc` hint (no write)

```bat
if not exist "%USERPROFILE%\.condarc" (
  echo.
  echo   NOTE: No .condarc found. If pip / conda installs fail due to network
  echo   issues, you may need to configure a proxy or internal channel mirror.
  echo   See: https://docs.conda.io/projects/conda/en/latest/user-guide/configuration/use-condarc.html
  echo.
)
```

Print-only — never write to `.condarc`. The corporate environment may have its own policy.

### Output / UX

Step 1 prints structured progress so the user can see what was auto-fixed:

```
==> [1/7] Checking for conda...
  conda: C:\Users\I015289\miniconda3\Scripts\conda.exe (found via probing — adding to user PATH)
  Running 'conda init cmd.exe' (one-time setup)...
  NOTE: No .condarc found. If pip / conda installs fail due to network issues...
```

If conda is already on PATH and initialized, the step prints just one line (existing behavior preserved).

## Step 2 — Interactive `.env` Configuration

### Flow

```
[2/7] Scaffolding .env and .sapcli.env from templates...
  (only if .env does not exist:)
    Configure ANTHROPIC_API_KEY interactively now? [y/N]:  ← default = N (Enter)
      y → Enter ANTHROPIC_API_KEY (Hyperspace key, leave empty to skip):
            non-empty → write to .env
            empty     → leave .env.example placeholder
      N → leave .env.example placeholder (existing behavior)
  (always:)
    SESSION_SECRET regenerated with python secrets.token_hex(32)
  .sapcli.env: copy from template (no prompt, existing behavior)
```

### Behavior matrix

| `.env` exists? | User answer | API key entered? | Result |
|----------------|-------------|------------------|--------|
| Yes | (no prompt) | — | Leave alone |
| No | N (default) | — | Copy template, regen SESSION_SECRET, placeholder API key |
| No | y | non-empty | Copy template, regen SESSION_SECRET, **write API key** |
| No | y | empty | Copy template, regen SESSION_SECRET, placeholder API key |

### Idempotency

- If `.env` already exists, the installer never prompts and never overwrites — same as today.
- The interactive branch only fires on a fresh install (`.env` missing).

### Implementation note

Use a single `conda run -n base python -c "..."` invocation that rewrites `.env` line-by-line, replacing both `SESSION_SECRET=` and (if provided) `ANTHROPIC_API_KEY=`. Symmetric with the existing SESSION_SECRET pattern in `install.bat`.

If the python rewrite fails, `goto :error` — the template was already copied, leaving a half-written file is worse than aborting.

### `.sapcli.env`

No interactive prompt. Existing behavior: copy from `.sapcli.env.example` if missing, leave alone if present. Defaults (`ANZEIGER` / `display` against ER6) work for the read-only analysis use case this project targets.

## Step 7 — Windows User Environment Variables

### Variables set

| Variable | Value | Why |
|----------|-------|-----|
| `PYTHONUTF8` | `1` | Force UTF-8 mode globally; avoids `UnicodeEncodeError` from Chinese / non-ASCII output on Windows. |
| `PATH` | `…;<conda_base>\envs\sapcli-env\Scripts` | Lets users run `uvicorn`, `sapcli`, etc. directly without `conda run -n sapcli-env`. |

### `PYTHONUTF8` logic

```bat
if not defined PYTHONUTF8 (
  setx PYTHONUTF8 1 >nul
)
```

- Checks current shell env, which reflects user-level setx from prior runs (new shells will see it).
- If `setx` exits non-zero: print `WARNING`, do NOT `goto :error`. Continue.

### `PATH` logic — three-stage idempotency

```bat
REM 1. Discover the actual sapcli-env\Scripts path
for /f "delims=" %%I in ('conda info --base') do set "CONDA_BASE=%%I"
set "SAPCLI_SCRIPTS=!CONDA_BASE!\envs\sapcli-env\Scripts"

REM 2. Check current %PATH%; if already there, skip
echo !PATH! | findstr /i /c:"!SAPCLI_SCRIPTS!" >nul
if errorlevel 1 (
  REM 3. Read USER PATH from registry (NOT %PATH%) and append
  for /f "tokens=2,*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul ^| findstr /i "Path"') do set "USER_PATH=%%B"
  if defined USER_PATH (
    setx PATH "!USER_PATH!;!SAPCLI_SCRIPTS!" >nul
  ) else (
    setx PATH "!SAPCLI_SCRIPTS!" >nul
  )
)
```

**Critical: read user-level PATH from `HKCU\Environment`, not `%PATH%`.**
`%PATH%` is the merged session value (system + user). `setx PATH "%PATH%"` is a well-known anti-pattern that copies the system PATH into the user PATH, permanently bloating it on every install run. Reading from the registry isolates the user PATH.

If `reg query` returns no value (user PATH never set), set `setx PATH` to just the new entry.

If the conda base lookup fails or `setx` errors: print `WARNING` with the path the user can add manually, do NOT `goto :error`.

### Idempotency summary

- **PYTHONUTF8**: `if not defined` skip — never re-set.
- **PATH**: `findstr` skip if already present — never appends a duplicate.
- Both checks make repeated `install.bat` runs safe.

## Error Handling

| Failure point | Action |
|---------------|--------|
| Step 1 — conda not on PATH AND not in any known install location | `exit /b 1` (existing behavior, hard error with download link) |
| Step 1 — `setx PATH` to add conda Scripts dir | Print WARNING, continue (script uses `!CONDA_EXE!` directly) |
| Step 1 — `conda init cmd.exe` | Print WARNING, continue (not required for this install run) |
| `.env` template copy | `goto :error` (existing behavior) |
| Python rewrite of `.env` (SESSION_SECRET or API key) | `goto :error` (existing behavior) |
| `setx PYTHONUTF8` | Print WARNING, continue |
| `setx PATH` (Step 7) | Print WARNING with manual-add path, continue |
| `conda info --base` failure (Step 7) | Print WARNING, skip Step 7 PATH portion, continue |

Rationale: env var / shell init are quality-of-life improvements. A failure here should not block a working install. Conda being completely unfindable is the only hard abort — without conda there is nothing to install.

## Completion Message

```
[OK] Install complete.

Next steps:
  1. If not yet edited: fill in .env        (ANTHROPIC_API_KEY = your Hyperspace API key, OIDC_*, BASE_URL).
  2. If not yet edited: fill in .sapcli.env  (SAP_ASHOST, SAP_PORT, SAP_CLIENT, SAP_PASSWORD).
  3. Open a NEW Anaconda Prompt (or cmd) for env var changes (PYTHONUTF8, PATH, conda init) to take effect.
  4. Start the server:
       conda run -n sapcli-env uvicorn app.main:app --reload
```

Line 3 is new — `setx` and `conda init` do not affect the current shell, only future ones.

## Files Changed

- `install.bat` — Step 1 expanded with conda probing, PATH repair, conda init, .condarc hint; Step 2 expanded with interactive prompt; Step 7 added; completion message updated; step counters renumbered (6 → 7).
- `install.sh` — unchanged.
- `.env.example` / `.sapcli.env.example` — unchanged.
- `docs/superpowers/specs/2026-06-08-install-bat-env-vars-design.md` — this file.

## Constraints

- `setlocal enabledelayedexpansion` already enabled at top of `install.bat`; `!VAR!` syntax available.
- Step 1 must use `!CONDA_EXE!` (the resolved path) for all subsequent conda commands rather than relying on `where conda`, because the user PATH update via setx does NOT affect the current shell.
- `conda run -n base python` is reachable in Anaconda Prompt — same assumption as the existing SESSION_SECRET line. Step 1 ensures `!CONDA_EXE!` exists; later steps use bare `conda run` since by then either it was already on PATH or the user re-runs from a new shell after PATH repair.
- `setx` truncates values at 1024 chars. User PATH appending pushes total length up; if a user already has a near-1024 user PATH, this could fail. The WARNING fallback is the safety net.
- Never overwrite existing `.env` / `.sapcli.env` (idempotent).
- Both files remain in `.gitignore`.
- `.condarc` is never written to by the installer — only detected and hinted about.

## Out of Scope (deliberately)

- Prompting for OIDC, BASE_URL, SAP credentials.
- Modifying `install.sh`.
- A separate Python configuration helper script.
- Touching system-level (HKLM) environment variables.
- Installing Miniconda itself, or downloading it on the user's behalf.
- Writing `.condarc` (proxy, channels, always_yes).
