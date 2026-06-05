# Early .env Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move `.env` / `.sapcli.env` scaffolding from Step 6 (last) to Step 2 (immediately after conda check) so users can edit config files while pip installs run.

**Architecture:** Edit `install.sh` and `install.bat` in place — move the scaffold block up, renumber all steps from 6 to 7, switch SECRET generation from `conda run -n sapcli-env python` to `python3` (sh) / `python` (bat) since sapcli-env doesn't exist yet at Step 2, and add an inline hint after scaffold completes.

**Tech Stack:** Bash, Windows batch (cmd)

---

## File Map

| File | Change |
|------|--------|
| `install.sh` | Move scaffold block to Step 2; renumber steps 2→3, 3→4, 4→5, 5→6; update `step()` total from 6→7; change SECRET generator to `python3`; add inline hint; update final message |
| `install.bat` | Same restructure; update all `[N/6]` to `[N/7]`; SECRET generator stays `python` (base env); add inline hint; update final message |

---

## Task 1: Rewrite `install.sh`

**Files:**
- Modify: `install.sh`

- [ ] **Step 1: Open the file and verify current content**

Confirm lines match what's expected (step total is `/6`, scaffold is near line 47).

- [ ] **Step 2: Rewrite `install.sh` with scaffold moved to Step 2**

Replace the entire file with:

```bash
#!/usr/bin/env bash
# One-click installer for iam-assistant on macOS / Linux.
# See docs/superpowers/specs/2026-06-01-one-click-installer-design.md.

set -euo pipefail

cd "$(dirname "$0")"

step() {
  printf '\n==> [%s/7] %s\n' "$1" "$2"
}

# Step 1 — verify conda is available
step 1 "Checking for conda..."
if ! command -v conda >/dev/null 2>&1; then
  cat <<'EOF'
ERROR: conda not found on PATH.

Install Miniconda from https://docs.anaconda.com/miniconda/, restart your
shell so conda is on PATH, then re-run ./install.sh.
EOF
  exit 1
fi
echo "  conda: $(command -v conda)"

# Step 2 — scaffold .env and .sapcli.env from templates (never overwrite)
step 2 "Scaffolding .env and .sapcli.env from templates..."

if [ -f .env ]; then
  echo "  .env already exists, leaving alone."
else
  cp .env.example .env
  secret="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
  python_inplace=$(cat <<'PY'
import sys
p = sys.argv[1]
secret = sys.argv[2]
with open(p) as f:
    lines = f.readlines()
with open(p, 'w') as f:
    for line in lines:
        if line.startswith('SESSION_SECRET='):
            f.write(f'SESSION_SECRET={secret}\n')
        else:
            f.write(line)
PY
)
  python3 -c "$python_inplace" .env "$secret"
  echo "  .env created from .env.example with a fresh SESSION_SECRET."
fi

if [ -f .sapcli.env ]; then
  echo "  .sapcli.env already exists, leaving alone."
else
  cp .sapcli.env.example .sapcli.env
  echo "  .sapcli.env created from .sapcli.env.example."
fi

echo ""
echo "  Tip: edit .env and .sapcli.env now while the install continues."

# Step 3 — create the sapcli-env conda environment if missing
step 3 "Creating sapcli-env conda environment (if missing)..."
if conda env list | awk '{print $1}' | grep -qx 'sapcli-env'; then
  echo "  sapcli-env already exists, skipping."
else
  conda create -n sapcli-env python=3.12 -y
fi

# Step 4 — install sapcli into sapcli-env
step 4 "Installing sapcli into sapcli-env..."
conda run -n sapcli-env pip install --quiet \
  git+https://github.com/jfilak/sapcli.git

# Step 5 — install MCP-server requirements
step 5 "Installing MCP server requirements..."
conda run -n sapcli-env pip install --quiet -r mcp-server/requirements.txt

# Step 6 — install web-app requirements
step 6 "Installing web app requirements..."
conda run -n sapcli-env pip install --quiet -r app/requirements.txt

cat <<'EOF'

✓ Install complete.

Next steps:
  1. If not yet edited: fill in .env       (ANTHROPIC_API_KEY, OIDC_*, BASE_URL).
  2. If not yet edited: fill in .sapcli.env (SAP_ASHOST, SAP_PORT, SAP_CLIENT, SAP_PASSWORD).
  3. Start the server:
       conda run -n sapcli-env uvicorn app.main:app --reload
EOF
```

- [ ] **Step 3: Verify the file is syntactically valid**

Run:
```bash
bash -n install.sh
```
Expected: no output (exit 0).

- [ ] **Step 4: Commit**

```bash
git add install.sh
git commit -m "feat(install): scaffold .env files at step 2, before pip installs"
```

---

## Task 2: Rewrite `install.bat`

**Files:**
- Modify: `install.bat`

- [ ] **Step 1: Rewrite `install.bat` with scaffold moved to Step 2**

Replace the entire file with:

