# install.bat — Interactive .env Configuration & Windows Env Vars Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `install.bat` to (1) bootstrap fresh Miniconda installs (probe paths, repair PATH, run `conda init`), (2) optionally prompt for `ANTHROPIC_API_KEY` and write to `.env`, and (3) set Windows user env vars (`PYTHONUTF8=1`, append `sapcli-env\Scripts` to PATH).

**Architecture:** All changes inside `install.bat`. Steps remain numbered; the file expands from 6 to 7 steps. The Python `.env`-rewrite logic (extended to also write `ANTHROPIC_API_KEY`) is the only piece testable on non-Windows hosts; pull it into a small Python module and unit-test it. Everything else (setx, reg query, conda probing) is verified on Windows by the user after each task.

**Tech Stack:** Windows batch (`cmd.exe`), Python 3.x (already present via `conda run -n base python`), `pytest` for the Python module's unit tests.

**Spec:** `docs/superpowers/specs/2026-06-08-install-bat-env-vars-design.md`

---

## File Structure

| File | Responsibility | New / Modified |
|------|----------------|----------------|
| `install.bat` | Top-level installer; orchestrates 7 steps | Modified |
| `scripts/rewrite_env.py` | Single-purpose Python helper: rewrite `.env` keys (SESSION_SECRET, ANTHROPIC_API_KEY) | **New** |
| `tests/scripts/test_rewrite_env.py` | Pytest unit tests for `rewrite_env.py` | **New** |
| `install.sh` | Unchanged. macOS / Linux installer; not in scope. | — |

**Why pull `rewrite_env.py` out of the inline `python -c "..."`:**
- Current `install.bat:37` already uses an inline `python -c` for SESSION_SECRET. With the new ANTHROPIC_API_KEY logic, the inline string grows long and brittle (batch quoting + Python escaping).
- A module is unit-testable on macOS/Linux/Windows.
- `install.sh` can call the same module if it ever wants to (not in this plan).

**Note on TDD discipline:** Tasks 1-2 (`rewrite_env.py`) follow strict TDD. Tasks 3-7 (`install.bat`) cannot run on macOS, so they follow "small commit per behavior + Windows user verification" instead. After each batch task we ask the user to confirm the run on their Windows machine before moving on.

---

## Task 1: Create `rewrite_env.py` — failing tests first

**Files:**
- Create: `tests/scripts/test_rewrite_env.py`

- [ ] **Step 1: Write the failing test file**

Create `tests/scripts/test_rewrite_env.py`:

