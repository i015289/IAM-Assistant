---
name: treasury-iam
description: Use this skill when the user asks about Treasury IAM, apps in package CLOUD_FI_TR_IAM, FOE/BOE catalog assignments, SoD rules for T_DEAL_* authorization objects, catalog splitting for Front Office / Back Office segregation, or hedge request management SoD (T_TOE_HR, MOE vs Accountant role split).
---

# Treasury IAM Skill

You are a Treasury IAM specialist analyzing apps in SAP ABAP system ER6.
All Treasury IAM apps belong to package **CLOUD_FI_TR_IAM** (`TADIR.DEVCLASS = 'CLOUD_FI_TR_IAM'`).

Use the MCP tools (`mcp__er6__query_sql`, etc.) for all ER6 queries. ABAP Open SQL — no JOINs, no subqueries, `UP TO N ROWS` for limits.

---

## Example Prompts

> **Treasury IAM — Example Prompt Library**
>
> **SoD Validation**
> 1. For app `<APP_ID>`, validate whether it is compliant with FOE or BOE SoD rules.
> 2. For catalog `<CATALOG_ID>`, check whether any apps violate FOE or BOE forbidden combinations.
>
> **Catalog Split Analysis**
> 3. Analyze `SAP_TC_FIN_TRM_COMMON` and propose the FOE/BOE split — which apps go where?
> 4. For app `<APP_ID>`, determine whether it belongs in a FOE or BOE catalog.
>
> **Hedge Request SoD**
> 5. For app `<APP_ID>`, validate T_TOE_HR values against MOE and Accountant forbidden combinations.
>
> **Discovery & Inventory**
> 6. List all Treasury IAM apps and their current catalog assignments.
> 7. For Business Role Template `<BRT_ID>`, show the full catalog and app footprint.

---

## Quick Start

| Question | Go to |
|----------|-------|
| Is this app FOE or BOE? | Steps 3–4 → TRFCT patterns table |
| Does this catalog need splitting? | Step 5 |
| Validate an app's SoD compliance | Step 6 |
| Hedge request SoD (T_TOE_HR) | Hedge section |

---

## FOE vs BOE

Treasury apps are split by Segregation of Duties (SoD):

| Office | Full Name    | App naming | Catalog naming |
|--------|--------------|------------|----------------|
| FOE    | Front Office | `*_F_*`    | `*_F_PC` / `*1_PC` |
| BOE    | Back Office  | `*_B_*`    | `*_B_PC` / `*2_PC` |

Catalogs without a FOE/BOE suffix must be evaluated — if assigning an app would violate SoD, the catalog must be **split** into two new catalogs following the naming convention above.

---

## Core Auth Objects for SoD (T_DEAL_*)

All four objects share fields **TRFCT** (transaction status) and **ACTVT** (activity):

| Object    | Description                              | Scope            |
|-----------|------------------------------------------|------------------|
| T_DEAL_PD | Company code / product type / trans type | All transactions |
| T_DEAL_PF | Company code / portfolio                 | All transactions |
| T_DEAL_DP | Company code / securities account        | Securities only  |
| T_DEAL_AG | Company code / authorization group       | All transactions (unused in cloud — apply same logic as T_DEAL_PD if present; do not add manually if absent) |

---

## ACTVT Values (all domains)

| ACTVT | Meaning       | T_DEAL_* | T_TOE_HR |
|-------|---------------|:--------:|:--------:|
| 01    | Create        | ✓        | ✓        |
| 02    | Edit/Change   | ✓        | ✓        |
| 03    | Display       | ✓        | ✓        |
| 06    | Delete        |          | ✓        |
| 16    | Execute       | ✓        |          |
| 43    | Release       |          | ✓        |
| 85    | Reverse       | ✓        | ✓        |
| AB    | Settle        | ✓        |          |
| KU    | Give Notice   | ✓        |          |
| VF    | Expired       | ✓        |          |

### TRFCT values (T_DEAL_* only)

| TRFCT | Meaning    |
|-------|------------|
| D1    | Order      |
| D2    | Contract   |
| D3    | Settlement |

---

## Forbidden Combinations

### T_DEAL_* — FOE / BOE matrix

| TRFCT | ACTVT | FOE | BOE | Meaning                  |
|-------|-------|:---:|:---:|--------------------------|
| D2    | 01    |     | ✗   | Create contract          |
| D2    | 02    |     | ✗   | Edit contract            |
| D2    | 16    |     | ✗   | Execute contract         |
| D2    | 85    |     | ✗   | Reverse contract         |
| D2    | AB    | ✗   |     | Settle contract          |
| D2    | KU    |     | ✗   | Give Notice on contract  |
| D2    | VF    |     | ✗   | Expire contract          |
| D3    | 01    | ✗   |     | Create settlement        |
| D3    | 85    | ✗   |     | Reverse settlement       |

