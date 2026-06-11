# IAM Assistant

A Claude Code–powered assistant for analyzing SAP IAM (Identity & Access Management) data on the ABAP system **ER6**.

## Overview

This project provides two modes for running natural-language IAM investigations against live ER6 data:

- **Claude Code** — interactive CLI with domain skills for Treasury IAM, Cash Management IAM, and Finance IAM (AP/AR/GL/BA), a goal-driven autonomous agent (`/goal` + `/execute`), and a persistent memo system (`/memo`) for saving findings across sessions.
- **Web UI** — a FastAPI application with a browser-based chat interface, Anthropic streaming, MCP tool execution, OIDC authentication, and a Light/Dark theme toggle.

## Benefits

**1. Natural language access to complex SAP IAM data**
Questions like "which apps carry TRFCT=D3 and ACTVT=01?" — which would normally require an SAP developer, SE16 access, and manual cross-referencing across APPAUI/APPAUV — are translated into a correct multi-step query chain automatically, returning a clean answer in minutes.

**2. Built-in SoD knowledge — no reference lookup required**
The skill files encode the complete FOE/BOE/MOE/Accountant forbidden matrices, TRFCT semantics, HREQ_CAT values, and BRT inventory. When investigating an app, the assistant already knows that D3+01 is a FOE violation, that `APS_IAM_W_BUC` is not directly queryable, and that `SUI_TM_MM_APP` stores Treasury app IDs as GUIDs. No external documentation needed.

**3. Persistent investigation memory across sessions**
The `/memo` system preserves findings, decisions, work-in-progress, and known-good baselines. A multi-day catalog split investigation doesn't lose context between sessions. The session query log also provides a full audit trail of every ER6 query executed.

**4. Automated quality enforcement via hooks**
Three hooks enforce correctness without manual effort: memo writes are blocked if required sections are missing; skill edits are auto-synced to all three locations preventing drift; every ER6 query is logged with a timestamp for audit and replay.

**5. Reusable skill-based architecture**
Domain knowledge lives in versioned skill files, not conversation history. Any analyst invoking `/treasury-iam` or `/cash-iam` immediately gets full specialist context without re-explaining domain rules each session.

**6. Autonomous multi-step investigation via `/execute`**
Complex analyses — validating all apps in a catalog, planning a FOE/BOE split across 53 apps — can be handed to Execute, which chains queries, adapts to unexpected findings, and produces a structured report (Goal / Summary / Findings / Violations / Recommendations) without step-by-step prompting.

**7. Validated, production-calibrated query patterns**
Every query pattern in the skills was validated against live ER6 data (20 tests, 100% pass rate). Known pitfalls — `UP TO N ROWS` with `WHERE`, non-queryable tables, GUID key formats — are documented and worked around. New analysts get patterns that are known to work.

**8. Significant time savings**
A typical investigation (5–8 queries) completes in 50–90 seconds of ER6 round-trip time. What previously required an SAP consultant with direct system access and hours of manual table navigation can now be completed in a single conversation by anyone on the team.

**9. Read-only safety**
All ER6 access is through the `ANZEIGER` display user — read-only, SSL-encrypted. No risk of accidental data modification. The tool can be used freely during active system operations without change management concerns.

**10. Living documentation that improves with use**
CLAUDE.md, skill files, and README are updated as new facts surface — undocumented table fields, queryability limits, GUID key formats. The project accumulates institutional knowledge rather than leaving it in individual analysts' heads.

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Claude Code | `claude` CLI installed and authenticated |
| MCP server | `er6` MCP server configured in `.mcp.json` (primary query path) |
| conda | `sapcli-env` environment with `sapcli` installed (fallback only) |
| `.sapcli.env` | Connection credentials for ER6 (not committed — fallback only) |

## Setup

**Quick install:** From the project root, run:

```bash
./install.sh         # macOS / Linux
install.bat          # Windows (Anaconda Prompt or PowerShell)
```

The installer creates `.env` and `.sapcli.env` at Step 2. `.sapcli.env` is pre-filled with the ER6 connection details. For `.env`, set `ANTHROPIC_API_KEY` to your **Hyperspace API key** (`ANTHROPIC_BASE_URL` is already set to `http://localhost:6655`). Then start the server:

```bash
conda run -n sapcli-env uvicorn app.main:app --reload
```

**Prerequisite:** conda must be installed first. The installer aborts with a link if it can't find conda. See [Miniconda](https://docs.anaconda.com/miniconda/).