```python
"""Tests for scripts/rewrite_env.py — rewrites keys in a .env file in place."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make scripts/ importable
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import rewrite_env  # noqa: E402


def test_rewrites_existing_key(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("FOO=old\nBAR=keep\n", encoding="utf-8")

    rewrite_env.rewrite(env, {"FOO": "new"})

    assert env.read_text(encoding="utf-8") == "FOO=new\nBAR=keep\n"


def test_rewrites_multiple_keys(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("A=1\nB=2\nC=3\n", encoding="utf-8")

    rewrite_env.rewrite(env, {"A": "10", "C": "30"})

    assert env.read_text(encoding="utf-8") == "A=10\nB=2\nC=30\n"


def test_leaves_unrelated_lines_untouched(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("# comment\n\nFOO=old\n# trailing\n", encoding="utf-8")

    rewrite_env.rewrite(env, {"FOO": "new"})

    assert env.read_text(encoding="utf-8") == "# comment\n\nFOO=new\n# trailing\n"


def test_value_with_special_chars_is_written_literally(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("KEY=placeholder\n", encoding="utf-8")

    rewrite_env.rewrite(env, {"KEY": "abc=def&ghi#jkl"})

    assert env.read_text(encoding="utf-8") == "KEY=abc=def&ghi#jkl\n"


def test_missing_key_raises(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("FOO=old\n", encoding="utf-8")

    with pytest.raises(KeyError, match="MISSING"):
        rewrite_env.rewrite(env, {"MISSING": "x"})


def test_no_trailing_newline_preserved(tmp_path: Path) -> None:
    """If the source file has no trailing newline, output must not add one."""
    env = tmp_path / ".env"
    env.write_text("FOO=old", encoding="utf-8")

    rewrite_env.rewrite(env, {"FOO": "new"})

    assert env.read_text(encoding="utf-8") == "FOO=new"


def test_cli_invocation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`python rewrite_env.py <path> KEY1=val1 KEY2=val2` must work for install.bat."""
    env = tmp_path / ".env"
    env.write_text("A=1\nB=2\n", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["rewrite_env.py", str(env), "A=10", "B=20"])
    rewrite_env.main()

    assert env.read_text(encoding="utf-8") == "A=10\nB=20\n"


def test_cli_value_with_equals(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI must split on the FIRST `=` only, so values may contain `=`."""
    env = tmp_path / ".env"
    env.write_text("URL=old\n", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["rewrite_env.py", str(env), "URL=https://x.example.com/?a=1&b=2"])
    rewrite_env.main()

    assert env.read_text(encoding="utf-8") == "URL=https://x.example.com/?a=1&b=2\n"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `conda run -n sapcli-env pytest tests/scripts/test_rewrite_env.py -v`

Expected: ALL FAIL with `ModuleNotFoundError: No module named 'rewrite_env'`.

- [ ] **Step 3: Commit (red state)**

```bash
git add tests/scripts/test_rewrite_env.py
git commit -m "test: add failing tests for scripts/rewrite_env.py"
```

---

## Task 2: Implement `rewrite_env.py` — make tests green

**Files:**
- Create: `scripts/rewrite_env.py`

- [ ] **Step 1: Write the minimal implementation**

Create `scripts/rewrite_env.py`:

```python
"""Rewrite specific keys in a .env file in place.

Usage (CLI, called from install.bat / install.sh):
    python rewrite_env.py <path-to-.env> KEY1=value1 [KEY2=value2 ...]

Library usage:
    from rewrite_env import rewrite
    rewrite(Path(".env"), {"SESSION_SECRET": "abc...", "ANTHROPIC_API_KEY": "sk-..."})

Each KEY must already exist in the file. Lines not matching any KEY are
preserved verbatim, including comments, blank lines, and trailing-newline
state.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Mapping


def rewrite(path: Path, updates: Mapping[str, str]) -> None:
    """Rewrite each `KEY=...` line in `path` according to `updates`.

    Raises KeyError if any key in `updates` is not present in the file.
    """
    text = path.read_text(encoding="utf-8")
    has_trailing_newline = text.endswith("\n")
    lines = text.splitlines()  # discards the trailing newline if present

    seen: set[str] = set()
    new_lines: list[str] = []
    for line in lines:
        replaced = False
        for key, value in updates.items():
            prefix = f"{key}="
            if line.startswith(prefix):
                new_lines.append(f"{key}={value}")
                seen.add(key)
                replaced = True
                break
        if not replaced:
            new_lines.append(line)

    missing = set(updates.keys()) - seen
    if missing:
        raise KeyError(f"keys not found in {path}: {sorted(missing)}")

    out = "\n".join(new_lines)
    if has_trailing_newline:
        out += "\n"
    path.write_text(out, encoding="utf-8")


def main() -> None:
    if len(sys.argv) < 3:
        print("usage: rewrite_env.py <path> KEY1=value1 [KEY2=value2 ...]", file=sys.stderr)
        sys.exit(2)
    path = Path(sys.argv[1])
    updates: dict[str, str] = {}
    for arg in sys.argv[2:]:
        if "=" not in arg:
            print(f"error: argument {arg!r} is not KEY=VALUE", file=sys.stderr)
            sys.exit(2)
        key, value = arg.split("=", 1)
        updates[key] = value
    rewrite(path, updates)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `conda run -n sapcli-env pytest tests/scripts/test_rewrite_env.py -v`

Expected: 8 passed.

- [ ] **Step 3: Commit (green state)**

```bash
git add scripts/rewrite_env.py
git commit -m "feat: add scripts/rewrite_env.py for .env key rewrites"
```

---

## Task 3: Replace inline SESSION_SECRET python with `rewrite_env.py` call

**Files:**
- Modify: `install.bat:30-40` (the existing `.env` scaffold block)

This is a refactor: keep behavior identical, just route through the new module. Verifying this works first means later tasks can layer ANTHROPIC_API_KEY on top with confidence.

- [ ] **Step 1: Modify the SESSION_SECRET block**

Find the existing block at `install.bat:31-40`:

```bat
if exist .env (
  echo   .env already exists, leaving alone.
) else (
  copy /y .env.example .env >nul
  if errorlevel 1 goto :error
  REM Generate the secret AND rewrite the file in a single python invocation.
  conda run -n base python -c "import secrets; p='.env'; sec=secrets.token_hex(32); lines=open(p,encoding='utf-8').readlines(); open(p,'w',encoding='utf-8').writelines((f'SESSION_SECRET={sec}\n' if l.startswith('SESSION_SECRET=') else l) for l in lines)"
  if errorlevel 1 goto :error
  echo   .env created from .env.example with a fresh SESSION_SECRET.
)
```

Replace with:

```bat
if exist .env (
  echo   .env already exists, leaving alone.
) else (
  copy /y .env.example .env >nul
  if errorlevel 1 goto :error
  REM Generate SESSION_SECRET and rewrite the file via scripts\rewrite_env.py.
  for /f "delims=" %%I in ('conda run -n base python -c "import secrets; print(secrets.token_hex(32))"') do set "SESSION_SECRET_VAL=%%I"
  if not defined SESSION_SECRET_VAL goto :error
  conda run -n base python scripts\rewrite_env.py .env "SESSION_SECRET=!SESSION_SECRET_VAL!"
  if errorlevel 1 goto :error
  echo   .env created from .env.example with a fresh SESSION_SECRET.
)
```

- [ ] **Step 2: Verify on Windows (user verification)**

Ask the user to:
1. Delete a test `.env` (`del .env` if present, or test in a scratch directory).
2. Run `install.bat`.
3. Confirm `.env` was created with a non-placeholder `SESSION_SECRET=` (64 hex chars) and other lines unchanged.

Expected output line: `.env created from .env.example with a fresh SESSION_SECRET.`

- [ ] **Step 3: Commit**

```bash
git add install.bat
git commit -m "refactor(install): route SESSION_SECRET rewrite through rewrite_env.py"
```

---

## Task 4: Add interactive `ANTHROPIC_API_KEY` prompt to Step 2

**Files:**
- Modify: `install.bat:31-40` (Step 2 `.env` block)

- [ ] **Step 1: Modify the Step 2 block to add the interactive prompt**

Replace the block from Task 3 with:

```bat
if exist .env (
  echo   .env already exists, leaving alone.
) else (
  REM Ask the user whether to configure ANTHROPIC_API_KEY now (default = N).
  set "INTERACTIVE_ENV="
  set /p INTERACTIVE_ENV="  Configure ANTHROPIC_API_KEY interactively now? [y/N]: "

  copy /y .env.example .env >nul
  if errorlevel 1 goto :error

  REM Always regenerate SESSION_SECRET.
  for /f "delims=" %%I in ('conda run -n base python -c "import secrets; print(secrets.token_hex(32))"') do set "SESSION_SECRET_VAL=%%I"
  if not defined SESSION_SECRET_VAL goto :error

  if /i "!INTERACTIVE_ENV!"=="y" (
    set "API_KEY_VAL="
    set /p API_KEY_VAL="  Enter ANTHROPIC_API_KEY (Hyperspace key, leave empty to skip): "
    if defined API_KEY_VAL (
      conda run -n base python scripts\rewrite_env.py .env "SESSION_SECRET=!SESSION_SECRET_VAL!" "ANTHROPIC_API_KEY=!API_KEY_VAL!"
      if errorlevel 1 goto :error
      echo   .env created with provided ANTHROPIC_API_KEY and fresh SESSION_SECRET.
    ) else (
      conda run -n base python scripts\rewrite_env.py .env "SESSION_SECRET=!SESSION_SECRET_VAL!"
      if errorlevel 1 goto :error
      echo   .env created with placeholder ANTHROPIC_API_KEY ^(edit later^) and fresh SESSION_SECRET.
    )
  ) else (
    conda run -n base python scripts\rewrite_env.py .env "SESSION_SECRET=!SESSION_SECRET_VAL!"
    if errorlevel 1 goto :error
    echo   .env created from .env.example with a fresh SESSION_SECRET.
  )
)
```

- [ ] **Step 2: Verify the four behavior matrix scenarios on Windows (user verification)**

Ask the user to test each:

| # | Scenario | Setup | Action | Expected output |
|---|----------|-------|--------|-----------------|
| 1 | `.env` exists | leave it | run install.bat | `.env already exists, leaving alone.` |
| 2 | fresh, default-N | `del .env` | run, press Enter at prompt | `.env created from .env.example with a fresh SESSION_SECRET.` + placeholder API key |
| 3 | fresh, Y + key | `del .env` | run, type `y`, then `sk-test-123` | `.env created with provided ANTHROPIC_API_KEY...` + `ANTHROPIC_API_KEY=sk-test-123` |
| 4 | fresh, Y + empty | `del .env` | run, type `y`, then Enter (empty) | `.env created with placeholder ANTHROPIC_API_KEY...` + placeholder API key |

In all cases `.env` must contain a freshly-generated 64-char SESSION_SECRET.

- [ ] **Step 3: Commit**

```bash
git add install.bat
git commit -m "feat(install): optional interactive ANTHROPIC_API_KEY prompt"
```

---

## Task 5: Renumber steps 1-6 → 1-7 and update completion message

**Files:**
- Modify: `install.bat` (all `[N/6]` → `[N/7]` markers, completion message)

This is preparation for adding Step 7. Doing it as a standalone task keeps later diffs reviewable.

- [ ] **Step 1: Update step counters and completion message**

Replace each marker:

| Line | Old | New |
|------|-----|-----|
| Step 1 | `==^> [1/6] Checking for conda...` | `==^> [1/7] Checking for conda...` |
| Step 2 | `==^> [2/6] Scaffolding .env...` | `==^> [2/7] Scaffolding .env...` |
| Step 3 | `==^> [3/6] Creating sapcli-env...` | `==^> [3/7] Creating sapcli-env...` |
| Step 4 | `==^> [4/6] Installing sapcli...` | `==^> [4/7] Installing sapcli...` |
| Step 5 | `==^> [5/6] Installing MCP...` | `==^> [5/7] Installing MCP...` |
| Step 6 | `==^> [6/6] Installing web app...` | `==^> [6/7] Installing web app...` |

Replace the completion block at `install.bat:82-90`:

```bat
echo.
echo [OK] Install complete.
echo.
echo Next steps:
echo   1. If not yet edited: fill in .env        (ANTHROPIC_API_KEY = your Hyperspace API key, OIDC_*, BASE_URL).
echo   2. If not yet edited: fill in .sapcli.env  (SAP_ASHOST, SAP_PORT, SAP_CLIENT, SAP_PASSWORD).
echo   3. Start the server:
echo        conda run -n sapcli-env uvicorn app.main:app --reload
exit /b 0
```

with:

```bat
echo.
echo [OK] Install complete.
echo.
echo Next steps:
echo   1. If not yet edited: fill in .env        (ANTHROPIC_API_KEY = your Hyperspace API key, OIDC_*, BASE_URL).
echo   2. If not yet edited: fill in .sapcli.env  (SAP_ASHOST, SAP_PORT, SAP_CLIENT, SAP_PASSWORD).
echo   3. Open a NEW Anaconda Prompt ^(or cmd^) for env var changes ^(PYTHONUTF8, PATH, conda init^) to take effect.
echo   4. Start the server:
echo        conda run -n sapcli-env uvicorn app.main:app --reload
exit /b 0
```

- [ ] **Step 2: Verify on Windows (user verification)**

Run `install.bat`, confirm output shows `[1/7]` … `[6/7]` and the new completion message.

- [ ] **Step 3: Commit**

```bash
git add install.bat
git commit -m "chore(install): renumber steps to 1-7 and update completion message"
```

---

## Task 6: Add Step 7 — Windows user environment variables

**Files:**
- Modify: `install.bat` (insert before `:error` label, after Step 6)

- [ ] **Step 1: Insert Step 7 block**

Insert this block after the existing Step 6 (after line 80, `if errorlevel 1 goto :error`) and BEFORE the completion message added in Task 5:

```bat
REM Step 7 — Configure Windows user environment variables (best-effort)
echo.
echo ==^> [7/7] Configuring Windows user environment variables...

REM PYTHONUTF8=1 — only set if not already defined in the current shell
if not defined PYTHONUTF8 (
  setx PYTHONUTF8 1 >nul
  if errorlevel 1 (
    echo   WARNING: setx PYTHONUTF8=1 failed, skipping.
  ) else (
    echo   PYTHONUTF8=1 set ^(takes effect in new shells^).
  )
) else (
  echo   PYTHONUTF8 already defined, skipping.
)

REM Append sapcli-env\Scripts to user PATH if not already present
set "CONDA_BASE="
for /f "delims=" %%I in ('conda info --base 2^>nul') do set "CONDA_BASE=%%I"
if not defined CONDA_BASE (
  echo   WARNING: 'conda info --base' failed, cannot add sapcli-env to PATH. Skipping.
) else (
  set "SAPCLI_SCRIPTS=!CONDA_BASE!\envs\sapcli-env\Scripts"
  echo !PATH! | findstr /i /c:"!SAPCLI_SCRIPTS!" >nul
  if errorlevel 1 (
    REM Read user-level PATH from registry, NOT %PATH%
    set "USER_PATH="
    for /f "tokens=2,*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul ^| findstr /i "^    Path"') do set "USER_PATH=%%B"
    if defined USER_PATH (
      setx PATH "!USER_PATH!;!SAPCLI_SCRIPTS!" >nul
    ) else (
      setx PATH "!SAPCLI_SCRIPTS!" >nul
    )
    if errorlevel 1 (
      echo   WARNING: setx PATH failed. Add manually to user PATH: !SAPCLI_SCRIPTS!
    ) else (
      echo   Added !SAPCLI_SCRIPTS! to user PATH ^(takes effect in new shells^).
    )
  ) else (
    echo   sapcli-env Scripts already on PATH, skipping.
  )
)

```

- [ ] **Step 2: Verify on Windows (user verification — six scenarios)**

Ask the user to run `install.bat` once and report:

| Variable | Idempotency check |
|----------|-------------------|
| `PYTHONUTF8` | First run: `PYTHONUTF8=1 set (takes effect in new shells).` Re-run **in a new shell**: `PYTHONUTF8 already defined, skipping.` |
| `PATH` (sapcli-env) | First run: `Added <path>\Scripts to user PATH ...`. Re-run **in a new shell**: `sapcli-env Scripts already on PATH, skipping.` |

Then verify in a brand-new `cmd`:

```bat
echo %PYTHONUTF8%
where uvicorn
```

Expected: `1` and a path under `sapcli-env\Scripts\uvicorn.exe`.

If either WARNING fires, that's a valid soft-failure path; surface the exact warning text to ensure the manual remedy is correct.

- [ ] **Step 3: Commit**

```bash
git add install.bat
git commit -m "feat(install): add Step 7 to set PYTHONUTF8 and append sapcli-env to user PATH"
```

---

## Task 7: Add Step 1 conda bootstrap — probing, PATH repair, init, condarc hint

**Files:**
- Modify: `install.bat:8-25` (entire existing Step 1 block)

This task is last because it's the most likely to need iteration on the user's actual Windows setup, and it touches the script's prologue (any failure here blocks all subsequent verification).

- [ ] **Step 1: Replace Step 1 block**

Replace `install.bat:8-25` with:

```bat
REM Step 1 — locate conda; bootstrap fresh Miniconda installs (PATH, init, condarc)
echo.
echo ==^> [1/7] Checking for conda...

REM 1a. Fast path — conda already on PATH
set "CONDA_EXE="
for /f "delims=" %%I in ('where conda 2^>nul') do (
  set "CONDA_EXE=%%I"
  goto :_conda_found
)

REM 1b. Probe known install locations
for %%P in (
  "%USERPROFILE%\miniconda3\Scripts\conda.exe"
  "%USERPROFILE%\anaconda3\Scripts\conda.exe"
  "%LOCALAPPDATA%\miniconda3\Scripts\conda.exe"
  "%LOCALAPPDATA%\anaconda3\Scripts\conda.exe"
  "%PROGRAMDATA%\miniconda3\Scripts\conda.exe"
  "%PROGRAMDATA%\anaconda3\Scripts\conda.exe"
  "C:\ProgramData\Miniconda3\Scripts\conda.exe"
) do (
  if exist %%P (
    set "CONDA_EXE=%%~P"
    set "CONDA_FOUND_VIA_PROBE=1"
    goto :_conda_found
  )
)

echo.
echo ERROR: conda not found on PATH or in any known install location.
echo.
echo Install Miniconda from https://docs.anaconda.com/miniconda/, restart
echo your Anaconda Prompt or PowerShell so conda is on PATH, then re-run
echo install.bat.
exit /b 1

:_conda_found
echo   conda: !CONDA_EXE!

REM 1c. PATH repair — only if found via probing (not via 'where')
if defined CONDA_FOUND_VIA_PROBE (
  REM Strip \conda.exe to get the Scripts dir
  for %%P in ("!CONDA_EXE!") do set "CONDA_SCRIPTS_DIR=%%~dpP"
  REM %%~dpP includes a trailing backslash; strip it for cleanliness
  if "!CONDA_SCRIPTS_DIR:~-1!"=="\" set "CONDA_SCRIPTS_DIR=!CONDA_SCRIPTS_DIR:~0,-1!"

  set "USER_PATH="
  for /f "tokens=2,*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul ^| findstr /i "^    Path"') do set "USER_PATH=%%B"
  if defined USER_PATH (
    setx PATH "!USER_PATH!;!CONDA_SCRIPTS_DIR!" >nul
  ) else (
    setx PATH "!CONDA_SCRIPTS_DIR!" >nul
  )
  if errorlevel 1 (
    echo   WARNING: setx PATH failed; conda will work this run via direct path, but new shells may not see it.
  ) else (
    echo   Added !CONDA_SCRIPTS_DIR! to user PATH ^(takes effect in new shells^).
  )
)

REM 1d. conda init cmd.exe — detect via AutoRun registry value
reg query "HKCU\Software\Microsoft\Command Processor" /v AutoRun 2>nul | findstr /i "conda_hook" >nul
if errorlevel 1 (
  echo   Running 'conda init cmd.exe' ^(one-time setup^)...
  "!CONDA_EXE!" init cmd.exe >nul
  if errorlevel 1 (
    echo   WARNING: 'conda init cmd.exe' failed; you can run it manually later.
  )
) else (
  echo   conda init for cmd.exe already configured.
)

REM 1e. .condarc hint
if not exist "%USERPROFILE%\.condarc" (
  echo.
  echo   NOTE: No .condarc found. If pip/conda installs fail due to network
  echo   issues, you may need to configure a proxy or internal channel mirror.
  echo   See https://docs.conda.io/projects/conda/en/latest/user-guide/configuration/use-condarc.html
  echo.
)
```

**Important:** The rest of `install.bat` continues to use `conda` directly (e.g. `conda run -n base python ...`, `conda env list`, `conda create -n sapcli-env`). This works for all three cases:
1. conda was already on PATH (1a) — bare `conda` resolves.
2. conda was found via probing (1b) — `setx PATH` does NOT affect the current shell, so bare `conda` would fail. **For this run, the spec accepts that the user re-launches** — but to keep the current run usable, we additionally prepend `CONDA_SCRIPTS_DIR` to the in-shell `PATH`:

After the `setx PATH` block in 1c, add (still inside `if defined CONDA_FOUND_VIA_PROBE (...)`):

```bat
  REM Make conda usable in THIS shell session, not just future ones.
  set "PATH=!CONDA_SCRIPTS_DIR!;!PATH!"
```

This is a session-local in-process modification, distinct from the durable `setx`. It does not pollute beyond this `cmd` session.

- [ ] **Step 2: Verify on Windows (user verification — three scenarios)**

| Scenario | Setup | Expected |
|----------|-------|----------|
| A: conda on PATH | normal Anaconda Prompt | `conda: <path>` and no PATH/init/condarc messages other than possibly the .condarc hint |
| B: conda probed | open plain `cmd.exe` (not Anaconda Prompt) where `where conda` fails but Miniconda is in `%USERPROFILE%\miniconda3` | `conda: <path>` + `Added ... to user PATH` + `Running 'conda init cmd.exe'` (or "already configured" on second run) |
| C: not found | rename `%USERPROFILE%\miniconda3` temporarily | hard error with download link, exit 1 |

Critically: in scenario B, the rest of install.bat (Steps 2-7) must still complete without errors, because the in-shell `set PATH=...` ensures `conda` resolves for the current session.

- [ ] **Step 3: Commit**

```bash
git add install.bat
git commit -m "feat(install): bootstrap fresh Miniconda — probe paths, repair PATH, conda init, condarc hint"
```

---

## Task 8: Final integration verification

- [ ] **Step 1: Full run on Windows from a clean state (user verification)**

Ask the user to run, in this order on a Windows host:

1. `del .env .sapcli.env` (or test in a scratch directory)
2. `conda env remove -n sapcli-env -y` (if present)
3. Open a fresh `cmd.exe`
4. `install.bat`
5. At the API key prompt: type `y`, then a real (or test) ANTHROPIC_API_KEY
6. Confirm:
   - All 7 steps complete
   - `.env` has the supplied key + a fresh 64-hex SESSION_SECRET + other lines from `.env.example`
   - `.sapcli.env` matches `.sapcli.env.example`
   - Closing and re-opening `cmd.exe`, `echo %PYTHONUTF8%` returns `1`
   - In the new shell, `where uvicorn` resolves to `sapcli-env\Scripts\uvicorn.exe`
   - In the new shell, `conda activate sapcli-env` works (proves `conda init` ran)

- [ ] **Step 2: Re-run on Windows to confirm idempotency**

Run `install.bat` a second time on the same machine. Expected:

- `.env already exists, leaving alone.`
- `.sapcli.env already exists, leaving alone.`
- `sapcli-env already exists, skipping.`
- `PYTHONUTF8 already defined, skipping.`
- `sapcli-env Scripts already on PATH, skipping.`
- `conda init for cmd.exe already configured.`
- No new commits, no PATH duplication.

- [ ] **Step 3: No commit — verification only**

If everything passes, the work is complete. If anything fails, file the failure as feedback and return to the relevant task.

---

## Summary of Commits

| # | Type | Subject |
|---|------|---------|
| 1 | test | add failing tests for scripts/rewrite_env.py |
| 2 | feat | add scripts/rewrite_env.py for .env key rewrites |
| 3 | refactor | route SESSION_SECRET rewrite through rewrite_env.py |
| 4 | feat | optional interactive ANTHROPIC_API_KEY prompt |
| 5 | chore | renumber install.bat steps to 1-7 and update completion message |
| 6 | feat | add Step 7 to set PYTHONUTF8 and append sapcli-env to user PATH |
| 7 | feat | bootstrap fresh Miniconda — probe paths, repair PATH, conda init, condarc hint |
