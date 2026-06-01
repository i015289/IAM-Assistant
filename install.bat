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

REM Step 2 — create the sapcli-env conda environment if missing
echo.
echo ==^> [2/6] Creating sapcli-env conda environment (if missing)...
conda env list | findstr /b /c:"sapcli-env " >nul
if errorlevel 1 (
  conda create -n sapcli-env python=3.12 -y
  if errorlevel 1 goto :error
) else (
  echo   sapcli-env already exists, skipping.
)

REM Step 3 — install sapcli
echo.
echo ==^> [3/6] Installing sapcli into sapcli-env...
conda run -n sapcli-env pip install --quiet git+https://github.com/jfilak/sapcli.git
if errorlevel 1 goto :error

REM Step 4 — install MCP-server requirements
echo.
echo ==^> [4/6] Installing MCP server requirements...
conda run -n sapcli-env pip install --quiet -r mcp-server\requirements.txt
if errorlevel 1 goto :error

REM Step 5 — install web-app requirements
echo.
echo ==^> [5/6] Installing web app requirements...
conda run -n sapcli-env pip install --quiet -r app\requirements.txt
if errorlevel 1 goto :error

REM Step 6 — scaffold .env and .sapcli.env from templates
echo.
echo ==^> [6/6] Scaffolding .env and .sapcli.env from templates...

if exist .env (
  echo   .env already exists, leaving alone.
) else (
  copy /y .env.example .env >nul
  if errorlevel 1 goto :error
  REM Generate the secret AND rewrite the file in a single python invocation —
  REM avoids cmd `for /f` quoting hazards entirely.
  conda run -n sapcli-env python -c "import secrets; p='.env'; sec=secrets.token_hex(32); lines=open(p,encoding='utf-8').readlines(); open(p,'w',encoding='utf-8').writelines((f'SESSION_SECRET={sec}\n' if l.startswith('SESSION_SECRET=') else l) for l in lines)"
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
echo [OK] Install complete.
echo.
echo Next steps:
echo   1. Edit .env           (fill in ANTHROPIC_API_KEY, OIDC_*, BASE_URL).
echo   2. Edit .sapcli.env    (fill in SAP_ASHOST, SAP_PORT, SAP_CLIENT, SAP_PASSWORD).
echo   3. Start the server:
echo        conda run -n sapcli-env uvicorn app.main:app --reload
exit /b 0

:error
echo.
echo ERROR: install.bat failed. The previous command's output above shows
echo why. Re-run install.bat after fixing the issue; completed steps will
echo skip themselves.
exit /b 1