**Manual setup** (if the installer fails or you prefer step-by-step instructions): see [docs/manual-setup.md](docs/manual-setup.md).

## Running Queries

**Preferred:** Claude Code uses the `er6` MCP tools directly — no shell commands needed. The MCP server exposes:

| Tool | Purpose |
|------|---------|
| `mcp__er6__query_sql` | Run ABAP Open SQL SELECT statements |
| `mcp__er6__read_table_def` | Read DDIC table/structure definitions |
| `mcp__er6__read_cds_view` | Read CDS view (DDLS) source |
| `mcp__er6__read_class` | Read ABAP class source |
| `mcp__er6__read_program` | Read ABAP program/report source |
| `mcp__er6__list_package` | List objects in an ABAP package |

**Fallback** (only if MCP is unavailable):

```bash
source .sapcli.env
conda run -n sapcli-env sapcli datapreview osql "SELECT * FROM <TABLE> UP TO 10 ROWS"
```

**SQL dialect:** ABAP Open SQL — no JOINs or subqueries. Use the `rows` parameter on `mcp__er6__query_sql` for row limits. **Do not use `UP TO N ROWS` inline when a `WHERE` clause is present** — the ER6 backend rejects this combination.

## Skills

### Skill Selection

Skills can be activated in two ways:

**1. Explicit invocation (recommended)** — type the skill name as the first token. Claude loads the full specialist context immediately, no ambiguity:

```
/treasury-iam   → Treasury IAM specialist (FOE/BOE SoD, T_DEAL_*, T_TOE_HR)
/cash-iam       → Cash Management IAM specialist (F_CLM_*, four-eyes principle)
/fin-iam        → Finance IAM specialist (AP / AR / GL / BA — F_BKPF_*, F_LFA1_*, F_KNA1_*)
/goal           → Decompose a high-level objective into a step-by-step plan
/execute        → Autonomously execute a plan against ER6
/memo           → Save, load, or manage persistent investigation memos
```

**2. Automatic selection** — Claude matches keywords in your question against each skill's description and picks the best fit:

| Skill | Auto-triggers on |
|-------|-----------------|
| `/treasury-iam` | "Treasury", "FOE", "BOE", "MOE", "T_DEAL_*", "T_TOE_HR", "CLOUD_FI_TR_IAM", "hedge request", "Front/Back Office", "TRFCT", "limit check", "whole-BRT audit", "country variant" |
| `/cash-iam` | "Cash Management", "bank account", "F_CLM_BAM/BAI/BAIC/BAOR", "four-eyes", "submit/approve", "SAP_FIN_BC_CM_*" |
| `/fin-iam` | "AP", "AR", "GL", "Bank Accounting", "Accounts Payable/Receivable", "F_BKPF_*", "F_LFA1_*", "F_KNA1_*", "journal entry", "dunning", "payment run" |
| `/goal` | High-level objective phrasing: "validate all...", "analyze...", "I want to..." |
| `/execute` | "run the plan", "execute autonomously", direct objective with clear scope |
| `/memo` | "save memo", "remember this", "load memo", "what did we find", "resume", "show memos" |

**When automatic selection may fail:** Vague questions without domain keywords — e.g. *"check the auth objects for this app"* — may not trigger any skill. Claude will answer from general knowledge instead of the specialist context. Fix this by either using explicit invocation or adding domain keywords (app ID, auth object name, catalog ID) to your question.

**Rule of thumb:** Use explicit invocation for any multi-step or complex analysis. Reserve automatic selection for quick, clearly scoped questions.

---

### `/treasury-iam`

Activates the Treasury IAM specialist mode. Use this for:

- Discovering Treasury apps in package `CLOUD_FI_TR_IAM`
- Analyzing SoD compliance of apps against FOE / BOE catalogs
- Checking forbidden TRFCT × ACTVT combinations on auth objects `T_DEAL_PD`, `T_DEAL_PF`, `T_DEAL_DP`, `T_DEAL_AG`
- Planning catalog splits when SoD violations are found
- Validating hedge request management SoD rules on auth object `T_TOE_HR` (MOE vs Accountant)
- Auditing indirect SoD risks: `T_DEAL_LC` (limit override), `T_BP_DEAL` (counterparty binding), `T_HREL_AUT` (hedge relationship self-designation)
- Running whole-BRT audits, cross-company-code violation scans, and pre/post-migration diffs
- Identifying 30+ auth objects by SoD relevance (primary / indirect / none)

