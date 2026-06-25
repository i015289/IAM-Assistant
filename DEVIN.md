# IAM Assistant — Devin Onboarding

## What this project does

IAM Assistant is a natural-language analysis tool for SAP IAM (Identity & Access Management) data on the ABAP system **ER6**. It translates plain English questions into ABAP Open SQL queries, executes them via MCP tools, and returns structured answers — without requiring the analyst to know SQL or SAP table structures.

It has two modes:
- **Claude Code CLI** — interactive terminal assistant with domain skills and autonomous execution
- **Web UI** — FastAPI browser app with streaming chat, OIDC auth, and the same MCP tools

## Repository layout

```
iam-assistant/
├── app/                    # Web UI (FastAPI)
│   ├── main.py             # Routes, MCP lifespan, status indicators
│   ├── chat.py             # Anthropic streaming + MCP tool execution
│   ├── mcp_client.py       # MCPClient + MCPMultiClient (er6 + sap-wiki)
│   ├── auth.py             # OIDC + dev-mode bypass
│   └── config.py           # Pydantic settings from .env
├── ui/
│   ├── templates/index.html
│   └── static/             # app.js, style.css, prompt-templates.js, vendor/
├── mcp-server/
│   └── er6_mcp_server.py   # MCP server: 6 ER6 read-only tools over stdio
├── .mcp.json               # MCP server definitions (er6 + sap-wiki)
├── .claude/
│   ├── skills/             # Domain skill files (treasury-iam, cash-iam, fin-iam, iam-wiki, etc.)
│   ├── commands/           # Slash command entry points
│   ├── hooks/              # validate-memo.sh, sync-skills.sh, log-query.sh
│   ├── memo/               # Persistent investigation memos (INDEX.md + per-topic files)
│   └── settings.json       # Permissions + hook configuration
├── CLAUDE.md               # Full data dictionary and query setup for Claude Code
└── README.md               # Complete user documentation
```

## MCP servers

Two MCP servers run as subprocesses, registered in `.mcp.json`:

| Server | Tools | Purpose |
|--------|-------|---------|
| `er6` | `query_sql`, `read_table_def`, `read_cds_view`, `read_class`, `read_program`, `list_package` | Read-only access to SAP ER6 ABAP system |
| `sap-wiki` | `general_search`, `cql_search`, `wiki_content`, `cql_examples` | Read-only SAP Confluence wiki search (SAP internal network required) |

Both are started at Web UI startup via `MCPMultiClient`. Failed servers are non-fatal (logged, skipped). The header shows independent connection status for each.

## Running locally

**Prerequisites:** conda with `sapcli-env` environment.

```bash
./install.sh   # creates .env and .sapcli.env, installs all dependencies
```

Then fill in `.env`:
```env
ANTHROPIC_API_KEY=<hyperspace-key>
ANTHROPIC_BASE_URL=http://localhost:6655
OIDC_CLIENT_ID=your-client-id    # use placeholder to skip OIDC in dev
SESSION_SECRET=<random-string>
BASE_URL=http://localhost:8080
WIKI_API_TOKEN=<sap-wiki-token>
```

Start the server:
```bash
conda run -n sapcli-env uvicorn app.main:app --reload
```

Open `http://localhost:8080`.

## Key technical facts

- **SQL dialect:** ABAP Open SQL — no JOINs, no subqueries, no table aliases. Multi-hop queries are staged across multiple calls.
- **Row limits:** Pass `rows` as a parameter to `query_sql`, not inline `UP TO N ROWS` when a `WHERE` clause is present.
- **Primary data layer:** CDS views (`I_APS_BUSINESS_CATALOG`, `APS_IAM_AUTH_FIELD_VAL`, etc.) over raw `APS_IAM_W_*` tables.
- **Auth:** OIDC in production; set `OIDC_CLIENT_ID=your-client-id` (the placeholder) to auto-login as `ANZEIGER` in dev.
- **Wiki access:** `sap-wiki` MCP is read-only. Write tools (`wiki_create_page`, `wiki_update_page`, `wiki_get_page_for_edit`) are not pre-approved and require explicit user confirmation.
- **ER6 access:** Read-only via user `ANZEIGER`/`display`, SSL enabled.

## Tests

```bash
conda run -n sapcli-env pytest tests/
```

Test suite covers: auth, chat streaming, MCP client, config, and main routes.

## Domain skills (slash commands)

| Command | Domain |
|---------|--------|
| `/treasury-iam` | Treasury SoD — FOE/BOE/MOE, T_DEAL_*, T_TOE_HR |
| `/cash-iam` | Cash Management — F_CLM_*, four-eyes principle |
| `/fin-iam` | Finance — AP/AR/GL/BA, F_BKPF_*, F_LFA1_*, F_KNA1_* |
| `/iam-wiki` | SAP Confluence research via sap-wiki MCP |
| `/goal` | Decompose a high-level objective into a plan |
| `/execute` | Autonomously execute a plan against ER6 |
| `/memo` | Save/load persistent investigation memos |
