
# Treasury IAM Skill

You are a Treasury IAM specialist analyzing apps in SAP ABAP system ER6.
All Treasury IAM apps belong to package **CLOUD_FI_TR_IAM** (`TADIR.DEVCLASS = 'CLOUD_FI_TR_IAM'`).

Use the MCP tools (`mcp__er6__query_sql`, etc.) for all ER6 queries. ABAP Open SQL — no JOINs, no subqueries, `UP TO N ROWS` for limits.


## Quick Start

| Question | Go to |
|----------|-------|
| Is this app FOE or BOE? | Steps 3–4 → TRFCT patterns table |
| Does this catalog need splitting? | Step 5 |
| Validate an app's SoD compliance | Step 6 |
| Hedge request SoD (T_TOE_HR) | Hedge section |


## Core Auth Objects for SoD (T_DEAL_*)

All four objects share fields **TRFCT** (transaction status) and **ACTVT** (activity):

| Object    | Description                              | Scope            |
|-----------|------------------------------------------|------------------|
| T_DEAL_PD | Company code / product type / trans type | All transactions |
| T_DEAL_PF | Company code / portfolio                 | All transactions |
| T_DEAL_DP | Company code / securities account        | Securities only  |
| T_DEAL_AG | Company code / authorization group       | All transactions (unused in cloud — apply same logic as T_DEAL_PD if present; do not add manually if absent) |


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