The skill encodes full business context (FOE/BOE/MOE responsibilities, why SoD matters in Treasury, country variant rules), structured workflows, troubleshooting tips, and a live ER6 appendix of observed auth objects and BRT catalog inventory.

**Example prompts:**
```
# SoD validation — single app
/treasury-iam
For app FTRCAI02_B_TRAN, validate whether it is compliant with BOE SoD rules.

# SoD validation — full catalog
/treasury-iam
For catalog SAP_TC_FIN_TRM_COMMON, check whether any apps violate FOE or BOE forbidden combinations.

# FOE/BOE classification
/treasury-iam
For app FTR_FX_F_TRAN, determine whether it belongs in a FOE or BOE catalog.

# Whole-BRT audit
/treasury-iam
For BRT SAP_BR_TREASURY_SPECIALIST_FOE, audit all catalogs and apps for SoD violations.

# Hedge SoD (T_TOE_HR)
/treasury-iam
For catalog SAP_FIN_BC_HEDGE_MGT_PC, validate T_TOE_HR values against MOE forbidden combinations.

# Indirect SoD — limit override check
/treasury-iam
For app <APP_ID>, check whether T_DEAL_LC override activity is held alongside T_DEAL_PD D2+01.
```

### `/cash-iam`

Activates the Cash Management IAM specialist mode. Use this for:

- Validating bank account create/change/delete/approve authorization setups
- Checking SoD (four-eyes principle) between submit and approve catalogs
- Analyzing auth objects `F_CLM_BAM`, `F_CLM_BAI`, `F_CLM_BAIC`, `F_CLM_BAOR`, `F_CLM_BKCR`
- Reviewing bank account interest condition authorizations
- Verifying Business Role Template (BRT) and catalog assignments

**Example prompts:**
```
# Activity set verification — create/change/delete
/cash-iam
For IAM App ID F1366_TRAN, verify whether the authorization activity set is complete and aligned with bank account create/change/delete.

# Approval catalog over-entitlement check
/cash-iam
For Business Catalog SAP_FIN_BC_CM_BAA_APPROVE_PC, check whether approval activities are correctly restricted from over-entitlement.

# Full IAM health check
/cash-iam
For IAM App ID F9017_TRAN, run a full IAM health check including authorization objects, activity sets, and catalog assignment.

# Four-eyes principle — BRT level
/cash-iam
For BRT SAP_BR_CASH_MANAGER, identify whether any access combination violates the four-eyes principle.

# Submit/approve segregation — single app
/cash-iam
For IAM App ID F5859_TRAN, analyze whether submit and approve capabilities are properly segregated.
```

### `/fin-iam`

Activates the Finance IAM specialist mode. Use this for:

- Analyzing app authorizations in AP (`CLOUD_FI_AP_IAM`), AR (`CLOUD_FI_AR_IAM`), GL (`CLOUD_FI_GL_IAM`), and BA (`CLOUD_FI_BA_IAM`) packages
- Checking core FI auth objects: `F_BKPF_BUK`, `F_BKPF_BLA`, `F_BKPF_KOA` (document posting), `F_LFA1_BUK` (vendor master), `F_KNA1_BUK` (customer master)
- Validating SoD between AP invoice creation and payment approval (four-eyes)
- Tracing authorization setup across AP payment run, AR clearing, and GL journal entry flows

**Example prompts:**
```
# AP payment flow SoD
/fin-iam
For the AP payment run flow (F0770_TRAN → F0771_TRAN → F0673A_TRAN), trace auth objects and confirm SoD between proposal, revision, and approval.

# GL posting controls
/fin-iam
For the GL journal entry flow (post / park / verify), trace auth objects F_BKPF_BUK, F_BKPF_BLA, F_BKPF_KOA and confirm posting controls.

# App auth analysis
/fin-iam
For IAM App ID <APP_ID>, show all active authorization object instances and their field values.

# AR dunning SoD
/fin-iam
For AR, verify that dunning and incoming payment posting are not both held by a single role without oversight.
```

### `/goal`

Captures a high-level IAM analysis objective and decomposes it into a concrete, step-by-step plan. Use this when the task spans multiple queries or requires a structured investigation.

**Example prompts:**
```
# Catalog-wide SoD compliance + split proposal
/goal Validate all apps in SAP_TC_FIN_TRM_COMMON for FOE/BOE SoD compliance and propose a catalog split

# Single-app health check
/goal Run a full IAM health check on F9017_TRAN including auth objects, activity sets, and catalog assignment

# Four-eyes principle — BRT level
/goal Check whether SAP_BR_CASH_MANAGER violates the four-eyes principle across submit and approve catalogs

# Cross-app TRFCT search
/goal Find all Treasury apps that hold both D2 and D3 TRFCT values on T_DEAL_PD
```

