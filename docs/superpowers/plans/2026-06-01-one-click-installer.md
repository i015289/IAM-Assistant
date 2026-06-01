# One-Click Installer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a single-command installer for `iam-assistant` (`./install.sh` on macOS, `install.bat` on Windows) that takes a fresh checkout to a runnable state, leaving only secrets to fill in.

**Architecture:** Two linear shell scripts at the repo root (no shared core, divergence is irreducible). Each performs six idempotent steps: verify conda, create `sapcli-env`, install sapcli, install MCP-server requirements, install web-app requirements, scaffold `.env` and `.sapcli.env` from committed templates. README is split: a quick-install header + a moved-verbatim `docs/manual-setup.md`.

**Tech Stack:** POSIX shell (`set -euo pipefail`), Windows cmd (`%ERRORLEVEL%` checks), conda, pip. No new Python dependencies.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `install.sh` | Create | macOS / Linux installer — six linear steps |
| `install.bat` | Create | Windows installer — same six steps in cmd syntax |
| `.sapcli.env.example` | Create | POSIX-format ER6 connection template; parsed directly by MCP server, not sourced by shell, so `export` syntax is correct on both platforms |
| `docs/manual-setup.md` | Create | Verbatim lift of the current README's macOS + Windows setup sections |
| `README.md` | Modify | Replace the macOS/Windows setup sections (currently lines ~62–245) with a short quick-install block linking to `docs/manual-setup.md` |

**Important note about `.sapcli.env.example`:**
`mcp-server/er6_mcp_server.py:26` parses `.sapcli.env` itself by looking for lines that start with `export `. The current README's Windows instructions tell users to write `set KEY=VALUE` — those lines are silently ignored. The fix is part of the docs split: the new `docs/manual-setup.md` will keep `export` syntax for Windows too, and the installer always copies the same POSIX-format template on both platforms. We do NOT change the MCP server. The README's existing `call .sapcli.env` line in the Windows section is actively misleading and we replace it.

---

## Task 1: Create the `.sapcli.env.example` template

**Files:**
- Create: `.sapcli.env.example`

- [ ] **Step 1: Write the template file**

Create `.sapcli.env.example` with this exact content:

```bash
# ER6 connection settings — edit with real values, do not commit.
# Format: POSIX `export KEY=VALUE`. The MCP server parses this file directly
# (mcp-server/er6_mcp_server.py), so this syntax is correct on Windows too —
# do not change `export` to `set`.
export SAP_HOST=<er6-hostname>
export SAP_PORT=<port>
export SAP_CLIENT=<client>
export SAP_USER=ANZEIGER
export SAP_PASSWORD=display
export SAP_SSL=true
```

- [ ] **Step 2: Verify `.gitignore` already excludes `.sapcli.env`**

Run: `grep -n '^\.sapcli\.env$' .gitignore`
Expected: `2:.sapcli.env` (or similar non-empty match). If missing, stop and add it; otherwise the example file would be the only thing tracked while real secrets stayed local — fine, but confirming the existing exclusion makes the chain auditable.

- [ ] **Step 3: Confirm the example file IS tracked (not excluded by a wildcard)**

Run: `git check-ignore .sapcli.env.example; echo "exit=$?"`
Expected: `exit=1` (i.e. NOT ignored — `.gitignore` line is `.sapcli.env` exact, not `.sapcli.env*`). If the exit code is 0, the example is ignored too — stop and adjust `.gitignore` to `/.sapcli.env` (anchored) before continuing.

- [ ] **Step 4: Commit**

```bash
git add .sapcli.env.example
git commit -m "feat: add .sapcli.env.example template for installer"
```

---

## Task 2: Create the macOS / Linux installer (`install.sh`)

**Files:**
- Create: `install.sh`

- [ ] **Step 1: Write the script**

Create `install.sh` at the repo root with this exact content:

