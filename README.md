# IAM Assistant

A Claude Code–powered assistant for analyzing SAP IAM (Identity & Access Management) data on the ABAP system **ER6**.

## Overview

This project lets you run natural-language IAM investigations against live ER6 data using Claude Code. It ships with a Treasury IAM skill (`/treasury-iam`) that understands Segregation of Duties (SoD) rules, FOE/BOE catalog structure, and the full Treasury authorization object model.

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Claude Code | `claude` CLI installed and authenticated |
| conda | `sapcli-env` environment with `sapcli` installed |
| `.sapcli.env` | Connection credentials for ER6 (not committed — see setup below) |

## Setup

1. **Clone / open the project** in Claude Code:
   ```bash
   claude /Users/I015289/Joule_Workspace/IAM_Assistant
   ```

2. **Ensure `.sapcli.env` exists** in the project root with the ER6 connection settings (host, user, password). This file is not committed to source control.

3. **Verify the conda environment**:
   ```bash
   conda run -n sapcli-env sapcli --version
   ```

4. **Test connectivity**:
   ```bash
   source .sapcli.env && conda run -n sapcli-env sapcli datapreview osql "SELECT DEVCLASS FROM TDEVC UP TO 1 ROWS"
   ```

## Running Queries

All queries go through `sapcli` in the `sapcli-env` conda environment:

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

**Usage:**
```
/treasury-iam
```
Then ask questions like:
- _"Which apps have TRFCT=D3 and ACTVT=01 in T_DEAL_PD?"_
- _"Is TM36_TRAN FOE-compatible?"_
- _"Show me all apps in SAP_TC_FIN_TRM_COMMON that violate BOE rules."_

## Key Tables

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

## Project Structure

```
IAM_Assistant/
├── CLAUDE.md          # Claude Code instructions (data dictionary, query setup)
├── README.md          # This file
├── .sapcli.env        # ER6 connection settings (not committed)
└── skills/
    └── treasury-iam.md  # Treasury IAM skill definition
```

## Notes

- Access is **read-only** (user `ANZEIGER`/`display`)
- SSL is enabled on the ER6 connection
- Query output is `|`-separated with a header row
- Active auth object instances have `INACTIVE` = blank; superseded ones have `INACTIVE = 'X'`