### `/execute`

Autonomous execution agent. Works through an IAM analysis plan step by step — chaining ER6 queries, evaluating results, and adapting if findings require detours — without prompting at each step. Typically invoked after `/goal`, but can also be triggered directly with a clear objective. Produces a structured `=== Execute Report ===` (Goal / Summary / Findings / Violations / Recommendations) on completion.

**Example prompts:**
```
# After /goal — execute the full plan
/execute

# Hedge SoD — full catalog sweep
/execute Validate T_TOE_HR SoD for all apps in SAP_FIN_BC_TRM_HM_HR_FOE_PC

# BRT forbidden combination check
/execute Check whether SAP_BR_TREASURY_SPECIALIST_BOE contains any FOE-forbidden combinations

# Single-app health check
/execute Run a health check on F5859_TRAN: auth objects, ACTVT values, catalog assignment, and BRT coverage

# Cash four-eyes check
/execute Check whether SAP_BR_CASH_MANAGER violates the four-eyes principle across submit and approve catalogs
```

### `/memo`

Persistent memory for IAM findings across sessions. Saves to `.claude/memo/` as markdown files, indexed by `INDEX.md`.

**Sub-commands:**

| Command | Action |
|---------|--------|
| `/memo save [topic]` | Save current session findings to a new memo file |
| `/memo update [topic]` | Append new findings to an existing memo |
| `/memo load [topic]` | Load a memo into context and offer to resume |
| `/memo list` | Show all saved memos from INDEX.md |
| `/memo clear <topic>` | Delete a memo (asks for confirmation) |

Each memo file contains four sections: **Findings**, **Decisions**, **Work in Progress**, **Known Good Baselines**.

At session start, Claude automatically checks `INDEX.md` and surfaces any in-progress memos:
> Found in-progress memo: **trm-catalog-split** — last updated 2026-05-10. Load it to resume?

**Example topics:** `trm-catalog-split`, `hedge-ttoe-hr-sod`, `cash-f9017-healthcheck`

**Example prompts:**
```
/memo save                              ← auto-infers topic from current conversation
/memo save trm-foe-boe-split            ← save under a specific topic
/memo save hedge-ttoe-hr-sod            ← save hedge SoD findings

/memo load trm-foe-boe-split            ← reload a previous investigation
/memo list                              ← show all saved memos
/memo update hedge-ttoe-hr-sod          ← append new findings to an existing memo
/memo clear trm-foe-boe-split           ← delete a memo (asks for confirmation)
```

**Combined end-to-end workflow:**
```
/goal Validate FOE/BOE SoD for all apps in CLOUD_FI_TR_IAM
        ↓  (plan presented)
/execute  ← executes all steps, queries ER6, produces report
        ↓  (findings ready)
/memo save trm-cloud-foe-boe-validation
        ↓  (next session — Claude auto-surfaces In Progress memos)
/memo load trm-cloud-foe-boe-validation
        ↓
/execute Continue from Step 4 — validate remaining apps
```

## Hooks

Three hooks are configured in `.claude/settings.json` to automate common tasks:

| Hook | Event | Trigger | What it does |
|------|-------|---------|--------------|
| `validate-memo.sh` | PreToolUse | Write | Blocks writes to `.claude/memo/*.md` if any of the 4 required sections are missing. Exits non-zero to abort the write. |
| `sync-skills.sh` | PostToolUse | Write | After any skill file is written to `.claude/skills/*.md`, automatically copies it to `skills/` (with frontmatter) and `.claude/commands/` (frontmatter stripped). |
| `log-query.sh` | PostToolUse | `mcp__er6__query_sql` | Asynchronously appends each ER6 SQL query with a timestamp to `.claude/memo/.session-log.md` for audit and replay. |

### Memo Validation

Every memo file (except `INDEX.md` and `.session-log.md`) must contain all four sections:

```
## Findings
## Decisions
## Work in Progress
## Known Good Baselines
```

If any section is missing, the write is blocked with an error listing the missing sections.

### Skill Sync

Editing a skill in `.claude/skills/` is the canonical source of truth. The sync hook handles propagation:

```
.claude/skills/treasury-iam.md  →  skills/treasury-iam.md        (full copy, with frontmatter)
                                →  .claude/commands/treasury-iam.md  (frontmatter stripped)
```

