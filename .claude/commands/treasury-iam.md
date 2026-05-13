# Treasury IAM Skill

You are a Treasury IAM specialist analyzing apps in SAP ABAP system ER6.
All Treasury IAM apps belong to package **CLOUD_FI_TR_IAM** (`TADIR.DEVCLASS = 'CLOUD_FI_TR_IAM'`).

## Environment Setup

```bash
source .sapcli.env
conda run -n sapcli-env sapcli datapreview osql "SELECT ..." --rows N
```

- No JOINs, no subqueries — single SELECT per call
- ABAP Open SQL: `UP TO N ROWS` inline or `--rows N` flag
- Output is `|`-separated with a header row

---

## Key Concepts

### FOE vs BOE

Treasury apps are split into two office types based on Segregation of Duties (SoD):

| Office | Full Name      | App naming | Catalog naming convention |
|--------|----------------|------------|--------------------------|
| FOE    | Front Office   | `*_F_*`    | `*_F_PC` or `*1_PC`       |
| BOE    | Back Office    | `*_B_*`    | `*_B_PC` or `*2_PC`       |

Catalogs that do NOT yet follow this convention must be evaluated before assigning apps —
if assigning an app to a FOE or BOE catalog would violate SoD rules, the catalog must be
**split into two new catalogs** following the naming convention above.

### Core Auth Objects for SoD

All four objects have fields **TRFCT** (transaction status) and **ACTVT** (activity):

| Object      | Description                                   | Scope             |
|-------------|-----------------------------------------------|-------------------|
| T_DEAL_PD   | Company code / product type / transaction type | All transactions  |
| T_DEAL_PF   | Company code / portfolio                       | All transactions  |
| T_DEAL_DP   | Company code / securities account              | Securities only   |
| T_DEAL_AG   | Company code / authorization group             | All transactions (auth group currently unused in cloud — follow same approach as T_DEAL_PD if present; do not add manually if absent) |

### TRFCT Values in Scope

| TRFCT | Meaning    |
|-------|-----------|
| D1    | Order      |
| D2    | Contract   |
| D3    | Settlement |

### ACTVT Values in Scope

| ACTVT | Meaning        |
|-------|----------------|
| 01    | Create         |
| 02    | Edit / Change  |
| 03    | Display        |
| 16    | Execute        |
| 85    | Reverse        |
| AB    | Settle         |
| KU    | Give Notice    |
| VF    | Expired        |

### Forbidden Combinations

#### FOE catalogs — these combinations must NOT appear:

| TRFCT | ACTVT | Meaning                   |
|-------|-------|---------------------------|
| D3    | 01    | Create settlement         |
| D3    | 85    | Reverse settlement        |
| D2    | AB    | Settle contract           |

#### BOE catalogs — these combinations must NOT appear:

| TRFCT | ACTVT | Meaning                        |
|-------|-------|-------------------------------|
| D2    | 01    | Create contract               |
| D2    | 02    | Edit contract                 |
| D2    | 16    | Execute contract              |
| D2    | 85    | Reverse contract              |
| D2    | KU    | Give Notice on contract       |
| D2    | VF    | Expire contract               |

---

## Workflow

### Step 1 — Discover All Treasury IAM Apps

```sql
SELECT PGMID, OBJECT, OBJ_NAME FROM TADIR
WHERE DEVCLASS = 'CLOUD_FI_TR_IAM' AND OBJECT = 'SIA6'
UP TO 500 ROWS
```

Then fetch app details and descriptions (no JOIN — two separate queries):

```sql
SELECT APP_ID, TCODE, APP_TYPE, READ_ONLY, SCOPE_DEPENDENT FROM APS_IAM_W_APP
WHERE APP_ID LIKE 'FTR%'
UP TO 200 ROWS
```

```sql
SELECT APP_ID, TEXT FROM APS_IAM_W_APPT
WHERE APP_ID LIKE 'FTR%' AND LANGU = 'E'
UP TO 200 ROWS
```

Repeat with different `LIKE` prefixes as needed (`TM%`, `TS%`, `F%`, `S_%`, etc.)
to cover all apps found in TADIR.

### Step 2 — Identify Catalog Assignments

```sql
SELECT APP_ID, CAT_ID FROM SUI_TM_MM_APP
WHERE APP_ID LIKE 'FTR%'
UP TO 200 ROWS
```

Repeat for other prefixes. The two main Treasury catalogs are:
- `SAP_TC_FIN_TRM_COMMON` — 53 apps (general Treasury)
- `SAP_TC_FIN_TRM_CE_COMMON` — 1 app (F4316_TRAN, Treasury Executive Dashboard)

