# IAM Assistant

A Claude Code–powered assistant for analyzing SAP IAM (Identity & Access Management) data on the ABAP system **ER6**.

## Overview

This project lets you run natural-language IAM investigations against live ER6 data using Claude Code. It ships with a Treasury IAM skill (`/treasury-iam`) that understands Segregation of Duties (SoD) rules, FOE/BOE catalog structure, and the full Treasury authorization object model.

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Claude Code | `claude` CLI installed and authenticated |
| MCP server | `er6` MCP server configured in `.mcp.json` (primary query path) |
| conda | `sapcli-env` environment with `sapcli` installed (fallback only) |
| `.sapcli.env` | Connection credentials for ER6 (not committed — fallback only) |

## Setup

1. **Clone / open the project** in Claude Code:
   ```bash
   claude /Users/I015289/Joule_Workspace/IAM_Assistant
   ```

2. **Install the MCP ER6 server dependencies** inside the `sapcli-env` conda environment:
   ```bash
   conda run -n sapcli-env pip install -r mcp-server/requirements.txt
   ```
   The server script is `mcp-server/er6_mcp_server.py` and is already wired up in `.mcp.json`:
   ```json
   {
     "mcpServers": {
       "er6": {
         "command": "conda",
         "args": ["run", "--no-capture-output", "-n", "sapcli-env",
                  "python", "<repo-root>/mcp-server/er6_mcp_server.py"]
       }
     }
   }
   ```
   Update the absolute path in `.mcp.json` to match your local checkout if needed.

3. **Verify MCP connectivity** — Claude Code will use the `er6` MCP tools automatically when the server is configured in `.mcp.json`.

4. **Fallback only — ensure `.sapcli.env` exists** if you need the `sapcli` CLI path (not committed to source control).

5. **Test fallback connectivity**:
   ```bash
   source .sapcli.env && conda run -n sapcli-env sapcli datapreview osql "SELECT DEVCLASS FROM TDEVC UP TO 1 ROWS"
   ```

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

**SQL dialect:** ABAP Open SQL — use `UP TO N ROWS` for row limits (not `TOP` or `FETCH FIRST`). No JOINs or subqueries.

## Skills

### `/treasury-iam`

Activates the Treasury IAM specialist mode. Use this for:

- Discovering Treasury apps in package `CLOUD_FI_TR_IAM`
- Analyzing SoD compliance of apps against FOE / BOE catalogs
- Checking forbidden TRFCT × ACTVT combinations on auth objects `T_DEAL_PD`, `T_DEAL_PF`, `T_DEAL_DP`, `T_DEAL_AG`
- Planning catalog splits when SoD violations are found
- Validating hedge request management SoD rules on auth object `T_TOE_HR` (MOE vs Accountant)

**Usage:**
```
/treasury-iam
```
Then ask questions like:
- _"Which apps have TRFCT=D3 and ACTVT=01 in T_DEAL_PD?"_
- _"Is TM36_TRAN FOE-compatible?"_
- _"Show me all apps in SAP_TC_FIN_TRM_COMMON that violate BOE rules."_
- _"Check T_TOE_HR values in SAP_FIN_BC_HEDGE_MGT_PC for MOE SoD violations."_

### `/cash-iam`

Activates the Cash Management IAM specialist mode. Use this for:

- Validating bank account create/change/delete/approve authorization setups
- Checking SoD (four-eyes principle) between submit and approve catalogs
- Analyzing auth objects `F_CLM_BAM`, `F_CLM_BAI`, `F_CLM_BAIC`, `F_CLM_BAOR`, `F_CLM_BKCR`
- Reviewing bank account interest condition authorizations
- Verifying Business Role Template (BRT) and catalog assignments

**Usage:**
```
/cash-iam
```
Then ask questions like:
- _"Verify the authorization setup of F1366_TRAN."_
- _"Does SAP_BR_CASH_MANAGER violate the four-eyes principle?"_
- _"Check whether F9017_TRAN has the correct ACTVT values for F_CLM_BAIC."_
- _"Which catalogs are assigned to SAP_BR_CASH_SPECIALIST?"_

| Table | Purpose |
|-------|---------|
| `TDEVC` | ABAP packages |
| `TADIR` | ABAP object registry (find SIA6 app objects) |
| `APS_IAM_W_APP` | IAM app registry (APP_ID, TCODE, type) |
| `APS_IAM_W_APPT` | App display texts |
| `APS_IAM_W_APPAUI` | Auth object instances per app (UUID-based) |
| `APS_IAM_W_APPAUV` | Field-level auth values (TRFCT, ACTVT, etc.) |
| `APS_IAM_W_APPAUO` | Auth object exclusions (outbound) |
| `SUI_TM_MM_APP` | Fiori Launchpad app–catalog assignments |
| `SUI_TM_MM_CAT` | Launchpad technical catalogs |
| `USOBT` / `USOBX` | Authorization defaults for T-codes |

## Treasury SoD Reference

### Core Auth Objects

| Object | Scope |
|--------|-------|
| `T_DEAL_PD` | Company code / product type / transaction type — all transactions |
| `T_DEAL_PF` | Company code / portfolio — all transactions |
| `T_DEAL_DP` | Company code / securities account — securities only |
| `T_DEAL_AG` | Company code / authorization group |

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

## Project Structure

```
IAM_Assistant/
├── CLAUDE.md                   # Claude Code instructions (data dictionary, query setup)
├── README.md                   # This file
├── .sapcli.env                 # ER6 connection settings (not committed)
└── .claude/
    ├── skills/
    │   ├── treasury-iam.md     # Treasury IAM skill (FOE/BOE SoD, T_DEAL_*, T_TOE_HR)
    │   └── cash-iam.md         # Cash Management IAM skill (F_CLM_* auth objects)
    └── commands/
        ├── treasury-iam.md     # /treasury-iam slash command
        └── cash-iam.md         # /cash-iam slash command
```

## Notes

- Access is **read-only** (user `ANZEIGER`/`display`), SSL enabled
- MCP tools are the preferred query path — `sapcli` is a fallback only
- `sapcli` query output is `|`-separated with a header row
- Active auth object instances have `INACTIVE` = blank; superseded ones have `INACTIVE = 'X'`