### Query Log

All ER6 SQL queries are logged to `.claude/memo/.session-log.md`:

```markdown
## 2026-05-10 14:23:01
```sql
SELECT BU_CATALOG_ID, APP_ID FROM APS_IAM_W_BC_APP WHERE APP_ID = 'FTRCAI02_B_TRAN'
```
rows limit: 20
```

## Key ER6 Tables

| Table | Purpose |
|-------|---------|
| `TDEVC` | ABAP packages |
| `TADIR` | ABAP object registry (find SIA6 app objects) |
| `APS_IAM_W_APP` | IAM app registry (APP_ID, TCODE, type) |
| `APS_IAM_W_APPT` | App display texts |
| `APS_IAM_W_APPAUI` | Auth object instances per app (UUID-based) |
| `APS_IAM_W_APPAUV` | Field-level auth values (TRFCT, ACTVT, etc.) |
| `APS_IAM_W_APPAUO` | Auth object exclusions (outbound) |
| `APS_IAM_W_BC_APP` | Business catalog app assignments (use this for catalog lookups by app name) |
| `APS_IAM_W_BRTBUC` | Business Role Template to Business Catalog assignments |
| `APS_IAM_W_BUC` | Business Catalog master (⚠ not directly queryable — use `APS_IAM_W_BRTBUC` or `APS_IAM_W_BC_APP` instead) |
| `SUI_TM_MM_APP` | Fiori Launchpad app–catalog assignments (⚠ Treasury apps stored as GUIDs here — use `APS_IAM_W_BC_APP` instead) |
| `SUI_TM_MM_CAT` | Launchpad technical catalogs |
| `USOBT` / `USOBX` | Authorization defaults for T-codes |

## Treasury SoD Reference

### Core Auth Objects

| Object | Scope |
|--------|-------|
| `T_DEAL_PD` | Company code / product type / transaction type — all transactions |
| `T_DEAL_PF` | Company code / portfolio — all transactions |
| `T_DEAL_DP` | Company code / securities account — securities only |
| `T_DEAL_AG` | Company code / authorization group (unused in cloud) |

### TRFCT Values

| Value | Meaning |
|-------|---------|
| `D1` | Order |
| `D2` | Contract |
| `D3` | Settlement |

### Forbidden Combinations

**FOE catalog** must NOT contain:

| TRFCT | ACTVT | Meaning |
|-------|-------|---------|
| D3 | 01 | Create settlement |
| D3 | 85 | Reverse settlement |
| D2 | AB | Settle contract |

**BOE catalog** must NOT contain:

| TRFCT | ACTVT | Meaning |
|-------|-------|---------|
| D2 | 01 | Create contract |
| D2 | 02 | Edit contract |
| D2 | 16 | Execute contract |
| D2 | 85 | Reverse contract |
| D2 | KU | Give Notice |
| D2 | VF | Expire contract |

### Business Role Templates

| BRT ID | Display Name | Office |
|--------|--------------|--------|
| `SAP_BR_TREASURY_SPECIALIST_FOE` | Treasury Specialist - Front Office | FOE |
| `SAP_BR_TREASURY_SPECIALIST_BOE` | Treasury Specialist - Back Office | BOE |
| `SAP_BR_TREASURY_SPECIALIST_MOE` | Treasury Specialist - Middle Office | MOE |
| `SAP_BR_TREASURY_ACCOUNTANT` | Treasury Accountant | BOE |
| `SAP_BR_TREASURY_RISK_MANAGER` | Treasury Risk Manager | Mixed |

Country variants (`_CN`, `_SG`, `_TH`, `_BR`) follow the same catalog pattern as their base BRT.

## Hedge Request Management SoD Reference

Governed by auth object **`T_TOE_HR`** (fields: `HREQ_CAT`, `ACTVT`), independent of the `T_DEAL_*` objects.

### HREQ_CAT Values

| Value | Meaning |
|-------|---------|
| `A` | Manual Designation |
| `D` | Dedesignation |
| `G` | FX Hedge |
| `O` | Offsetting |
| `S` | FX Swap |

### Role Split and Relevant Catalogs

| Role | Catalogs | Restriction |
|------|----------|-------------|
| **MOE** (front office) | `SAP_FIN_BC_HEDGE_MGT_PC`, `SAP_FIN_BC_TRM_HM_HR_FOE_PC` | Cannot release or reverse designation/dedesignation requests |
| **Accountant** | `SAP_FIN_BC_TRM_HM_HR_ACCT_PC` | Can only release and reverse dedesignation requests |