```bash
#!/usr/bin/env bash
# One-click installer for iam-assistant on macOS / Linux.
# See docs/superpowers/specs/2026-06-01-one-click-installer-design.md.

set -euo pipefail

cd "$(dirname "$0")"

step() {
  printf '\n==> [%s/6] %s\n' "$1" "$2"
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

# Step 2 — create the sapcli-env conda environment if missing
step 2 "Creating sapcli-env conda environment (if missing)..."
if conda env list | awk '{print $1}' | grep -qx 'sapcli-env'; then
  echo "  sapcli-env already exists, skipping."
else
  conda create -n sapcli-env python=3.12 -y
fi

# Step 3 — install sapcli into sapcli-env
step 3 "Installing sapcli into sapcli-env..."
conda run -n sapcli-env pip install --quiet \
  git+https://github.com/jfilak/sapcli.git

# Step 4 — install MCP-server requirements
step 4 "Installing MCP server requirements..."
conda run -n sapcli-env pip install --quiet -r mcp-server/requirements.txt

# Step 5 — install web-app requirements
step 5 "Installing web app requirements..."
conda run -n sapcli-env pip install --quiet -r app/requirements.txt

# Step 6 — scaffold .env and .sapcli.env from templates (never overwrite)
step 6 "Scaffolding .env and .sapcli.env from templates..."

if [ -f .env ]; then
  echo "  .env already exists, leaving alone."
else
  cp .env.example .env
  secret="$(conda run -n sapcli-env python -c \
    'import secrets; print(secrets.token_hex(32))')"
  # Replace the placeholder SESSION_SECRET line. Use a delimiter unlikely to
  # appear in a hex token.
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
  conda run -n sapcli-env python -c "$python_inplace" .env "$secret"
  echo "  .env created from .env.example with a fresh SESSION_SECRET."
fi

if [ -f .sapcli.env ]; then
  echo "  .sapcli.env already exists, leaving alone."
else
  cp .sapcli.env.example .sapcli.env
  echo "  .sapcli.env created from .sapcli.env.example."
fi

cat <<'EOF'

✓ Install complete.

Next steps:
  1. Edit .env           (fill in ANTHROPIC_API_KEY, OIDC_*, BASE_URL).
  2. Edit .sapcli.env    (fill in SAP_HOST, SAP_PORT, SAP_CLIENT, SAP_PASSWORD).
  3. Start the server:
       conda run -n sapcli-env uvicorn app.main:app --reload
EOF
```

- [ ] **Step 2: Make it executable**

Run: `chmod +x install.sh`

- [ ] **Step 3: Run it on the current checkout (which already has sapcli-env, .env, .sapcli.env from prior work)**

Run: `./install.sh`
Expected: Exits 0. Step 2 reports `sapcli-env already exists, skipping`. Step 6 reports both `.env already exists, leaving alone` and `.sapcli.env already exists, leaving alone`. Steps 3–5 are pip no-ops (each line ends with "Requirement already satisfied" — quiet mode hides routine output but errors still surface).

- [ ] **Step 4: Verify exit code**

Run: `./install.sh && echo OK`
Expected: trailing `OK` on a successful run.

- [ ] **Step 5: Commit**

```bash
git add install.sh
git commit -m "feat: add install.sh one-click installer for macOS/Linux"
```

---

## Task 3: Create the Windows installer (`install.bat`)

**Files:**
- Create: `install.bat`

- [ ] **Step 1: Write the script**