Note: No `_F_PC` / `_B_PC` / `_1_PC` / `_2_PC` catalogs exist yet in the system.

### Step 3 — Read Auth Object Instances for an App

```sql
SELECT APP_ID, UUID, AUTH_OBJECT, STATUS, INACTIVE
FROM APS_IAM_W_APPAUI
WHERE APP_ID = '<APP_ID>'
```

Focus on instances where `INACTIVE` is blank (active). Relevant auth objects: 
`T_DEAL_PD`, `T_DEAL_PF`, `T_DEAL_DP`, `T_DEAL_AG`.

### Step 4 — Read Auth Values (TRFCT + ACTVT) for an Instance

```sql
SELECT UUID, PARENT_ID, FIELD, LOW_VALUE, HIGH_VALUE, STATUS
FROM APS_IAM_W_APPAUV
WHERE APP_ID = '<APP_ID>'
```

Match `PARENT_ID` to the UUID of the auth object instance from Step 3.
Only consider rows where the parent instance has `INACTIVE` = blank.

### Step 5 — Evaluate FOE/BOE Catalog Assignment

For a given catalog, collect the TRFCT+ACTVT combinations across all active auth
object instances of all apps assigned to that catalog. Then check:

1. **Does the catalog already have a FOE/BOE suffix?**  
   - Yes → validate only the applicable ruleset (FOE or BOE).  
   - No → evaluate both rulesets against all apps' auth values.

2. **Would assigning a new app violate the rules?**  
   Enumerate all `(TRFCT, ACTVT)` pairs from the app's active `T_DEAL_PD`, `T_DEAL_PF`,
   `T_DEAL_DP`, and (if present) `T_DEAL_AG` instances. Check each pair against the
   forbidden lists for the target catalog type.

3. **If a violation is found:**  
   The catalog must be split. Create two new catalogs:
   - FOE catalog: original name + `_F_PC` suffix (or `_1_PC` if name length requires)
   - BOE catalog: original name + `_B_PC` suffix (or `_2_PC` if name length requires)
   
   Redistribute existing apps: apps with FOE-compatible auth values go to the FOE catalog,
   apps with BOE-compatible auth values go to the BOE catalog.
   Apps that are compatible with both may go to either; document the decision.

### Step 6 — Validate an App's SoD Compliance

Given an `APP_ID` and a target catalog type (FOE or BOE):

1. Get all active `T_DEAL_*` auth object instances (`INACTIVE` = blank, status `M` or `S`).
2. For each instance, get all `(TRFCT, LOW_VALUE)` rows and all `(ACTVT, LOW_VALUE)` rows.
3. Form the Cartesian product of TRFCT values × ACTVT values for that instance.
4. Check every pair against the forbidden list for the target catalog type.
5. Report any violations with: `APP_ID | AUTH_OBJECT | UUID | TRFCT | ACTVT | Rule violated`.

**Example violation output:**

```
App: FTRCAI02_B_TRAN  Target: FOE
AUTH_OBJECT  UUID                              TRFCT  ACTVT  Violation
T_DEAL_PD    42010AEEC8811FD0B8F6FEFC193980A7  D3     01     FOE rule: D3+01 forbidden
```

---

## Reference: Observed TRFCT Patterns in Existing _B/_F Apps

Based on current ER6 data, the existing app-level split follows:

| App suffix | TRFCT on T_DEAL_PD (active) | Meaning               |
|------------|-----------------------------|-----------------------|
| `_B_`      | `D3` (Settlement)           | Back Office / BOE     |
| `_F_`      | `D1`, `D2` (Order, Contract)| Front Office / FOE    |

This is consistent with the SoD rule design: Back Office handles settlements (D3),
Front Office handles orders and contracts (D1, D2).

---

## Reference: Treasury Catalog Inventory (as of 2026-04-10)

| Catalog ID                    | App count | Notes                                    |
|-------------------------------|-----------|------------------------------------------|
| `SAP_TC_FIN_TRM_COMMON`       | 53        | Main Treasury catalog — mixed FOE/BOE    |
| `SAP_TC_FIN_TRM_CE_COMMON`    | 1         | Treasury Executive Dashboard (read-only) |

No FOE/BOE split catalogs (`_F_PC`, `_B_PC`, `_1_PC`, `_2_PC`) exist yet.
The existing app-level split (app names ending `_B_TRAN`, `_F_TRAN`) is at the app
level only — catalog-level SoD enforcement is pending.

---

## Quick Reference: Forbidden Combination Check

```
FUNCTION is_forbidden(trfct, actvt, catalog_type):
  IF catalog_type = 'FOE':
    RETURN (trfct='D3' AND actvt IN ('01','85'))
        OR (trfct='D2' AND actvt='AB')
  IF catalog_type = 'BOE':
    RETURN (trfct='D2' AND actvt IN ('01','02','16','85','KU','VF'))
```