### Forbidden Combinations

**MOE catalogs** must NOT contain (on `T_TOE_HR`):

| HREQ_CAT | ACTVT | Meaning |
|----------|-------|---------|
| A | 43 | Release manual designation request |
| A | 85 | Reverse manual designation request |
| D | 43 | Release dedesignation request |
| D | 85 | Reverse dedesignation request |

**Accountant catalogs** must NOT contain (on `T_TOE_HR`):

| HREQ_CAT | ACTVT | Meaning |
|----------|-------|---------|
| A | 01 | Create manual designation request |
| A | 02 | Change manual designation request |
| A | 06 | Delete manual designation request |
| D | 01 | Create dedesignation request |
| D | 02 | Change dedesignation request |
| D | 06 | Delete dedesignation request |

> Categories G, O, S carry no SoD restriction — both roles may hold all activities for those categories.

## Cash Management SoD Reference

### Core Authorization Objects

| Auth Object | Description | Key ACTVT Values |
|-------------|-------------|-----------------|
| `F_CLM_BAM` | Bank account master data (create/change/delete/display) | `01`=Create, `02`=Change, `03`=Display, `06`=Delete, `63`=Transport |
| `F_CLM_BAOR` | Bank account opening request (submit/approve) | `03`=Display, `31`=Approve |
| `F_CLM_BKCR` | Bank account change request (create/change/approve) | `01`=Create, `02`=Change, `03`=Display |
| `F_CLM_BAI` | Bank account interest records | `03`=Display, `06`=Delete |
| `F_CLM_BAIC` | Bank account interest conditions | `01`=Create, `02`=Change, `03`=Display, `06`=Delete, `F4`=Value Help |
| `F_CLM_BAH2` | Bank account hierarchy | `01`=Create, `02`=Change, `03`=Display, `06`=Delete |

### Key Business Catalogs

| Catalog ID | Title | Role |
|------------|-------|------|
| `SAP_FIN_BC_CM_BAM2_PC` | Bank Accounts Management | Create/change/delete/approve accounts |
| `SAP_FIN_BC_CM_BAM2_BASIC_PC` | Bank Accounts Management Basic | Display bank accounts |
| `SAP_FIN_BC_CM_BAA_SUBMIT_PC` | Submit Bank Account Applications | Submit workflow |
| `SAP_FIN_BC_CM_BAA_APPROVE_PC` | Approve Bank Account Applications | Approve workflow |
| `SAP_FIN_BC_CM_BAI_PC` | Bank Account Interest Management | Interest conditions |

### Business Role Templates

| BRT ID | Display Name | Catalogs |
|--------|--------------|---------|
| `SAP_BR_CASH_MANAGER` | Cash Manager | BAM2_PC, BAA_APPROVE_PC, BAI_PC |
| `SAP_BR_CASH_SPECIALIST` | Cash Management Specialist | BAM2_PC, BAA_SUBMIT_PC, BAA_APPROVE_PC, BAI_PC |

### Four-Eyes Principle (SoD)

Cash Management enforces separation via workflow rather than hard auth-object rules:

- **Submitter** (`SAP_FIN_BC_CM_BAA_SUBMIT_PC`) must NOT be the same role as **Approver** (`SAP_FIN_BC_CM_BAA_APPROVE_PC`)
- A user creating bank accounts (`F1366_TRAN`, ACTVT 01/02) should not also approve changes (`F6264_TRAN`)

### Activity Matrix per Key App

| App | Description | F_CLM_BAM ACTVT | F_CLM_BAOR ACTVT | F_CLM_BKCR ACTVT |
|-----|-------------|-----------------|------------------|------------------|
| `F1366_TRAN` | Manage Bank Accounts | 01, 02, 03, 06 | — | — |
| `F1366A_TRAN` | Display Bank Accounts | 03 | — | — |
| `F5861_TRAN` | Submit Applications | — | (submit flow) | — |
| `F5859_TRAN` | Approve Applications | — | 03, 31 | — |
| `F5860_TRAN` | Applications Overview | — | 03, 31 | — |
| `F6264_TRAN` | Approve Changes | 03, 63 | — | 01, 02, 03 |
| `F9015_TRAN` | Monitor Interest | 03 | — | — |
| `F9016_TRAN` | Schedule Interest Jobs | 03 | — | — |
| `F9017_TRAN` | Manage Interest Conditions | 03 | — | — |

## Performance Timing Reference

Measured against live ER6 data (2026-05-15, 20 tests, 100% pass rate).

