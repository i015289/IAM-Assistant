# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

IAM (Identity & Access Management) analysis assistant that queries the SAP ABAP system **ER6** to analyze authorizations, roles, packages, transactions, and related IAM data.

## Running Queries Against ER6

### Setup

1. Activate the connection environment:
   ```bash
   source .sapcli.env
   ```

2. Run a query:
   ```bash
   conda run -n sapcli-env sapcli datapreview osql "SELECT * FROM TABLE_NAME UP TO 10 ROWS"
   ```

### Key Notes

- sapcli is installed in the conda environment `sapcli-env`
- Connection credentials and host are defined in `.sapcli.env` (not committed)
- Output is `|`-separated, similar to CSV with a header row
- SQL dialect is **ABAP Open SQL** — use `UP TO N ROWS` for row limits (not `TOP` or `FETCH FIRST`)
- Authentication: username/password (`ANZEIGER`/`display`), read-only access, SSL enabled

## Data Dictionary

### TDEVC — ABAP Packages
- `DEVCLASS`: Package name (PK)
- `PACKTYPE`: `C`=Cloud, `D`=Deactivated, `H`=Home, `O`=On-Premise, `F`=Future Cloud

### TADIR — ABAP Object Registry
- `OBJ_NAME`: Object name
- `OBJECT`: Object type
- `PGMID`: Program ID

### USOBT / USOBX — Authorization Defaults
Maps T-Codes to required Authorization Objects.
- `USOBX`: Whether a check is active
- `USOBT`: Proposed values (the "Variant")
- `NAME`: Transaction code, `OBJECT`: Authorization Object, `TYPE`: Object type

### USOBHASH — Authorization Defaults Hash Keys
- `NAME`: Hash key, `TYPE`: Auth object type
- `OBJ_NAME`, `OBJECT`, `PGMID`: same as TADIR

### TSTCV — Transaction Variants
Maps T-Codes to visual/functional variants.
- `TCODE`: Base transaction, `VARIANT`: Variant name

### T001 — Company Codes

### SUI_TM_MM_APP — Fiori Launchpad App Description Items

### SUI_TM_MM_CAT — Launchpad Technical Catalog

### APS_IAM_W_APP — IAM App Registry
Master table of IAM-managed apps (SIA6 objects).
- `APP_ID`: App identifier (PK, e.g. `F1443A_TRAN`)
- `APP_TYPE`: Type of app (e.g. `TRAN` for transaction-based)
- `TCODE`: Linked SAP transaction code
- `READ_ONLY`: Whether the app is read-only
- `SCOPE_DEPENDENT`: Whether app is scope-dependent
- `CREATE_USER` / `CHANGE_USER`: Responsible users
- `CREATE_TIMESTAMP` / `CHANGE_TIMESTAMP`: Audit timestamps

### APS_IAM_W_APPT — IAM App Texts
Human-readable descriptions for apps.
- `APP_ID`: App identifier (FK to APS_IAM_W_APP)
- `TEXT`: Display text / description
- `LANGU`: Language key

### APS_IAM_W_APPAUO — IAM App Authorization Objects (Outbound)
Maps apps to authorization objects that must NOT be checked (exclusions/overrides).
- `APP_ID`: App identifier
- `AUTH_OBJECT`: Authorization object (e.g. `S_TABU_NAM`, `B_BUP_DCPD`)
- `STATUS`: Status flag (e.g. `S`)

### APS_IAM_W_APPAUI — IAM App Authorization Object Instances
Detailed authorization object instances per app, with UUID-based hierarchy.
- `APP_ID`: App identifier
- `UUID`: Unique ID of this instance
- `AUTH_OBJECT`: Authorization object
- `AUTH_OBJECT_INST_ID`: Instance ID
- `STATUS`: Status flag
- `IBS_SOURCE`, `IBS_SOURCE_TYPE`: Source tracing fields
- `INACTIVE`, `COPIED`: State flags

### APS_IAM_W_APPAUV — IAM App Authorization Values
Field-level authorization values for each auth object instance.
- `APP_ID`: App identifier
- `UUID`: This value record's UUID
- `PARENT_ID`: UUID of the parent auth object instance (links to APS_IAM_W_APPAUI)
- `FIELD`: Authorization field name (e.g. `ACTVT`)
- `LOW_VALUE` / `HIGH_VALUE`: Value range
- `STATUS`: Status flag
- `COPIED`: Whether value was copied
