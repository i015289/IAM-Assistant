@echo off
REM One-click installer for iam-assistant on Windows.
REM See docs\superpowers\specs\2026-06-01-one-click-installer-design.md.

setlocal enabledelayedexpansion
cd /d "%~dp0"

REM Step 1 — verify conda is available
echo.
echo ==^> [1/6] Checking for conda...
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
echo ==^> [2/6] Scaffolding .env and .sapcli.env from templates...

if exist .env (
  echo   .env already exists, leaving alone.
) else (
  copy /y .env.example .env >nul
  if errorlevel 1 goto :error
  REM Generate SESSION_SECRET and rewrite the file via scripts\rewrite_env.py.
  set "SESSION_SECRET_VAL="
  for /f "delims=" %%I in ('conda run -n base python -c "import secrets; print(secrets.token_hex(32))"') do set "SESSION_SECRET_VAL=%%I"
  if not defined SESSION_SECRET_VAL goto :error
  conda run -n base python scripts\rewrite_env.py .env "SESSION_SECRET=!SESSION_SECRET_VAL!"
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
echo ==^> [3/6] Creating sapcli-env conda environment (if missing)...
conda env list | findstr /b /c:"sapcli-env " >nul
if errorlevel 1 (
  conda create -n sapcli-env python=3.12 -y
  if errorlevel 1 goto :error
) else (
  echo   sapcli-env already exists, skipping.
)

REM Step 4 — install sapcli
echo.
echo ==^> [4/6] Installing sapcli into sapcli-env...
conda run -n sapcli-env pip install --quiet git+https://github.com/jfilak/sapcli.git
if errorlevel 1 goto :error

REM Step 5 — install MCP-server requirements
echo.
echo ==^> [5/6] Installing MCP server requirements...
conda run -n sapcli-env pip install --quiet -r mcp-server\requirements.txt
if errorlevel 1 goto :error

REM Step 6 — install web-app requirements
echo.
echo ==^> [6/6] Installing web app requirements...
conda run -n sapcli-env pip install --quiet -r app\requirements.txt
if errorlevel 1 goto :error

echo.
echo [OK] Install complete.
echo.
echo Next steps:
echo   1. If not yet edited: fill in .env        (ANTHROPIC_API_KEY = your Hyperspace API key, OIDC_*, BASE_URL).
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
