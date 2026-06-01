# One-Click Installer — Design

**Date:** 2026-06-01
**Status:** Approved
**Audience:** New developer / analyst onboarding to `iam-assistant` on macOS or Windows.

## Problem

The current README walks new users through six manual steps to set up
`iam-assistant`: install conda, create the `sapcli-env` environment, install
`sapcli` from GitHub, install the MCP server requirements, install the web app
requirements, and write two secrets files (`.env`, `.sapcli.env`). This is
faithfully documented but error-prone — every onboarding hits the same friction
in the same order, and the failure modes (forgotten step, wrong directory,
unclear which `pip install` belongs in which env) are predictable.

A single command (`./install.sh` on macOS, `install.bat` on Windows) should
take a fresh checkout to a runnable state, leaving the user only the
irreducible step of filling in real secrets.

## Goals

1. One command, run from the repo root, brings a clean checkout to a state
   where the only remaining work is editing `.env` and `.sapcli.env` with real
   values and starting the server.
2. Re-running the script after a partial failure or after editing secrets does
   not destroy work or duplicate effort (idempotent).
3. The script is short enough that an experienced user can read it end-to-end
   and trust what it does.
4. Failures abort loudly, naming the step that failed and the underlying
   command, so the user knows where to resume manually.

## Non-goals (YAGNI)

- Auto-installing Miniconda. The script detects conda and aborts with a clear
  pointer to the Miniconda download page if it's missing. Auto-installing adds
  ~150MB of download, license prompts, sudo on macOS, and a corporate-network
  failure mode that doubles the script's complexity.
- Interactive secret prompts. Users rarely have all secrets to hand at install
  time, and prompts put passwords into shell scrollback. Template-copy is
  simpler and works in non-TTY contexts.
- Linux support. The macOS shell script will likely work unchanged on Linux,
  but Linux is not a declared platform.
- A `run.sh` / `run.bat` launcher. The existing one-line `uvicorn` invocation
  is short enough; we can add launcher scripts later if usage shows it
  matters.
- Validating `.env` contents at server startup. Pydantic Settings already
  raises clearly on missing required fields.
- An uninstaller. `conda env remove -n sapcli-env` is a one-liner.
- Automated tests of the installer beyond `shellcheck` (optional, not
  required).

## Approach

Two scripts at the repo root: `install.sh` (POSIX shell, `set -euo pipefail`)
and `install.bat` (Windows cmd). Each is a linear sequence of self-checking
steps. Per-platform divergence is irreducible — different shell, different
conda activation idioms, different file commands — so we accept the
duplication and don't try to factor a shared core.

A new template file `.sapcli.env.example` is committed to the repo so step 6
has something to copy from. (`.env.example` already exists.)

The README is rewritten so the quick-install path is the headline; the current
manual steps move verbatim into a new `docs/manual-setup.md` for users who
prefer the long form or whose installer fails.

### Considered alternatives

| Approach | Why not chosen |
|---|---|
| Single Python `tools/install.py` + 3-line shell wrappers | Chicken-and-egg: needs Python installed before conda is set up. macOS ships Python 3; Windows often does not. Removes one duplication but adds a fragile prerequisite. |
| Makefile / Justfile + thin platform bootstraps | Make is not standard on Windows and Just adds a tool dependency. The DRY win is small for six linear steps. |
| Self-contained shell installer that bundles Miniconda download | Doubles complexity; corporate networks frequently block anaconda.com. Out of scope per the goals. |

## What the installer does

| # | Step | macOS / Linux (`install.sh`) | Windows (`install.bat`) |
|---|---|---|---|
| 1 | Verify conda is on PATH | `command -v conda` → on miss, print Miniconda link and exit 1 | `where conda` → on miss, print Miniconda link and exit 1 |
| 2 | Create `sapcli-env` if missing | `conda env list \| grep -q '^sapcli-env ' \|\| conda create -n sapcli-env python=3.12 -y` | equivalent using `findstr` |
| 3 | Install sapcli into the env | `conda run -n sapcli-env pip install git+https://github.com/jfilak/sapcli.git` | same |
| 4 | Install MCP-server requirements | `conda run -n sapcli-env pip install -r mcp-server/requirements.txt` | same |
| 5 | Install web-app requirements | `conda run -n sapcli-env pip install -r app/requirements.txt` | same |
| 6 | Scaffold `.env` and `.sapcli.env` | If `.env` is missing, copy `.env.example` and replace the `SESSION_SECRET=...` line with a freshly generated 32-byte hex via `conda run -n sapcli-env python -c "import secrets; print(secrets.token_hex(32))"`. If `.sapcli.env` is missing, copy `.sapcli.env.example`. Skip each file with a friendly message if it already exists. | same logic, `copy` instead of `cp` |

