
# Treasury IAM Skill

You are a Treasury IAM specialist analyzing apps in SAP ABAP system ER6.
All Treasury IAM apps belong to package **CLOUD_FI_TR_IAM** (`TADIR.DEVCLASS = 'CLOUD_FI_TR_IAM'`).

Use the MCP tools (`mcp__er6__query_sql`, etc.) for all ER6 queries. ABAP Open SQL — no JOINs, no subqueries. Use the `rows` parameter for row limits; do **not** use `UP TO N ROWS` inline when a `WHERE` clause is present.


## Quick Start

| Question | Go to |
|----------|-------|
| Is this app FOE or BOE? | Workflows → Single-app SoD validation (Steps 3–4) → TRFCT patterns table |
| Does this catalog need splitting? | Workflows → Catalog FOE/BOE split analysis |
| Validate an app's SoD compliance | Workflows → Single-app SoD validation |
| Audit a whole BRT | Workflows → Whole-BRT audit |
| Hedge request SoD (T_TOE_HR) | Workflows → Hedge request SoD — **MOE / Accountant only** |
| I see an unusual auth object | Authorization Objects Reference |
| Something looks wrong in my result | Troubleshooting & Validation Tips |


## FOE vs BOE

Treasury apps are split by Segregation of Duties (SoD):

| Office | Full Name    | App naming | Catalog naming |
|--------|--------------|------------|----------------|
| FOE    | Front Office | `*_F_*`    | `*_F_PC` / `*1_PC` |
| BOE    | Back Office  | `*_B_*`    | `*_B_PC` / `*2_PC` |

Catalogs without a FOE/BOE suffix must be evaluated — if assigning an app would violate SoD, the catalog must be **split** into two new catalogs following the naming convention above.


## ACTVT Values

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


## TRFCT Patterns in Existing Apps

| App suffix | TRFCT (active T_DEAL_PD) | Office |
|------------|--------------------------|--------|
| `_B_`      | D3 (Settlement)          | BOE    |
| `_F_`      | D1, D2 (Order, Contract) | FOE    |


## Workflows

### Single-app SoD validation

**Input:** App ID (e.g. `FTRCAI02_F_TRAN`)
**Output:** Verdict (FOE-compliant / BOE-compliant / BOTH / NEITHER) + violation table

#### Step 1 — Discover Treasury Apps

```sql
SELECT PGMID, OBJECT, OBJ_NAME FROM TADIR
WHERE DEVCLASS = 'CLOUD_FI_TR_IAM' AND OBJECT = 'SIA6'
```
(pass `rows=500` parameter)

Then fetch app details by prefix (`FTR%`, `TM%`, `TS%`):

```sql
SELECT APP_ID, TCODE, APP_TYPE, READ_ONLY FROM APS_IAM_W_APP
WHERE APP_ID LIKE 'FTR%'
```

```sql
SELECT APP_ID, TEXT FROM APS_IAM_W_APPT
WHERE APP_ID LIKE 'FTR%' AND LANGU = 'E'
```
(pass `rows=200` per query)

#### Step 2 — Catalog Assignments

Use `APS_IAM_W_BC_APP` — `SUI_TM_MM_APP` stores Treasury app IDs as GUIDs and cannot be filtered by SIA6 name.

```sql
SELECT BU_CATALOG_ID, APP_ID FROM APS_IAM_W_BC_APP
WHERE APP_ID = '<APP_ID>'
```

To list all apps in a catalog:
```sql
SELECT BU_CATALOG_ID, APP_ID FROM APS_IAM_W_BC_APP
WHERE BU_CATALOG_ID = '<CATALOG_ID>'
```

#### Step 3 — Read Auth Object Instances

```sql
SELECT APP_ID, UUID, AUTH_OBJECT, STATUS, INACTIVE
FROM APS_IAM_W_APPAUI WHERE APP_ID = '<APP_ID>'
```

Active instances: `INACTIVE` = blank. Relevant objects: `T_DEAL_PD`, `T_DEAL_PF`, `T_DEAL_DP`, `T_DEAL_AG`.

