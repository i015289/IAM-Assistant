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
  # Rewrite the SESSION_SECRET line in-place via an embedded Python program
  # (passed through stdin via heredoc) — sed is awkward for line-prefix
  # replacement and would force us to escape the secret.
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