Every step prints a banner before running so failures are easy to locate:

```
==> [3/6] Installing sapcli into sapcli-env...
```

The `cd "$(dirname "$0")"` (`%~dp0` on Windows) at the top of the script
ensures relative paths work regardless of the user's current directory.

## File: `.sapcli.env.example` (new)

This file is added to the repo as part of this work. Contents mirror the
README's existing block:

```bash
# ER6 connection settings — edit with real values, do not commit.
export SAP_HOST=<er6-hostname>
export SAP_PORT=<port>
export SAP_CLIENT=<client>
export SAP_USER=ANZEIGER
export SAP_PASSWORD=display
export SAP_SSL=true
```

`.gitignore` already excludes `.sapcli.env`, so the example file is the only
ER6-credentials artifact in version control.

## Failure modes

| Situation | Installer behavior |
|---|---|
| `conda` not on PATH | Print: "conda not found. Install Miniconda from https://docs.anaconda.com/miniconda/, restart your shell, then re-run this script." Exit 1. |
| Network failure during `pip install git+...` | pip's non-zero exit propagates. `set -euo pipefail` aborts the script. The banner names the failed step. User fixes network, re-runs — earlier steps are idempotent (env exists, packages cached). |
| User runs `install.sh` from a different directory | Script `cd`s to its own directory at the top so relative paths resolve. |
| `sapcli-env` already exists from a prior run | Step 2 skips creation. Pip install steps are no-ops if all packages are present. |
| `.env` or `.sapcli.env` already exists | Step 6 prints `→ .env already exists, leaving alone` and proceeds. Never overwrites user secrets. |

## README changes

The current macOS and Windows setup sections (steps 1–6 each) are replaced
with a short quick-install block:

> **Quick install:** From the project root, run `./install.sh` (macOS) or
> `install.bat` (Windows). Then edit `.env` and `.sapcli.env` with your real
> values, and start the server with
> `conda run -n sapcli-env uvicorn app.main:app --reload`.
>
> Conda must be installed first — see
> [Miniconda](https://docs.anaconda.com/miniconda/).
>
> **Manual setup** (if the installer fails or you prefer step-by-step):
> see [docs/manual-setup.md](docs/manual-setup.md).

`docs/manual-setup.md` is created by lifting the existing macOS and Windows
sections verbatim out of the README — no rewriting.

## Verification

Two manual checks before declaring done:

1. **Fresh-install path (macOS).** On a clean checkout in a fresh shell:
   `./install.sh` succeeds end-to-end; user edits `.env` and `.sapcli.env`
   with real values; `conda run -n sapcli-env uvicorn app.main:app --reload`
   starts the server at `http://localhost:8080` and the chat UI loads.
2. **Idempotent re-run (macOS).** Run `./install.sh` a second time on the
   same checkout. It skips env creation, skips file scaffolding, and finishes
   noticeably faster than the first run because pip recognizes every package
   as already-installed.

Windows path is verified by the user on a Windows machine; this design
defines the expected behavior but the author cannot test from macOS.

No automated tests are added. The installer is shell glue around documented
commands. Optional follow-up: `shellcheck install.sh` in CI.

## Out of scope, parking lot

- Apple Silicon vs Intel detection (conda already handles this).
- macOS code signing / notarization of the script (not a binary; not needed).
- Removing the `conda` dependency in favor of `python -m venv`. Worth
  revisiting if `sapcli` proves install-friendly outside conda; would also
  require updating `.mcp.json`.
- Auto-launching the server after install. Deferred — keeping install and
  run as separate steps lets the user edit secrets between them.
