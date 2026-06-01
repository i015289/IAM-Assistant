> If you'd rather run one command, see the **Quick install** block in [README.md](../README.md). This document is the long-form alternative for users who hit problems with the installer or prefer to do each step by hand.

# Manual Setup

Pick the section matching your operating system:

- [Setup — macOS](#setup--macos)
- [Setup — Windows](#setup--windows)

---

## Setup — macOS

### 1. Install conda (Miniconda)

If conda is not already installed, install Miniconda. The Apple Silicon (`arm64`) installer is recommended for M1/M2/M3 Macs; use `x86_64` for Intel Macs.

```bash
# Apple Silicon (M1/M2/M3)
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh
bash Miniconda3-latest-MacOSX-arm64.sh

# Intel Macs
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
bash Miniconda3-latest-MacOSX-x86_64.sh
```

Follow the installer prompts, then restart your shell (or `source ~/.zshrc`). Verify:

```bash
conda --version
```

> **Alternative:** `brew install --cask miniconda` if you use Homebrew.

### 2. Install sapcli

sapcli is the SAP CLI tool that provides the underlying connectivity to ER6. It runs inside a dedicated conda environment.

```bash
# Create a dedicated conda environment with Python 3.12
conda create -n sapcli-env python=3.12 -y

# Activate the environment
conda activate sapcli-env

# Install sapcli from GitHub
pip install git+https://github.com/jfilak/sapcli.git

# Verify installation
sapcli --version
```

> **Source:** [https://github.com/jfilak/sapcli](https://github.com/jfilak/sapcli)

### 3. Configure ER6 connection

Create a `.sapcli.env` file in the project root (not committed to source control):

```bash
export SAP_HOST=<er6-hostname>
export SAP_PORT=<port>
export SAP_CLIENT=<client>
export SAP_USER=ANZEIGER
export SAP_PASSWORD=display
export SAP_SSL=true
```

Test connectivity:

```bash
source .sapcli.env && conda run -n sapcli-env sapcli datapreview osql "SELECT DEVCLASS FROM TDEVC UP TO 1 ROWS"
```

### 4. Clone / open the project in Claude Code

```bash
claude /Users/<you>/Joule_Workspace/iam-assistant
```

### 5. Install the MCP ER6 server

```bash
conda run -n sapcli-env pip install -r mcp-server/requirements.txt
```

The server script is `mcp-server/er6_mcp_server.py` and is already wired up in `.mcp.json` using a relative path — no path editing required:

```json
{
  "mcpServers": {
    "er6": {
      "command": "conda",
      "args": ["run", "--no-capture-output", "-n", "sapcli-env",
               "python", "./mcp-server/er6_mcp_server.py"]
    }
  }
}
```

### 6. Verify MCP connectivity

Claude Code will use the `er6` MCP tools automatically when the server is configured in `.mcp.json`. Start Claude Code and run a test query to confirm.

---

## Setup — Windows

> Run all commands in **Anaconda Prompt** (or PowerShell once conda is on `PATH`). Forward slashes in JSON paths are fine on Windows; backslashes must be escaped (`\\`).

### 1. Install conda (Miniconda)

If conda is not already installed, download and install Miniconda for Windows:

1. Download the installer: <https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe>
2. Run the installer. Accept the defaults — when prompted, install for "Just Me" and let the installer register Miniconda as the default Python.
3. Open **Anaconda Prompt** from the Start menu.

Verify:

```cmd
conda --version
```

> **Alternative:** `winget install Anaconda.Miniconda3`.

### 2. Install sapcli

```cmd
:: Create a dedicated conda environment with Python 3.12
conda create -n sapcli-env python=3.12 -y

:: Activate the environment
conda activate sapcli-env

:: Install sapcli from GitHub (requires git — install from https://git-scm.com if missing)
pip install git+https://github.com/jfilak/sapcli.git

:: Verify installation
sapcli --version
```

> **Source:** [https://github.com/jfilak/sapcli](https://github.com/jfilak/sapcli)

### 3. Configure ER6 connection

Create a `.sapcli.env` file in the project root (not committed to source control). On Windows, use `set` instead of `export`:

```cmd
set SAP_HOST=<er6-hostname>
set SAP_PORT=<port>
set SAP_CLIENT=<client>
set SAP_USER=ANZEIGER
set SAP_PASSWORD=display
set SAP_SSL=true
```

Test connectivity (in Anaconda Prompt):

```cmd
call .sapcli.env && conda run -n sapcli-env sapcli datapreview osql "SELECT DEVCLASS FROM TDEVC UP TO 1 ROWS"
```

> If you prefer PowerShell, use `$env:SAP_HOST = "<er6-hostname>"` style assignments and dot-source the file.

### 4. Clone / open the project in Claude Code

```cmd
claude C:\Users\<you>\Joule_Workspace\iam-assistant
```

### 5. Install the MCP ER6 server

```cmd
conda run -n sapcli-env pip install -r mcp-server\requirements.txt
```

The server script is `mcp-server\er6_mcp_server.py` and is already wired up in `.mcp.json` using a relative path — no path editing required:

```json
{
  "mcpServers": {
    "er6": {
      "command": "conda",
      "args": ["run", "--no-capture-output", "-n", "sapcli-env",
               "python", "./mcp-server/er6_mcp_server.py"]
    }
  }
}
```

### 6. Verify MCP connectivity

Claude Code will use the `er6` MCP tools automatically when the server is configured in `.mcp.json`. Start Claude Code and run a test query to confirm.