#### Step 4 — Read Auth Values (TRFCT + ACTVT)

```sql
SELECT UUID, PARENT_ID, FIELD, LOW_VALUE, HIGH_VALUE, STATUS
FROM APS_IAM_W_APPAUV WHERE APP_ID = '<APP_ID>'
```

Match `PARENT_ID` to UUID from Step 3. Only instances where `INACTIVE` = blank.

#### Step 5 — Evaluate FOE/BOE Catalog Assignment

1. If catalog already has `_F_`/`_B_` suffix → validate only the applicable ruleset.
2. If no suffix → evaluate both rulesets against all apps' auth values.
3. If violation found → split the catalog:
   - FOE: original name + `_F_PC` (or `_1_PC` if length requires)
   - BOE: original name + `_B_PC` (or `_2_PC` if length requires)
   - Redistribute apps; document apps compatible with both.

#### Step 6 — Validate SoD Compliance

1. Get all active `T_DEAL_*` instances (`INACTIVE` = blank).
2. Collect all TRFCT values and all ACTVT values from APPAUV for each instance.
3. Form the Cartesian product TRFCT × ACTVT per instance.
4. Check every pair against the forbidden matrix for the target catalog type.
5. Report violations:

```
App: FTRCAI02_B_TRAN  Target: FOE
AUTH_OBJECT  UUID                              TRFCT  ACTVT  Violation
T_DEAL_PD    42010AEEC8811FD0B8F6FEFC193980A7  D3     01     FOE: D3+01 forbidden
```


### Whole-BRT audit

**Input:** BRT ID (e.g. `SAP_BR_TREASURY_SPECIALIST_FOE`)
**Output:** All SoD violations across all catalogs and apps assigned to the BRT

1. Get all catalogs for the BRT:
```sql
SELECT BU_CATALOG_ID, BRT_ID FROM APS_IAM_W_BRTBUC
WHERE BRT_ID = '<BRT_ID>'
```

2. For each catalog, get its apps:
```sql
SELECT APP_ID, BU_CATALOG_ID FROM APS_IAM_W_BC_APP
WHERE BU_CATALOG_ID = '<CATALOG_ID>'
```

3. For each app, run Steps 3–6 of Single-app validation. Determine the expected office from the BRT (FOE BRT → validate against FOE ruleset; BOE BRT → BOE ruleset; mixed BRT → validate both).

4. Aggregate results. Report:
```
BRT: SAP_BR_TREASURY_SPECIALIST_FOE
Catalogs audited: 14  Apps audited: 47  Violations found: 3

APP_ID               CATALOG_ID                    AUTH_OBJECT  TRFCT  ACTVT  Violation
FTRCAI02_F_TRAN      SAP_FIN_BC_TRM_FT_CCP_1_PC   T_DEAL_PD    D3     01     FOE: D3+01
...
```


### Pre/post-migration diff

**Input:** App ID and two points in time (before/after a transport or config change)
**Output:** Which auth values changed and whether the change affects SoD posture

Since ER6 does not store history natively, this workflow compares a saved baseline (from `/memo`) with the current live state.

1. Run Step 3–4 queries now and record results.
2. Load the saved baseline from the memo.
3. Compare instance-by-instance:
   - New UUID: newly added auth instance — evaluate for SoD
   - Missing UUID: removed instance — was it a violation? If yes, violation resolved.
   - Changed value: same UUID, different LOW_VALUE/HIGH_VALUE — re-evaluate the Cartesian product

4. Report only the delta:
```
App: FTRCAI02_B_TRAN  Transport: TR1000123
ADDED:   T_DEAL_PD UUID=A3B4... TRFCT=D2 ACTVT=01 → NEW BOE VIOLATION (D2+01)
REMOVED: T_DEAL_PF UUID=C5D6... TRFCT=D3 ACTVT=85 → Violation cleared
```


### Reverse inference: SQL result → SoD verdict

Use when you already have a TRFCT/ACTVT value from a query and need to know what it means for SoD.