### By Tool Type

| Tool | Calls | Mean | Min | Max |
|------|-------|------|-----|-----|
| `mcp__er6__query_sql` | 17 | 10,106 ms | 8,728 ms | 12,603 ms |
| `mcp__er6__read_table_def` | 2 | 8,922 ms | 8,650 ms | 9,193 ms |
| `mcp__er6__list_package` | 1 | 17,322 ms | — | — |

### Selected Query Timings

| Operation | Table | Rows | Duration |
|-----------|-------|------|----------|
| SIA6 objects in package | `TADIR` | 20 | 12,603 ms |
| List full package contents | `list_package` | 700+ objects | 17,322 ms |
| App registry point lookup | `APS_IAM_W_APP` | 1 | 9,592 ms |
| App registry LIKE query | `APS_IAM_W_APP` | 20 | 10,732 ms |
| Auth object instances | `APS_IAM_W_APPAUI` | 5–15 | 9,129–10,082 ms |
| Auth field values | `APS_IAM_W_APPAUV` | 21–50 | 9,567–12,001 ms |
| Business catalog lookup | `APS_IAM_W_BC_APP` | 1 | 9,343–11,053 ms |
| BRT catalog assignments | `APS_IAM_W_BRTBUC` | 29–39 | 9,131–11,223 ms |
| Table DDL definition | `read_table_def` | DDL | 8,650–9,193 ms |

### Notes

- **Typical investigation cost:** A 5–8 query analysis runs in roughly **50–90 seconds** of ER6 round-trip time.
- **`list_package` is the slowest tool** (~17 s) due to large payload size for big packages — avoid on packages with hundreds of objects unless needed.
- **`read_table_def` is fastest** (~8.9 s mean) — returns DDL only, no table scan.
- **Row count has modest impact:** 50-row result sets take ~2.5 s longer than single-row lookups against the same table.
- **Repeat queries run ~19% faster** on second call due to server-side caching (observed on identical BRTBUC queries: 11,223 ms cold → 9,131 ms warm).

## Web UI

The `app/` directory contains a standalone web application for browser-based IAM chat. It runs the same Anthropic model and MCP tools as the Claude Code CLI.

### Stack

| Component | Technology |
|-----------|-----------|
| Web framework | FastAPI + Uvicorn |
| Chat streaming | Anthropic API (`claude-opus-4-7`), SSE |
| ER6 tools | MCP subprocess over stdio (same `er6_mcp_server.py`) |
| Auth | OIDC (Authlib) with signed session cookie; dev mode skips OIDC |
| Templates | Jinja2 (`ui/templates/`) |
| Static assets | `ui/static/` (CSS + JS) |
| Markdown rendering | `marked` + `DOMPurify`, vendored locally in `ui/static/vendor/` (no CDN dependency) |
| Theming | CSS variables with `data-theme` attribute on `<html>`; Catppuccin Latte (Light) / Mocha (Dark) palettes |

### Configuration

Create a `.env` file in the project root:

```env
ANTHROPIC_API_KEY=<your-hyperspace-api-key>   # Hyperspace API key (not the standard Anthropic key)
ANTHROPIC_BASE_URL=http://localhost:6655
OIDC_CLIENT_ID=your-client-id
OIDC_CLIENT_SECRET=your-client-secret
OIDC_DISCOVERY_URL=https://your-idp/.well-known/openid-configuration
SESSION_SECRET=a-long-random-string
BASE_URL=http://localhost:8080
```

**Dev mode:** Set `OIDC_CLIENT_ID=your-client-id` (the placeholder default) to skip OIDC and auto-log in as `dev`.

### Running the Web UI

```bash
# Install dependencies
conda run -n sapcli-env pip install -r app/requirements.txt

# Start the server
conda run -n sapcli-env uvicorn app.main:app --reload
```

Then open `http://localhost:8080` in your browser.

### Theme

The header has a Light / Dark toggle (next to the logo). The default is **Light** (Catppuccin Latte); clicking it switches to **Dark** (Catppuccin Mocha) and the choice is persisted in `localStorage`. An inline `<head>` script applies the saved theme before the stylesheet loads, so reloading never flashes the wrong palette.

### Session Management

Sessions are stored client-side in `localStorage`. Each session holds its own conversation history; switching sessions restores the full message list. The **+ New** button in the sidebar creates a new empty session. It is disabled while a response is being generated and re-enabled when generation completes or is stopped.

### Prompt Templates

