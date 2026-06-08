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
  REM Ask the user whether to configure ANTHROPIC_API_KEY now (default = N).
  set "INTERACTIVE_ENV="
  set /p INTERACTIVE_ENV="  Configure ANTHROPIC_API_KEY interactively now? [y/N]: "

  copy /y .env.example .env >nul
  if errorlevel 1 goto :error

  REM Always regenerate SESSION_SECRET.
  set "SESSION_SECRET_VAL="
  for /f "delims=" %%I in ('conda run -n base python -c "import secrets; print(secrets.token_hex(32))"') do set "SESSION_SECRET_VAL=%%I"
  if not defined SESSION_SECRET_VAL goto :error

  if /i "!INTERACTIVE_ENV!"=="y" (
    set "API_KEY_VAL="
    set /p API_KEY_VAL="  Enter ANTHROPIC_API_KEY (Hyperspace key, leave empty to skip): "
    if defined API_KEY_VAL (
      REM API key assumed safe for delayed expansion (Hyperspace/sk- keys use [A-Za-z0-9_-] only; no !).
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
    REM Read user-level PATH from registry, NOT %PATH%, to avoid copying system PATH into user PATH.
    set "USER_PATH="
    for /f "tokens=2,*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul ^| findstr /i "^    Path"') do set "USER_PATH=%%B"
    REM Compute proposed combined length and skip if > 1000 chars (setx silently truncates at 1024).
    if defined USER_PATH (
      set "NEW_USER_PATH=!USER_PATH!;!SAPCLI_SCRIPTS!"
    ) else (
      set "NEW_USER_PATH=!SAPCLI_SCRIPTS!"
    )
    call :_pathlen "!NEW_USER_PATH!" NEW_USER_PATH_LEN
    if !NEW_USER_PATH_LEN! gtr 1000 (
      echo   WARNING: combined user PATH would be !NEW_USER_PATH_LEN! chars ^(setx truncates at 1024^).
      echo            Skipping setx to avoid silent truncation. Add manually: !SAPCLI_SCRIPTS!
    ) else (
      setx PATH "!NEW_USER_PATH!" >nul
      if errorlevel 1 (
        echo   WARNING: setx PATH failed. Add manually to user PATH: !SAPCLI_SCRIPTS!
      ) else (
        echo   Added !SAPCLI_SCRIPTS! to user PATH ^(takes effect in new shells^).
      )
    )
  ) else (
    echo   sapcli-env Scripts already on PATH, skipping.
  )
)

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

:error
echo.
echo ERROR: install.bat failed. The previous command's output above shows
echo why. Re-run install.bat after fixing the issue; completed steps will
echo skip themselves.
exit /b 1

REM Helper: compute the length of a string into a variable.
REM Usage: call :_pathlen "the string" RESULT_VAR_NAME
:_pathlen
setlocal enabledelayedexpansion
set "_str=%~1"
set _len=0
:_pathlen_loop
if defined _str (
  set "_str=!_str:~1!"
  set /a _len+=1
  goto :_pathlen_loop
)
endlocal & set "%~2=%_len%"
exit /b 0