```bat
@echo off
REM One-click installer for iam-assistant on Windows.
REM See docs\superpowers\specs\2026-06-01-one-click-installer-design.md.

setlocal enabledelayedexpansion
cd /d "%~dp0"

REM Step 1 — verify conda is available
echo.
echo ==^> [1/7] Checking for conda...
where conda >nul 2>&1
if errorlevel 1 (
  echo.
  echo ERROR: conda not found on PATH.
  echo.
  echo Install Miniconda from https://docs.anaconda.com/miniconda/, restart
  echo your Anaconda Prompt or PowerShell so conda is on PATH, then re-run
  echo install.bat.
  exit /b 1
)
for /f "delims=" %%I in ('where conda') do (
  echo   conda: %%I
  goto :_conda_ok
)
:_conda_ok

REM Step 2 — scaffold .env and .sapcli.env from templates
echo.
echo ==^> [2/7] Scaffolding .env and .sapcli.env from templates...

if exist .env (
  echo   .env already exists, leaving alone.
) else (
  copy /y .env.example .env >nul
  if errorlevel 1 goto :error
  REM Generate the secret AND rewrite the file in a single python invocation.
  python -c "import secrets; p='.env'; sec=secrets.token_hex(32); lines=open(p,encoding='utf-8').readlines(); open(p,'w',encoding='utf-8').writelines((f'SESSION_SECRET={sec}\n' if l.startswith('SESSION_SECRET=') else l) for l in lines)"
  if errorlevel 1 goto :error
  echo   .env created from .env.example with a fresh SESSION_SECRET.
)

if exist .sapcli.env (
  echo   .sapcli.env already exists, leaving alone.
) else (
  copy /y .sapcli.env.example .sapcli.env >nul
  if errorlevel 1 goto :error
  echo   .sapcli.env created from .sapcli.env.example.
)

echo.
echo   Tip: edit .env and .sapcli.env now while the install continues.

REM Step 3 — create the sapcli-env conda environment if missing
echo.
echo ==^> [3/7] Creating sapcli-env conda environment (if missing)...
conda env list | findstr /b /c:"sapcli-env " >nul
if errorlevel 1 (
  conda create -n sapcli-env python=3.12 -y
  if errorlevel 1 goto :error
) else (
  echo   sapcli-env already exists, skipping.
)

REM Step 4 — install sapcli
echo.
echo ==^> [4/7] Installing sapcli into sapcli-env...
conda run -n sapcli-env pip install --quiet git+https://github.com/jfilak/sapcli.git
if errorlevel 1 goto :error

REM Step 5 — install MCP-server requirements
echo.
echo ==^> [5/7] Installing MCP server requirements...
conda run -n sapcli-env pip install --quiet -r mcp-server\requirements.txt
if errorlevel 1 goto :error

REM Step 6 — install web-app requirements
echo.
echo ==^> [6/7] Installing web app requirements...
conda run -n sapcli-env pip install --quiet -r app\requirements.txt
if errorlevel 1 goto :error

echo.
echo [OK] Install complete.
echo.
echo Next steps:
echo   1. If not yet edited: fill in .env        (ANTHROPIC_API_KEY, OIDC_*, BASE_URL).
echo   2. If not yet edited: fill in .sapcli.env  (SAP_ASHOST, SAP_PORT, SAP_CLIENT, SAP_PASSWORD).
echo   3. Start the server:
echo        conda run -n sapcli-env uvicorn app.main:app --reload
exit /b 0

:error
echo.
echo ERROR: install.bat failed. The previous command's output above shows
echo why. Re-run install.bat after fixing the issue; completed steps will
echo skip themselves.
exit /b 1
```

- [ ] **Step 2: Verify step numbers are consistent**

Check that all `[N/7]` markers in the file go 1→2→3→4→5→6 with no gaps or duplicates:
```bash
grep -n "\[./7\]" install.bat
```
Expected output (6 lines):
```
10:echo ==^> [1/7] Checking for conda...
28:echo ==^> [2/7] Scaffolding .env and .sapcli.env from templates...
52:echo ==^> [3/7] Creating sapcli-env conda environment (if missing)...
61:echo ==^> [4/7] Installing sapcli into sapcli-env...
67:echo ==^> [5/7] Installing MCP server requirements...
73:echo ==^> [6/7] Installing web app requirements...
```

- [ ] **Step 3: Commit**

```bash
git add install.bat
git commit -m "feat(install): scaffold .env files at step 2, before pip installs (Windows)"
```

---

## Task 3: Verify `install.sh` step numbers

**Files:**
- Read: `install.sh`

- [ ] **Step 1: Check that all `[N/7]` markers in install.sh are consistent**

```bash
grep -n "\[./7\]" install.sh
```
Expected output (6 lines):
```
14:  printf '\n==> [%s/7] %s\n' "$1" "$2"
```
(The `step()` function uses `%s/7` as a format string — the individual step numbers are passed as arguments, so only one grep hit is expected here. Verify by also checking the step() call sites are 1–6.)

```bash
grep -n "^step " install.sh
```
Expected:
```
13:step 1 "Checking for conda..."
27:step 2 "Scaffolding .env and .sapcli.env from templates..."
...
step 3 ...
step 4 ...
step 5 ...
step 6 ...
```

- [ ] **Step 2: Commit spec reference update (if desired)**

The spec file already references the correct design. No further commits needed unless the spec file needs updating.