The welcome screen displays a categorised library of example prompts (`ui/static/prompt-templates.js`). Categories and their contents:

| Category | Templates |
|----------|-----------|
| **Getting Started** | What can I ask?, Glossary: BRT/BC/App, What is SoD?, How do roles work? |
| **General** | App → Catalog mapping, Restriction type coverage, BRT catalog tree, Auth object usage |
| **Finance — AP** | App auth analysis, AP payment flow SoD |
| **Finance — AR** | AR clearing & incoming payment, AR dunning SoD check |
| **Finance — GL** | GL posting controls, Activity set check |
| **Finance — BA** | Bank statement health check |
| **Treasury and Risk Management** | FOE/BOE SoD validation, Catalog split analysis, Hedge request SoD, BRT footprint |
| **Cash Management** | Activity set completeness, Submit/Approve SoD, Four-eyes catalog check, IAM health check |

### Tests

```bash
conda run -n sapcli-env pytest tests/
```

---

## Project Structure

```
iam-assistant/
├── CLAUDE.md                   # Claude Code instructions (data dictionary, query setup, memo auto-load)
├── README.md                   # This file
├── pyproject.toml              # pytest configuration
├── .sapcli.env                 # ER6 connection settings (not committed; fallback only)
├── .env                        # Web UI settings (not committed)
├── app/                        # Web UI application
│   ├── main.py                 # FastAPI app, routes, MCP lifespan
│   ├── auth.py                 # OIDC auth routes and session dependency
│   ├── chat.py                 # Anthropic streaming chat with MCP tool execution
│   ├── config.py               # Pydantic settings (loaded from .env)
│   ├── mcp_client.py           # MCP subprocess client (stdio protocol)
│   └── requirements.txt        # Python dependencies for the web app
├── ui/
│   ├── templates/index.html    # Jinja2 chat template
│   └── static/
│       ├── app.js              # Chat/streaming/sessions/theme logic
│       ├── style.css           # Layout, styles, Dark + Light palettes
│       ├── prompt-templates.js # Welcome-screen prompt library
│       └── vendor/             # Vendored marked.js + DOMPurify (no CDN)
├── tests/                      # pytest test suite
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_chat.py
│   ├── test_config.py
│   ├── test_main.py
│   └── test_mcp_client.py
├── mcp-server/
│   └── er6_mcp_server.py       # MCP server exposing ER6 tools
├── skills/                     # Skill source files (mirrored from .claude/skills/ by sync hook)
│   ├── treasury-iam.md
│   ├── cash-iam.md
│   ├── fin-iam.md
│   ├── goal.md
│   ├── execute.md
│   └── memo.md
└── .claude/
    ├── hooks/
    │   ├── validate-memo.sh    # PreToolUse/Write: blocks memo writes with missing sections
    │   ├── sync-skills.sh      # PostToolUse/Write: syncs .claude/skills/ → skills/ and commands/
    │   └── log-query.sh        # PostToolUse/query_sql (async): logs queries to .session-log.md
    ├── memo/
    │   ├── INDEX.md            # Index of all saved memos (auto-loaded at session start)
    │   ├── .session-log.md     # Auto-generated query log (written by log-query hook)
    │   └── *.md                # Per-investigation memo files
    ├── skills/
    │   ├── treasury-iam.md     # Treasury IAM skill (FOE/BOE SoD, T_DEAL_*, T_TOE_HR)
    │   ├── cash-iam.md         # Cash Management IAM skill (F_CLM_* auth objects)
    │   ├── fin-iam.md          # Finance IAM skill (AP/AR/GL/BA — F_BKPF_*, F_LFA1_*, F_KNA1_*)
    │   ├── goal.md             # Goal decomposition skill
    │   ├── execute.md          # Autonomous multi-step execution agent
    │   └── memo.md             # Persistent memo system
    ├── commands/
    │   ├── treasury-iam.md     # /treasury-iam slash command
    │   ├── cash-iam.md         # /cash-iam slash command
    │   ├── fin-iam.md          # /fin-iam slash command
    │   ├── goal.md             # /goal slash command
    │   ├── execute.md          # /execute slash command
    │   └── memo.md             # /memo slash command
    └── settings.json           # Hooks and permission configuration
```

## Notes

- Access is **read-only** (user `ANZEIGER`/`display`), SSL enabled
- MCP tools are the preferred query path — `sapcli` is a fallback only
- `sapcli` query output is `|`-separated with a header row
- Active auth object instances have `INACTIVE` = blank; superseded ones have `INACTIVE = 'X'`