```
is_forbidden(FOE): (D3 AND actvt IN 01,85) OR (D2 AND actvt=AB)
is_forbidden(BOE): D2 AND actvt IN 01,02,16,85,KU,VF
```

### T_TOE_HR — MOE / Accountant matrix

| HREQ_CAT | ACTVT | MOE | Accountant | Meaning                           |
|----------|-------|:---:|:----------:|-----------------------------------|
| A        | 01    |     | ✗          | Create manual designation request |
| A        | 02    |     | ✗          | Change manual designation request |
| A        | 06    |     | ✗          | Delete manual designation request |
| A        | 43    | ✗   |            | Release manual designation request|
| A        | 85    | ✗   |            | Reverse manual designation request|
| D        | 01    |     | ✗          | Create dedesignation request      |
| D        | 02    |     | ✗          | Change dedesignation request      |
| D        | 06    |     | ✗          | Delete dedesignation request      |
| D        | 43    | ✗   |            | Release dedesignation request     |
| D        | 85    | ✗   |            | Reverse dedesignation request     |

```
is_hr_forbidden(MOE):        hreq_cat IN (A,D) AND actvt IN (43,85)
is_hr_forbidden(Accountant): hreq_cat IN (A,D) AND actvt IN (01,02,06)
```

Note: Categories G, O, S are unrestricted — both roles may hold all activities for those.

---

## TRFCT Patterns in Existing Apps

| App suffix | TRFCT (active T_DEAL_PD) | Office |
|------------|--------------------------|--------|
| `_B_`      | D3 (Settlement)          | BOE    |
| `_F_`      | D1, D2 (Order, Contract) | FOE    |

---

## Business Role Templates

Core global Treasury BRTs (country variants like `_CN`, `_SG`, `_TH` follow the same catalog pattern):

| BRT ID                          | Display Name                      | Office | Key Catalogs |
|---------------------------------|-----------------------------------|--------|--------------|
| `SAP_BR_TREASURY_SPECIALIST_FOE` | Treasury Specialist - Front Office | FOE   | `SAP_FIN_BC_TRM_FT_CCP_1_PC`, `SAP_FIN_BC_TRM_FT_DE_F_PC`, `SAP_FIN_BC_TRM_FT_FX_F_PC`, `SAP_FIN_BC_TRM_FT_MM_F_PC`, `SAP_FIN_BC_TRM_FTDECP_1_PC`, `SAP_FIN_BC_TRM_FTFXCP_1_PC`, `SAP_FIN_BC_TRM_FTMMCP_1_PC`, `SAP_FIN_BC_TRM_FT_CLA_PC` |
| `SAP_BR_TREASURY_SPECIALIST_BOE` | Treasury Specialist - Back Office  | BOE   | `SAP_FIN_BC_TRM_POS_MGT_PC`, `SAP_FIN_BC_TRM_CTR_PC`, `SAP_FIN_BC_TRM_COR_PC`, `SAP_FIN_BC_TRM_FT_CCP_2_PC`, `SAP_FIN_BC_TRM_FTDECP_2_PC`, `SAP_FIN_BC_TRM_FTFXCP_2_PC`, `SAP_FIN_BC_TRM_FTMMCP_2_PC`, + others |
| `SAP_BR_TREASURY_SPECIALIST_MOE` | Treasury Specialist - Middle Office | MOE  | `SAP_FIN_BC_TRM_EXP_POS_PC`, `SAP_FIN_BC_TRM_MR_ANLYS_PC`, `SAP_FIN_BC_TRM_RAW_EXP_PC`, `SAP_FIN_BC_TRM_VAL_PC`, `SAP_FIN_BC_TRM_AJ_TSMO_PC`, `SAP_FIN_BC_HEDGE_MGT_PC` |
| `SAP_BR_TREASURY_ACCOUNTANT`     | Treasury Accountant               | BOE   | `SAP_FIN_BC_TRM_ACCT_PC`, `SAP_FIN_BC_TRM_ACCT_PST_PC`, `SAP_FIN_BC_TRM_VAL_PC`, `SAP_FIN_BC_TRM_POS_MGT_PC`, `SAP_FIN_BC_TRM_POS_IND_PC`, + others |
| `SAP_BR_TREASURY_RISK_MANAGER`   | Treasury Risk Manager             | Mixed | `SAP_FIN_BC_TRM_ANLYTS_PC`, `SAP_FIN_BC_TRM_ADMIN_PC`, `SAP_FIN_BC_TRM_FT_TAUTH_PC`, + others |

Query to get full catalog list for a BRT:
```sql
SELECT BU_CATALOG_ID, BRT_ID FROM APS_IAM_W_BRTBUC WHERE BRT_ID = '<BRT_ID>'
```

---

## Workflow

### Step 1 — Discover Treasury Apps

```sql
SELECT PGMID, OBJECT, OBJ_NAME FROM TADIR
WHERE DEVCLASS = 'CLOUD_FI_TR_IAM' AND OBJECT = 'SIA6'
UP TO 500 ROWS
```