1. Identify the auth object (`T_DEAL_PD`, `T_DEAL_PF`, `T_DEAL_DP`, or `T_TOE_HR`).
2. For `T_DEAL_*`: look up the (TRFCT, ACTVT) pair in the FOE/BOE matrix.
3. For `T_TOE_HR`: look up the (HREQ_CAT, ACTVT) pair in the MOE/Accountant matrix.
4. If the pair appears in the forbidden column for the target role, it is a violation.
5. If not in the matrix, it is either neutral (D1+01 = create order — FOE-allowed) or a display value (ACTVT=03 — always allowed for all roles).

Example:
```
Observed: T_DEAL_PD, TRFCT=D2, ACTVT=AB on app FTRCAI02_F_TRAN
Matrix lookup: D2+AB → FOE forbidden (Settle contract)
Verdict: App FTRCAI02_F_TRAN violates FOE SoD — FOE user can settle contracts
```


## Appendix: Live ER6 evidence (2026-06-03)

### Distinct auth objects observed in active Treasury IAM app instances

The following query, run against ER6 on 2026-06-03, returns the distinct auth objects present in active (non-inactive) instances across Treasury IAM apps:

```sql
SELECT AUTH_OBJECT, STATUS FROM APS_IAM_W_APPAUI
WHERE APP_ID LIKE 'FTR%' AND INACTIVE = ''
```
(repeat with `APP_ID LIKE 'TM%'` and `APP_ID LIKE 'TS%'`)

Auth objects observed (categorized):

| Category | Objects |
|----------|---------|
| SoD-critical | `T_DEAL_PD`, `T_DEAL_PF`, `T_DEAL_DP`, `T_DEAL_AG`, `T_TOE_HR` |
| Indirect SoD | `T_DEAL_LC`, `T_BP_DEAL`, `T_POS_ASS`, `T_HREL_AUT`, `FW_BES_BUK` |
| Position/Exposure | `T_TEX_POS`, `T_TEX_REXP`, `T_EXT_SEC`, `T_STAM_GAT`, `T_DEPOT`, `T_ASGTTMPL` |
| Valuation | `F_T_VTBLV`, `F_T_NPV`, `F_T_TRANSB` |
| FI cross-cutting | `F_BKPF_BUK`, `F_BKPF_KOA`, `F_BKPF_BES`, `F_INFO_BUK`, `F_BUK_BUPL`, `F_FAGL_LEV`, `F_FAGL_LDR`, `F_BNKA_BUK`, `F_SKA1_BUK`, `F_BUKRS_MD` |
| Business partner | `B_BUPA_CRS`, `B_BUPA_RLT`, `B_BUPA_RAT`, `B_BUPA_GRP`, `B_BUPR_BZT` |
| Cash Management | `F_CLM_BAM` |
| CO/PS | `K_CSKS`, `K_CCA`, `K_PCA`, `K_PCA_MD`, `/S4PPM/PR1`, `C_PRPS_ART` |
| Generic/Utility | `S_TABU_NAM`, `S_APPL_LOG`, `S_SCD0_OBJ` |
| Custom namespace | `/TMF/SHAEX` |

All objects classified as "No" SoD relevance in the Authorization Objects Reference section above can be skipped during a standard Treasury SoD audit.

### BRT catalog inventory (as of 2026-06-03)

Full catalog-to-BRT mapping is in `APS_IAM_W_BRTBUC`. As of the live query:
- `SAP_BR_TREASURY_SPECIALIST_FOE`: 11 distinct global BRTs queried → 26 catalog assignments
- `SAP_BR_TREASURY_SPECIALIST_BOE`: largest footprint — 40+ catalog assignments including market data, payment, correspondence, and securities catalogs
- `SAP_BR_TREASURY_SPECIALIST_MOE`: 14 catalog assignments including hedge management, exposure, market risk
- `SAP_BR_TREASURY_ACCOUNTANT`: 18 catalog assignments
- `SAP_BR_TREASURY_RISK_MANAGER`: 12 catalog assignments

Country variants add 1–5 additional catalogs each (country-specific payment, compliance, or local tax apps).