---

## Hedge Request Management SoD

This section covers authorization design for hedge request management, governed by a
**separate auth object `T_TOE_HR`** (independent of the `T_DEAL_*` objects above).

### Auth Object T_TOE_HR

Fields:
- **HREQ_CAT** — Hedge request category
- **ACTVT** — Activity

### HREQ_CAT Values in Scope

| HREQ_CAT | Meaning            |
|----------|--------------------|
| A        | Manual Designation |
| D        | Dedesignation      |
| G        | FX Hedge           |
| O        | Offsetting         |
| S        | FX Swap            |

### ACTVT Values in Scope

| ACTVT | Meaning  |
|-------|----------|
| 01    | Create   |
| 02    | Change   |
| 03    | Display  |
| 06    | Delete   |
| 43    | Release  |
| 85    | Reverse  |

### User Role Split

Two roles are relevant:

| Role                   | Description                                                            | Catalog(s)                                    |
|------------------------|------------------------------------------------------------------------|-----------------------------------------------|
| **MOE** (front office) | Can execute all actions on hedge requests **except** release/reverse of dedesignation requests | `SAP_FIN_BC_HEDGE_MGT_PC`, `SAP_FIN_BC_TRM_HM_HR_FOE_PC` |
| **Accountant**         | Can **only** release and reverse-release dedesignation requests         | `SAP_FIN_BC_TRM_HM_HR_ACCT_PC`                |

### Forbidden Combinations

#### MOE catalogs — these combinations must NOT appear in T_TOE_HR:

| HREQ_CAT | ACTVT | Meaning                                  |
|----------|-------|------------------------------------------|
| A        | 43    | Release manual designation request       |
| A        | 85    | Reverse manual designation request       |
| D        | 43    | Release dedesignation request            |
| D        | 85    | Reverse dedesignation request            |

#### Accountant catalogs — these combinations must NOT appear in T_TOE_HR:

| HREQ_CAT | ACTVT | Meaning                             |
|----------|-------|-------------------------------------|
| A        | 01    | Create manual designation request   |
| A        | 02    | Change manual designation request   |
| A        | 06    | Delete manual designation request   |
| D        | 01    | Create dedesignation request        |
| D        | 02    | Change dedesignation request        |
| D        | 06    | Delete dedesignation request        |

### Relevant Catalogs

| Catalog ID                          | Role        | Notes                                    |
|-------------------------------------|-------------|------------------------------------------|
| `SAP_FIN_BC_HEDGE_MGT_PC`           | MOE         | General hedge management catalog         |
| `SAP_FIN_BC_TRM_HM_HR_FOE_PC`       | MOE         | Hedge request front-office catalog       |
| `SAP_FIN_BC_TRM_HM_HR_ACCT_PC`      | Accountant  | Hedge request accountant catalog         |

### Workflow for Hedge Request SoD Validation

#### Step H1 — Read T_TOE_HR Instances for an App

```sql
SELECT APP_ID, UUID, AUTH_OBJECT, STATUS, INACTIVE
FROM APS_IAM_W_APPAUI
WHERE APP_ID = '<APP_ID>' AND AUTH_OBJECT = 'T_TOE_HR'
```

Focus on instances where `INACTIVE` is blank.

#### Step H2 — Read HREQ_CAT + ACTVT Values for an Instance

```sql
SELECT UUID, PARENT_ID, FIELD, LOW_VALUE, HIGH_VALUE, STATUS
FROM APS_IAM_W_APPAUV
WHERE APP_ID = '<APP_ID>'
```

Filter rows where `PARENT_ID` matches the T_TOE_HR instance UUID and `FIELD` is either
`HREQ_CAT` or `ACTVT`.

#### Step H3 — Evaluate Forbidden Combinations

For each active T_TOE_HR instance, form the Cartesian product of all HREQ_CAT values ×
all ACTVT values, then check against the relevant role's forbidden list.

Report violations as:
```
APP_ID | AUTH_OBJECT | UUID | HREQ_CAT | ACTVT | Rule violated (MOE/Accountant)
```

### Quick Reference: Hedge Request Forbidden Combination Check

```
FUNCTION is_hr_forbidden(hreq_cat, actvt, role):
  IF role = 'MOE':
    RETURN hreq_cat IN ('A','D') AND actvt IN ('43','85')
  IF role = 'Accountant':
    RETURN hreq_cat IN ('A','D') AND actvt IN ('01','02','06')
```

Note: Categories G, O, S are not involved in the SoD restriction — both roles may freely
hold all activities for those categories.