Then fetch details and descriptions (separate queries per prefix — `FTR%`, `TM%`, `TS%`, etc.):

```sql
SELECT APP_ID, TCODE, APP_TYPE, READ_ONLY, SCOPE_DEPENDENT FROM APS_IAM_W_APP
WHERE APP_ID LIKE 'FTR%' UP TO 200 ROWS
```

```sql
SELECT APP_ID, TEXT FROM APS_IAM_W_APPT
WHERE APP_ID LIKE 'FTR%' AND LANGU = 'E' UP TO 200 ROWS
```

### Step 2 — Catalog Assignments

```sql
SELECT APP_ID, CAT_ID FROM SUI_TM_MM_APP
WHERE APP_ID LIKE 'FTR%' UP TO 200 ROWS
```

Current catalog inventory (as of 2026-04-10):

| Catalog ID                 | Apps | Notes                           |
|----------------------------|------|---------------------------------|
| `SAP_TC_FIN_TRM_COMMON`    | 53   | Main — mixed FOE/BOE, not split |
| `SAP_TC_FIN_TRM_CE_COMMON` | 1    | Treasury Executive Dashboard    |

No `_F_PC` / `_B_PC` split catalogs exist yet.

### Step 3 — Read Auth Object Instances for an App

```sql
SELECT APP_ID, UUID, AUTH_OBJECT, STATUS, INACTIVE
FROM APS_IAM_W_APPAUI WHERE APP_ID = '<APP_ID>'
```

Active instances: `INACTIVE` = blank. Relevant objects: `T_DEAL_PD`, `T_DEAL_PF`, `T_DEAL_DP`, `T_DEAL_AG`.

### Step 4 — Read Auth Values (TRFCT + ACTVT)

```sql
SELECT UUID, PARENT_ID, FIELD, LOW_VALUE, HIGH_VALUE, STATUS
FROM APS_IAM_W_APPAUV WHERE APP_ID = '<APP_ID>'
```

Match `PARENT_ID` to UUID from Step 3. Only consider instances where `INACTIVE` = blank.

### Step 5 — Evaluate FOE/BOE Catalog Assignment

1. If catalog already has `_F_`/`_B_` suffix → validate only the applicable ruleset.
2. If no suffix → evaluate both rulesets against all apps' auth values.
3. If violation found → split the catalog:
   - FOE: original name + `_F_PC` (or `_1_PC` if length requires)
   - BOE: original name + `_B_PC` (or `_2_PC` if length requires)
   - Redistribute apps; document apps compatible with both.

### Step 6 — Validate an App's SoD Compliance

1. Get all active `T_DEAL_*` instances (`INACTIVE` = blank, status `M` or `S`).
2. Collect all TRFCT values and all ACTVT values from APPAUV for each instance.
3. Form the Cartesian product TRFCT × ACTVT per instance.
4. Check every pair against the forbidden matrix for the target catalog type.
5. Report violations:

```
App: FTRCAI02_B_TRAN  Target: FOE
AUTH_OBJECT  UUID                              TRFCT  ACTVT  Violation
T_DEAL_PD    42010AEEC8811FD0B8F6FEFC193980A7  D3     01     FOE: D3+01 forbidden
```

---

## Hedge Request Management SoD

Governed by auth object **`T_TOE_HR`** — independent of `T_DEAL_*`.

Fields: **HREQ_CAT** (hedge request category), **ACTVT** (activity).

### HREQ_CAT values

| HREQ_CAT | Meaning            |
|----------|--------------------|
| A        | Manual Designation |
| D        | Dedesignation      |
| G        | FX Hedge           |
| O        | Offsetting         |
| S        | FX Swap            |

### Role Split

| Role           | Description                                                                 | Catalogs |
|----------------|-----------------------------------------------------------------------------|----------|
| **MOE**        | All hedge request actions **except** release/reverse of A and D categories  | `SAP_FIN_BC_HEDGE_MGT_PC` (→ `SAP_BR_TREASURY_SPECIALIST_MOE`) |
| **Accountant** | Only release and reverse-release of dedesignation (D) requests              | `SAP_FIN_BC_HEDGE_ACCT_P_PC` (→ `SAP_BR_TREASURY_ACCOUNTANT`, `SAP_BR_TREASURY_SPECIALIST_BOE`) |

See the T_TOE_HR forbidden matrix above.

### Hedge SoD Workflow

Same as Steps 3–4 but:
- In Step 3: filter `AUTH_OBJECT = 'T_TOE_HR'`
- In Step 4: filter `FIELD IN ('HREQ_CAT', 'ACTVT')`

Then form the Cartesian product HREQ_CAT × ACTVT per active instance and check against the MOE/Accountant forbidden matrix. Report:

```
APP_ID | AUTH_OBJECT | UUID | HREQ_CAT | ACTVT | Rule violated (MOE/Accountant)
```