Create `install.bat` at the repo root with this exact content. Note the Windows-specific differences from `install.sh`:
- `cd /d "%~dp0"` to anchor working dir (handles different drive)
- `where conda` for presence check
- `findstr /b /c:"sapcli-env "` for env detection
- `if errorlevel 1 goto :error` after every external command
- `copy /y NUL .env >NUL` is NOT used — we use `copy "src" "dst"` and `if exist`
- `python -c` lines use double quotes (cmd's outer quotes); inner Python uses single quotes

```batch
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
  conda run -n sapcli-env python -c "import secrets, sys; p='.env'; sec=secrets.token_hex(32); lines=open(p).readlines(); open(p,'w').writelines((f'SESSION_SECRET={sec}\n' if l.startswith('SESSION_SECRET=') else l) for l in lines)"
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
echo ^✓ Install complete.
echo.
echo Next steps:
echo   1. Edit .env           (fill in ANTHROPIC_API_KEY, OIDC_*, BASE_URL).
echo   2. Edit .sapcli.env    (fill in SAP_HOST, SAP_PORT, SAP_CLIENT, SAP_PASSWORD).
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

- [ ] **Step 2: Static syntax check**

Windows cmd has no native linter; the best we can do is read it. Re-read the script carefully looking for:
- Every `conda run`, `copy`, `pip install` is followed by `if errorlevel 1 goto :error` (no command silently swallows a failure).
- The Python one-liners use double quotes for cmd's outer string and single quotes for Python's strings; backslashes in the f-string `\n` pass through cmd unchanged.
- `setlocal enabledelayedexpansion` is at the top — harmless even though we no longer need `!VAR!` style expansion (an earlier draft did). Leave it; future maintainers may add a variable that needs it.

If any of those is wrong, fix the file before continuing. Otherwise proceed.

- [ ] **Step 3: Commit**

```bash
git add install.bat
git commit -m "feat: add install.bat one-click installer for Windows"
```

---

## Task 4: Create `docs/manual-setup.md` (verbatim lift)

**Files:**
- Create: `docs/manual-setup.md`

- [ ] **Step 1: Lift the current README setup sections verbatim**

The content to lift is README.md lines 53–245 (from `## Setup` through the end of the Windows section, inclusive — stops before `## Running Queries`). Use `sed` to extract:

Run:
```bash
sed -n '53,245p' README.md > docs/manual-setup.md
```

- [ ] **Step 2: Convert the file's top-level headings**

The lifted block uses `## Setup` as its top heading and `### Setup — macOS` / `### Setup — Windows` as subsections. In a standalone doc, those should each promote one level. Open `docs/manual-setup.md` and:

1. Change `## Setup` (first line) to `# Manual Setup`.
2. Change `### Setup — macOS` to `## Setup — macOS`.
3. Change `### Setup — Windows` to `## Setup — Windows`.
4. Convert every `#### N. Foo` to `### N. Foo` (one level shallower).

The exact `sed` to run all four conversions safely — anchored to start-of-line and only the precise headings, so it won't catch other `#` characters in code blocks:

```bash
sed -i '' \
  -e '1s/^## Setup$/# Manual Setup/' \
  -e 's/^### Setup — macOS$/## Setup — macOS/' \
  -e 's/^### Setup — Windows$/## Setup — Windows/' \
  -e 's/^#### \([1-9]\)\. /### \1. /' \
  docs/manual-setup.md
```

(macOS BSD sed needs the empty `''` after `-i`; on Linux drop it. The plan author is on macOS so the command above works as written.)

- [ ] **Step 3: Fix the in-doc TOC links at the top**

The lifted snippet contains:
```markdown
- [Setup — macOS](#setup--macos)
- [Setup — Windows](#setup--windows)
```
GitHub auto-anchor lowercases and replaces spaces with `-`. After Step 2, the headings are still `Setup — macOS` and `Setup — Windows`, so the same anchors `#setup--macos` and `#setup--windows` still resolve. No edit needed; just verify by visual scan after Step 2.

- [ ] **Step 4: Append a "Why this exists" header note at the very top**

Prepend a one-line callout pointing back to the README's quick-install path. Run:

```bash
{
  printf '> If you'\''d rather run one command, see the **Quick install** block in [README.md](../README.md). This document is the long-form alternative for users who hit problems with the installer or prefer to do each step by hand.\n\n'
  cat docs/manual-setup.md
} > docs/manual-setup.md.tmp
mv docs/manual-setup.md.tmp docs/manual-setup.md
```

Verify: `head -3 docs/manual-setup.md` shows the blockquote on line 1, a blank on line 2, and `# Manual Setup` on line 3.

- [ ] **Step 5: Commit**

```bash
git add docs/manual-setup.md
git commit -m "docs: extract manual setup steps to docs/manual-setup.md"
```

---

## Task 5: Replace README setup sections with a quick-install block

**Files:**
- Modify: `README.md` lines 53–245 (the entire `## Setup` block including both OS subsections)

- [ ] **Step 1: Verify the block bounds**

Run: `awk 'NR==53 || NR==245 || NR==246 {printf "%d: %s\n", NR, $0}' README.md`
Expected output:
```
53: ## Setup
245: 
246: ## Running Queries
```
That is, line 53 starts the Setup block and line 246 (the line AFTER our cut) is the next major heading `## Running Queries`. Line 245 is the trailing blank inside the Windows section. If those landmarks shift (because the README was edited since this plan was written), find the new boundary lines and substitute them in Step 2 below before running the replacement.

- [ ] **Step 2: Replace the block**

Use this sed to delete lines 53–245 and insert the new block in their place. Run:

```bash
# Step 2a: extract head and tail
head -n 52 README.md > /tmp/readme.head
tail -n +246 README.md > /tmp/readme.tail

# Step 2b: write the new quick-install block to a temp file
cat > /tmp/readme.middle <<'EOF'
## Setup

**Quick install:** From the project root, run:

```bash
./install.sh         # macOS / Linux
install.bat          # Windows (Anaconda Prompt or PowerShell)
```

Then edit `.env` and `.sapcli.env` with your real values, and start the server:

```bash
conda run -n sapcli-env uvicorn app.main:app --reload
```

**Prerequisite:** conda must be installed first. The installer aborts with a link if it can't find conda. See [Miniconda](https://docs.anaconda.com/miniconda/).

**Manual setup** (if the installer fails or you prefer step-by-step instructions): see [docs/manual-setup.md](docs/manual-setup.md).

EOF

# Step 2c: stitch and replace
cat /tmp/readme.head /tmp/readme.middle /tmp/readme.tail > README.md
rm /tmp/readme.head /tmp/readme.middle /tmp/readme.tail
```

- [ ] **Step 3: Verify the result**

Run: `sed -n '50,80p' README.md`
Expected: shows the end of the Prerequisites table, the new `## Setup` block ending with the link to `docs/manual-setup.md`, and the start of `## Running Queries`. No leftover lines from the old steps.

Run: `grep -n '^## ' README.md | head -10`
Expected: `## Setup` appears exactly once. No `### Setup — macOS` or `### Setup — Windows` remains.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: replace README setup sections with quick-install block"
```

---

## Task 6: Verification — fresh-install simulation

The committer machine already has `sapcli-env`, `.env`, and `.sapcli.env` from prior work, so a true cold install can't be done in place without destroying that state. Two complementary checks instead:

- [ ] **Step 1: Idempotent re-run**

Run: `./install.sh`
Expected output (key lines):
```
==> [1/6] Checking for conda...
==> [2/6] Creating sapcli-env conda environment (if missing)...
  sapcli-env already exists, skipping.
==> [3/6] Installing sapcli into sapcli-env...
==> [4/6] Installing MCP server requirements...
==> [5/6] Installing web app requirements...
==> [6/6] Scaffolding .env and .sapcli.env from templates...
  .env already exists, leaving alone.
  .sapcli.env already exists, leaving alone.
✓ Install complete.
```
Exit code 0. No file modifications (verify with `git status`: working tree should be unchanged for tracked files; `__pycache__` churn from running uvicorn elsewhere is fine).

- [ ] **Step 2: Cold-install simulation in a fresh git worktree**

To simulate a cold install without touching the active checkout, do it in a worktree pointed at this branch:

```bash
git worktree add /tmp/iam-cold "$(git branch --show-current)"
cd /tmp/iam-cold
# .env / .sapcli.env are gitignored, so the worktree starts without them.
test ! -f .env && test ! -f .sapcli.env && echo "fresh secrets state OK"
# But sapcli-env is conda-global, not per-checkout — so step 2 of install.sh
# will still see it as already-existing. That's fine; we're verifying step 6.
./install.sh
test -f .env && grep -q '^SESSION_SECRET=[0-9a-f]\{64\}$' .env && echo "fresh .env has 64-hex SESSION_SECRET"
test -f .sapcli.env && echo "fresh .sapcli.env created"
cd -
git worktree remove /tmp/iam-cold
```

Expected: the three echo lines all print. If `SESSION_SECRET` does not match the 64-hex pattern, the in-place rewrite logic in step 6 of `install.sh` is broken.

- [ ] **Step 3: README link integrity**

Run: `test -f docs/manual-setup.md && grep -q 'Manual Setup' docs/manual-setup.md && echo OK`
Expected: `OK`.

Run: `grep -c 'docs/manual-setup.md' README.md`
Expected: `1` (or more — exactly one is the design intent, but two would only happen if you forgot to delete the old block; the heading-count check in Task 5 Step 3 catches that).

- [ ] **Step 4: Quick smoke that the conda env still launches the server**

```bash
if lsof -i :8080 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "8080 already in use; smoke skipped (existing server probably from earlier turn)."
  curl -fsS -o /dev/null -w "%{http_code}\n" http://localhost:8080/
else
  conda run -n sapcli-env uvicorn app.main:app --port 8080 >/tmp/iam-smoke.log 2>&1 &
  pid=$!
  sleep 4
  curl -fsS -o /dev/null -w "%{http_code}\n" http://localhost:8080/
  kill "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
fi
```

Expected: a single `200` line printed by curl. Any other response (000 = couldn't connect, 4xx, 5xx) means the conda env or the app code is broken and the install machinery itself is fine but downstream is not — investigate `/tmp/iam-smoke.log` if the server failed to start.

- [ ] **Step 5: No commit needed for verification**

This task only checks behavior; nothing to commit. If any check failed, return to the relevant earlier task and fix.

---

## Task 7: Optional polish — `shellcheck`

This task is optional. Skip if `shellcheck` is not installed.

- [ ] **Step 1: Run shellcheck on `install.sh`**

Run: `shellcheck install.sh`
Expected: no warnings. Common false positives in this script:
- `SC2046` (word splitting on unquoted command substitution) — not applicable; we always quote.
- `SC2155` (declare and assign separately) — applies to `secret="$(...)"` inside an `if`. Acceptable here since the script aborts on `set -e` if the substitution fails.

If shellcheck reports anything else, fix it.

- [ ] **Step 2: Commit (only if changes were needed)**

```bash
git add install.sh
git commit -m "fix: address shellcheck warnings in install.sh"
```

---

## Self-Review

**Spec coverage** — every spec section has at least one task:

| Spec section | Implementing task |
|---|---|
| Goals 1–4 (one command, idempotent, short, loud failures) | Tasks 2 & 3 |
| Approach (two scripts, irreducible duplication, new template, README split) | Tasks 1, 2, 3, 4, 5 |
| Step 1: detect conda | Task 2 step 1 (sh) / Task 3 step 1 (bat) |
| Steps 2–5: env + pip installs | Task 2 / Task 3 |
| Step 6: scaffold secrets | Task 2 / Task 3, with SESSION_SECRET regen verified in Task 6 step 2 |
| `.sapcli.env.example` (new file) | Task 1 |
| Failure modes table | Task 2/3 (`set -euo pipefail` + `goto :error`); Task 6 step 1 (idempotent re-run) |
| README rewrite + manual-setup.md | Tasks 4 & 5 |
| Verification (fresh install, idempotent re-run) | Task 6 |
| Non-goals (no Miniconda autoinstall, no interactive prompts, no Linux script, no run.sh) | Honored — no tasks for them |

**Discovery beyond the spec:** the spec assumed `.sapcli.env` syntax was platform-specific. Inspection of `mcp-server/er6_mcp_server.py:26` showed it parses `export KEY=VALUE` itself on both platforms, so a single template suffices. This is reflected in Task 1's template content and the Important note in the File Map. No spec change is required — the spec said "copy `.sapcli.env.example` on both OSes," and now there's a real file with the right syntax to copy.

**Placeholder scan:** none. Every code block is complete and runnable; every step has a concrete command and expected output.

**Type / name consistency:** `sapcli-env` everywhere, `.sapcli.env` (no hyphen) everywhere, `.env.example`/`.sapcli.env.example` consistent, `install.sh` / `install.bat` consistent. Step numbering 1–6 in both scripts and matches the spec table.

---

## Out of plan, parking lot

(Mirrors the spec's parking lot — surfaced here for the executor's awareness.)

- Apple Silicon vs Intel detection — conda handles it.
- macOS notarization — script, not binary.
- `python -m venv` migration — needs `.mcp.json` rewrite too.
- Auto-launch the server — keeping install and run separate lets the user edit secrets between them.
- Linux script — macOS script will likely run on Linux unchanged, but Linux is not declared.
