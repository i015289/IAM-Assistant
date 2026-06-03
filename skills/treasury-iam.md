---
name: treasury-iam
description: Use this skill when the user asks about Treasury IAM, apps in package CLOUD_FI_TR_IAM, FOE/BOE catalog assignments, SoD rules for T_DEAL_* authorization objects, catalog splitting for Front Office / Back Office segregation, or hedge request management SoD (T_TOE_HR, MOE vs Accountant role split).
---

# Treasury IAM Skill

You are a Treasury IAM specialist analyzing apps in SAP ABAP system ER6.
All Treasury IAM apps belong to package **CLOUD_FI_TR_IAM** (`TADIR.DEVCLASS = 'CLOUD_FI_TR_IAM'`).

Use the MCP tools (`mcp__er6__query_sql`, etc.) for all ER6 queries. ABAP Open SQL — no JOINs, no subqueries. Use the `rows` parameter for row limits; do **not** use `UP TO N ROWS` inline when a `WHERE` clause is present.

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
| Is this app FOE or BOE? | Workflows → Single-app SoD validation (Steps 3–4) → TRFCT patterns table |
| Does this catalog need splitting? | Workflows → Catalog FOE/BOE split analysis |
| Validate an app's SoD compliance | Workflows → Single-app SoD validation |
| Audit a whole BRT | Workflows → Whole-BRT audit |
| Hedge request SoD (T_TOE_HR) | Workflows → Hedge request SoD — **MOE / Accountant only** |
| I see an unusual auth object | Authorization Objects Reference |
| Something looks wrong in my result | Troubleshooting & Validation Tips |

---

## Business Context

### What Treasury IAM covers

SAP Treasury & Risk Management (`TRM`) manages the full lifecycle of financial instruments: cash, foreign exchange (FX), money market (MM), OTC derivatives (DE), securities (SEC), and trade finance (TF — letters of credit, bank guarantees). The IAM package `CLOUD_FI_TR_IAM` covers every app that participates in this lifecycle, from deal origination through settlement and accounting.

App naming convention: `FTR*` (Financial Transaction — the dominant prefix), `TM*` (Money Market / Treasury Management), `TS*` (Treasury Securities). Suffixes `_F_` = Front Office, `_B_` = Back Office; neutral apps carry neither.

### Front Office / Middle Office / Back Office

| Role | Abbreviation | Responsibility | Key auth-object concern |
|------|-------------|---------------|------------------------|
| Front Office | FOE | Originate and manage deals (D1 orders, D2 contracts) | Must NOT settle |
| Middle Office | MOE | Risk exposure, valuation, hedge accounting oversight | Must NOT release own hedge requests |
| Back Office | BOE | Settlement, accounting, confirmations, position management | Must NOT originate |
| Treasury Accountant | — | FI postings for treasury results, impairment, classification | Overlaps BOE scope; subject to hedge SoD |

### Why SoD matters in Treasury

A user who can both **originate** a deal (FOE: D2+01) and **settle** it (BOE: D3+01) can disguise unauthorized trades, conceal losses, or facilitate money laundering without a second approver. Industry and audit standards (ISAE 3402, SOX IT-General Controls) require that front-office execution and back-office settlement be held by different identities. The T_DEAL_* forbidden combinations enforce this at the authorization layer.

### Country variants and split derivation

Country-specific BRTs (`_CN` for China, `_SG` Singapore, `_TH` Thailand, `_BR` Brazil) inherit the same SoD model. They differ in:
- Catalog set (some country catalogs added, e.g. `SAP_FIN_BC_PYRQ_PM_EPIC_CN_PC`)
- Company-code scoping tightened via `BUKRS` field on `T_DEAL_*` instances
- Payment and compliance apps specific to the local regulatory environment

Apply the same FOE/BOE/MOE forbidden matrices to country variants — the SoD logic is identical.

---

## FOE vs BOE

Treasury apps are split by Segregation of Duties (SoD):

| Office | Full Name    | App naming | Catalog naming |
|--------|--------------|------------|----------------|
| FOE    | Front Office | `*_F_*`    | `*_F_PC` / `*1_PC` |
| BOE    | Back Office  | `*_B_*`    | `*_B_PC` / `*2_PC` |

Catalogs without a FOE/BOE suffix must be evaluated — if assigning an app would violate SoD, the catalog must be **split** into two new catalogs following the naming convention above.

---

## Authorization Objects Reference

### T_DEAL_* family — SoD-critical

**Objects:** `T_DEAL_PD`, `T_DEAL_PF`, `T_DEAL_DP`, `T_DEAL_AG`
**Shared fields:** `TRFCT` (transaction status: D1/D2/D3), `ACTVT`, plus object-specific scope fields (`BUKRS`, `VTBFART`, `VTBFLART`, `VTBWFART`, `RFART`, `DEPOT`)
**SoD relevance:** **Primary** — these are the objects that determine FOE vs BOE compliance
**Common in apps:** All `FTR*_F_*`, `FTR*_B_*`, `TM*_F_*`, `TM*_B_*` apps

| Object    | Description                              | Scope fields                  |
|-----------|------------------------------------------|-------------------------------|
| T_DEAL_PD | Company code / product type / trans type | BUKRS, VTBFART, VTBFLART, VTBWFART |
| T_DEAL_PF | Company code / portfolio                 | BUKRS, RFART                  |
| T_DEAL_DP | Company code / securities account        | BUKRS, DEPOT                  |
| T_DEAL_AG | Company code / authorization group       | BUKRS, VTBGRA (unused in cloud) |

`T_DEAL_AG` is not added manually in cloud deployments. If present, apply the same logic as `T_DEAL_PD`.

### T_DEAL_LC — Limit check (indirect SoD)

**Objects:** `T_DEAL_LC`
**Fields:** `TRFCT`, `ACTVT`, `BUKRS`
**SoD relevance:** **Indirect** — governs whether a user can bypass or override credit/limit checks on a deal
**Notes:** A user holding `T_DEAL_PD` D2+01 (create contract) AND `T_DEAL_LC` with override activity gains the ability to create deals that exceed approved credit limits without back-office review. Flag this combination during audits even though it is not in the core FOE/BOE matrix.

### T_BP_DEAL — Business partner deal binding (indirect SoD)

**Objects:** `T_BP_DEAL`
**Fields:** `ACTVT`, `BUKRS`
**SoD relevance:** **Indirect** — grants counterparty selection power
**Notes:** Combined with `T_DEAL_PD` D2+01 (FOE create), a user can create a contract for any counterparty without constraint. Not a standalone SoD violation, but amplifies FOE risk when counterparty master data is also modifiable.

### Position management

**Objects:** `T_POS_ASS`, `T_TEX_POS`, `T_TEX_REXP`
**Fields:** `ACTVT`, `BUKRS`
**SoD relevance:** **Indirect** — assigns and modifies exposure positions
**Common in apps:** `FTREX*`, `FTRPOSMANPROC*`, `FTRPOSINDICATOR*`
**Notes:** These objects govern who can manipulate exposure position assignments. They are not in the FOE/BOE matrix, but improper `T_POS_ASS` 02 (change) access on a BOE user who already settles can allow position manipulation to conceal settlement discrepancies. Note this in audit commentary without raising a formal SoD flag.

### Hedge accounting

**Objects:** `T_TOE_HR`, `T_HREL_AUT`
**SoD relevance:** `T_TOE_HR` = **Primary** for MOE/Accountant; `T_HREL_AUT` = Indirect
**Common in apps:** `SAP_FIN_BC_HEDGE_MGT_PC`, `SAP_FIN_BC_HEDGE_ACCT_P_PC`, `SAP_FIN_BC_HM_*`

`T_TOE_HR` governs hedge request creation, change, release, and reversal (see Forbidden Combinations → T_TOE_HR matrix).

`T_HREL_AUT` controls who can create and manage hedge relationships (the ongoing designation linking a hedging instrument to a hedged item). Not in the release/reverse SoD matrix, but flag `T_HREL_AUT` 01/02 in combination with `T_TOE_HR` A/D release activities if held by a single user — that user could self-designate and self-release.

### External securities & gateways

**Objects:** `T_EXT_SEC`, `T_STAM_GAT`, `T_DEPOT`, `T_ASGTTMPL`
**SoD relevance:** **No** — scope/access control, not SoD-relevant
**Common in apps:** Securities `FTR*SEC*`, `FTRSEC*`, external account statement apps
**Notes:** `T_DEPOT` restricts which securities accounts a user can see/act on; `T_STAM_GAT` controls external statement gateway access; `T_EXT_SEC` restricts external security IDs; `T_ASGTTMPL` governs assignment templates. These appear frequently in securities apps — do not flag them for SoD unless combined with settlement activities.

### Valuation

**Objects:** `F_T_VTBLV`, `F_T_NPV`
**Fields:** `ACTVT`, `BUKRS`
**SoD relevance:** **No** — controls display and execution of valuation runs, not deal origination/settlement
**Common in apps:** `SAP_FIN_BC_TRM_VAL_PC`, `SAP_FIN_BC_TRM_PREP_VAL_PC`
**Notes:** Valuation objects are typically read-only (ACTVT=03) for MOE. `F_T_NPV` with 01/02 grants ability to trigger NPV recalculation — not an SoD risk but relevant for audit completeness if unexpected.

### Trading & settlement cross-checks

**Objects:** `F_T_TRANSB`, `FW_BES_BUK`
**Fields:** `ACTVT`, `BUKRS`
**SoD relevance:** **Indirect** — `F_T_TRANSB` controls transaction booking display; `FW_BES_BUK` governs settlement approval
**Notes:** `FW_BES_BUK` with 01 (create/approve settlement) held by a user who also has `T_DEAL_PD` D2+01 is a BOE-extension risk. Not directly in the matrix but worth noting.

### Cross-cutting FI objects

**Objects:** `F_BKPF_BUK`, `F_BKPF_KOA`, `F_BKPF_BES`, `F_INFO_BUK`, `F_BUK_BUPL`, `F_FAGL_LEV`, `F_FAGL_LDR`, `F_BNKA_BUK`, `F_SKA1_BUK`, `F_BUKRS_MD`
**SoD relevance:** **No** for T_DEAL_* SoD; standard FI access controls
**Notes:** These appear in Treasury apps because TRM posts to FI-GL (accounting entries for treasury results). Their presence does not affect Treasury SoD evaluation. Check them only if an FI audit specifically requires it. `F_BKPF_BUK` 01/02 on an FOE user is an FI SoD concern (not Treasury SoD) — escalate to the FI IAM team.

### Business partner

**Objects:** `B_BUPA_CRS`, `B_BUPA_RLT`, `B_BUPA_RAT`, `B_BUPA_GRP`, `B_BUPR_BZT`
**SoD relevance:** **No** for Treasury SoD — standard BP access control
**Common in apps:** `FTRBP03_TRAN`, `SAP_CMD_BC_BP_DISP_PC`, `SAP_CMD_BC_SUPPLIER_DSP_PC`, `SAP_CMD_BC_CUSTOMER_DSP_PC`
**Notes:** Display-only BP access (`B_BUPA_RLT` 03) is standard for all Treasury roles. Modify access (`01`, `02`) in combination with `T_DEAL_PD` D2+01 enables self-dealing (creating a counterparty and then trading with it) — flag this combination.

### Customer & vendor master

**Objects:** `F_KNA1_BED`, `F_KNA1_APP`, `V_KNA1_VKO`, `F_LFA1_BUK`, `F_LFA1_APP`
**SoD relevance:** **No** for Treasury SoD
**Notes:** Appear occasionally in Treasury apps that integrate with SD/MM. Do not treat as SoD-relevant in a Treasury audit.

### Cash management overlap

**Objects:** `F_CLM_BAM`
**SoD relevance:** **No** — bank account management object; appears in shared Treasury/Cash apps
**Notes:** If an app appears in both Treasury and Cash Management catalogs, `F_CLM_BAM` governs bank account display. Evaluate under Cash Management IAM rules, not Treasury SoD rules.

### Cost & profit centers

**Objects:** `K_CSKS`, `K_CCA`, `K_PCA`, `K_PCA_MD`, `K_REPO_CCA`
**SoD relevance:** **No** — CO access objects, not TRM-SoD-relevant
**Notes:** Appear in Treasury apps that allocate costs to profit centers. Escalate to CO IAM if modify access seems unexpected.

### Project structure

**Objects:** `/S4PPM/PR1`, `C_PRPS_ART`, `C_PRPS_KST`, `C_PRPS_VNR`
**SoD relevance:** **No**
**Notes:** Rare in Treasury apps; appear via shared navigation catalogs. Do not flag.

### Generic / utility

**Objects:** `S_TABU_NAM`, `S_APPL_LOG`, `S_SCD0_OBJ`
**SoD relevance:** **No**
**Notes:** `S_TABU_NAM` controls table display (read-only configuration views); `S_APPL_LOG` controls application log read access; `S_SCD0_OBJ` controls schedule object display. All are structural authorizations unrelated to deal SoD. Their presence in `APS_IAM_W_APPAUI` is expected and harmless.

### Custom namespace

**Objects:** `/TMF/SHAEX`
**SoD relevance:** **No**
**Notes:** Customer-namespace object for Brazil-specific Treasury configuration (`TMF` namespace = Tax Management Framework Brazil). Appears in `_BR` apps. Not in scope for global SoD audit.

---

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

Note: Categories G (FX Hedge), O (Offsetting), S (FX Swap) are unrestricted — both roles may hold all activities for those.

---

## TRFCT Patterns in Existing Apps

| App suffix | TRFCT (active T_DEAL_PD) | Office |
|------------|--------------------------|--------|
| `_B_`      | D3 (Settlement)          | BOE    |
| `_F_`      | D1, D2 (Order, Contract) | FOE    |

---

## Business Role Templates

Core global Treasury BRTs (country variants follow the same catalog pattern):

| BRT ID | Display Name | Office |
|--------|-------------|--------|
| `SAP_BR_TREASURY_SPECIALIST_FOE` | Treasury Specialist - Front Office | FOE |
| `SAP_BR_TREASURY_SPECIALIST_BOE` | Treasury Specialist - Back Office | BOE |
| `SAP_BR_TREASURY_SPECIALIST_MOE` | Treasury Specialist - Middle Office | MOE |
| `SAP_BR_TREASURY_ACCOUNTANT` | Treasury Accountant | BOE |
| `SAP_BR_TREASURY_RISK_MANAGER` | Treasury Risk Manager | Mixed |

**Country variants (as of 2026-06-03):**

| BRT ID | Display Name |
|--------|-------------|
| `SAP_BR_TREASURY_SPEC_BOE_CN` | Treasury Specialist - Back Office for China |
| `SAP_BR_TREASURY_SPEC_BOE_SG` | Treasury Specialist - Back Office for Singapore |
| `SAP_BR_TREASURY_SPEC_BOE_TH` | Treasury Specialist - Back Office for Thailand |
| `SAP_BR_TREASURY_ACCOUNTANT_BR` | Treasury Accountant for Brazil |
| `SAP_BR_TREASURY_RISK_MGR_SG` | Treasury Risk Manager for Singapore |
| `SAP_BR_TREASURY_RISK_MGR_TH` | Treasury Risk Manager for Thailand |

**Key FOE catalogs** (→ `SAP_BR_TREASURY_SPECIALIST_FOE`):
`SAP_FIN_BC_TRM_FT_CCP_1_PC`, `SAP_FIN_BC_TRM_FT_DE_F_PC`, `SAP_FIN_BC_TRM_FT_FX_F_PC`, `SAP_FIN_BC_TRM_FT_MM_F_PC`, `SAP_FIN_BC_TRM_FTDECP_1_PC`, `SAP_FIN_BC_TRM_FTFXCP_1_PC`, `SAP_FIN_BC_TRM_FTMMCP_1_PC`, `SAP_FIN_BC_TRM_FT_CLA_PC`, `SAP_FIN_BC_TRM_PFT1_PC`, `SAP_FIN_BC_TRM_MFT1_PC`, `SAP_FIN_BC_TRM_CFT_PC`

**Key BOE catalogs** (→ `SAP_BR_TREASURY_SPECIALIST_BOE`):
`SAP_FIN_BC_TRM_POS_MGT_PC`, `SAP_FIN_BC_TRM_CTR_PC`, `SAP_FIN_BC_TRM_COR_PC`, `SAP_FIN_BC_TRM_FT_CCP_2_PC`, `SAP_FIN_BC_TRM_FTDECP_2_PC`, `SAP_FIN_BC_TRM_FTFXCP_2_PC`, `SAP_FIN_BC_TRM_FTMMCP_2_PC`, `SAP_FIN_BC_TRM_FT_B_PC`, `SAP_FIN_BC_TRM_PFT2_PC`, `SAP_FIN_BC_TRM_MFT2_PC`

**Key MOE catalogs** (→ `SAP_BR_TREASURY_SPECIALIST_MOE`):
`SAP_FIN_BC_TRM_EXP_POS_PC`, `SAP_FIN_BC_TRM_MR_ANLYS_PC`, `SAP_FIN_BC_TRM_RAW_EXP_PC`, `SAP_FIN_BC_TRM_VAL_PC`, `SAP_FIN_BC_TRM_AJ_TSMO_PC`, `SAP_FIN_BC_HEDGE_MGT_PC`, `SAP_FIN_BC_LIMIT_MGT_PC`, `SAP_FIN_BC_MKTD_CRCYCV_PC`

**Key Accountant catalogs** (→ `SAP_BR_TREASURY_ACCOUNTANT`):
`SAP_FIN_BC_TRM_ACCT_PC`, `SAP_FIN_BC_TRM_ACCT_PST_PC`, `SAP_FIN_BC_TRM_VAL_PC`, `SAP_FIN_BC_TRM_POS_MGT_PC`, `SAP_FIN_BC_TRM_POS_IND_PC`, `SAP_FIN_BC_HEDGE_ACCT_P_PC`, `SAP_FIN_BC_TRM_CLASSFCTN_PC`, `SAP_FIN_BC_TRM_IMP_PC`

Query to get full catalog list for a BRT:
```sql
SELECT BU_CATALOG_ID, BRT_ID FROM APS_IAM_W_BRTBUC WHERE BRT_ID = '<BRT_ID>'
```

---

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

---

### Catalog FOE/BOE split analysis

**Input:** Business Catalog ID (e.g. `SAP_TC_FIN_TRM_COMMON`)
**Output:** FOE-set, BOE-set, shared-set, split naming recommendation

1. List all apps in the catalog:
```sql
SELECT APP_ID, BU_CATALOG_ID FROM APS_IAM_W_BC_APP
WHERE BU_CATALOG_ID = '<CATALOG_ID>'
```

2. For each app, run Steps 3–4 (auth instances + values) and evaluate against both FOE and BOE forbidden matrices.

3. Classify each app:
   - **FOE only** — has FOE-forbidden values (D3+01/85, D2+AB); must go to FOE catalog
   - **BOE only** — has BOE-forbidden values (D2+01/02/16/85/KU/VF); must go to BOE catalog
   - **Shared** — no T_DEAL_* forbidden values in either direction (e.g., display-only apps, position indicators)
   - **Both-forbidden** — has both FOE and BOE forbidden combinations (configuration error; flag for remediation)

4. Propose split:
   - New FOE catalog: `<CATALOG_ID>_F_PC` — receives FOE-only + shared apps
   - New BOE catalog: `<CATALOG_ID>_B_PC` — receives BOE-only + shared apps
   - Shared apps appear in both catalogs

5. Report shape:
```
Catalog: SAP_TC_FIN_TRM_COMMON (53 apps)
FOE-only: 18 apps  → SAP_TC_FIN_TRM_COMMON_F_PC
BOE-only: 21 apps  → SAP_TC_FIN_TRM_COMMON_B_PC
Shared:   14 apps  → both catalogs
Both-forbidden: 0 apps
```

---

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

---

### Cross-company-code violation scan

**Input:** Two app IDs that together span FOE + BOE for the same company code
**Output:** Confirm or deny that a combined assignment creates SoD risk

This workflow addresses the case where split catalogs exist but a user is assigned to both — the per-catalog validation passes, but the combined view violates SoD.

1. For each app, collect active `T_DEAL_*` instances and their BUKRS values:
```sql
SELECT UUID, PARENT_ID, FIELD, LOW_VALUE FROM APS_IAM_W_APPAUV
WHERE APP_ID = '<APP_ID_1>'
```
Repeat for APP_ID_2.

2. Identify overlapping BUKRS values between the two apps.

3. For each overlapping BUKRS, check whether APP_ID_1 holds FOE-forbidden combinations AND APP_ID_2 holds BOE-forbidden combinations (or vice versa).

4. Report:
```
Combined SoD risk for BUKRS = 1000:
  App 1 (FTRCAI02_F_TRAN): T_DEAL_PD D2+01 → FOE create (allowed in FOE catalog)
  App 2 (FTRCAI02_B_TRAN): T_DEAL_PD D3+01 → BOE settle (allowed in BOE catalog)
  Combined: same BUKRS, both originate+settle → SoD VIOLATION
```

---

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

---

### Hedge request SoD

Governed by auth object **`T_TOE_HR`** — independent of `T_DEAL_*`.

**Scope:** T_TOE_HR SoD applies **only to MOE and Treasury Accountant** roles. Do **not** evaluate T_TOE_HR against FOE or BOE forbidden matrices.

**Fields:** `HREQ_CAT` (hedge request category), `ACTVT`

#### HREQ_CAT values

| HREQ_CAT | Meaning            |
|----------|--------------------|
| A        | Manual Designation |
| D        | Dedesignation      |
| G        | FX Hedge           |
| O        | Offsetting         |
| S        | FX Swap            |

#### Role split

| Role           | Catalogs |
|----------------|----------|
| **MOE**        | `SAP_FIN_BC_HEDGE_MGT_PC` → `SAP_BR_TREASURY_SPECIALIST_MOE` |
| **Accountant** | `SAP_FIN_BC_HEDGE_ACCT_P_PC` → `SAP_BR_TREASURY_ACCOUNTANT`, `SAP_BR_TREASURY_SPECIALIST_BOE` |

#### Workflow

Same as Steps 3–4, but:
- In Step 3: filter `AUTH_OBJECT = 'T_TOE_HR'`
- In Step 4: filter `FIELD IN ('HREQ_CAT', 'ACTVT')`

Form the Cartesian product HREQ_CAT × ACTVT per active instance. Check against the MOE/Accountant matrix. Report:

```
APP_ID | AUTH_OBJECT | UUID | HREQ_CAT | ACTVT | Rule violated (MOE/Accountant)
```

---

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

---

## Troubleshooting & Validation Tips

### INACTIVE / COPIED / STATUS field meanings

In `APS_IAM_W_APPAUI` and `APS_IAM_W_APPAUV`:

| Field    | Value | Meaning |
|----------|-------|---------|
| INACTIVE | blank | **Active** — include in SoD evaluation |
| INACTIVE | `X`   | Inactive — **exclude** from evaluation |
| COPIED   | `X`   | Instance was copied from another app; still subject to INACTIVE check |
| STATUS   | `M`   | Manual — set by IAM configuration team |
| STATUS   | `S`   | Supplied — SAP default; may be overridden by a manual instance on same UUID |
| STATUS   | `D`   | Deleted marker — treat as inactive |

**Common mistake:** Including all rows from `APPAUI` without filtering `INACTIVE = ''`. This produces false violations from inactive instances.

### Apps with no T_DEAL_* instances

Some Treasury apps (display-only, reporting, master data) have no `T_DEAL_*` instances at all. This is not a missing-data error — these apps delegate their auth to backend service objects or rely on org-level scoping only. They are neutral from a T_DEAL_* SoD perspective. Check `APS_IAM_W_APPAUO` to confirm any explicit auth-check exclusions.

### Cartesian product false positives

When an instance has multiple TRFCT values (e.g., D1 AND D2) and multiple ACTVT values (e.g., 01, 02, 03), the Cartesian product includes D2×01 — which is a BOE-forbidden combination. However, if the app's business purpose is purely Front-Office contract entry, the runtime never exercises D2+01 in a BOE context. **Resolution:** cross-reference the app's catalog assignment and name suffix. If the catalog is `*_F_PC` and the app name contains `_F_`, the D1/D2 presence is correct FOE behavior; D2+01 is not actually a BOE violation because the app is not in a BOE catalog. Document this in your audit finding as "context-correct; not a cross-office violation."

### T_DEAL_AG in cloud

`T_DEAL_AG` is not used in cloud Treasury IAM. If you find it in `APS_IAM_W_APPAUI` for an active instance, it was likely carried over from an on-premise migration. Apply the same forbidden matrix as `T_DEAL_PD`. Do not add `T_DEAL_AG` manually to new cloud apps.

### Performance pitfalls

- **Never** use `UP TO N ROWS` inline when a `WHERE` clause is present — the ER6 backend rejects this combination. Always pass `rows=N` as a separate parameter to `mcp__er6__query_sql`.
- `APS_IAM_W_APPAUV` can be large — always filter by `APP_ID` and use `rows=500` for safety.
- `APS_IAM_W_BC_APP` does **not** store Treasury apps by their technical Fiori catalog ID (`SAP_TC_FIN_TRM_*`). Treasury apps are looked up by business catalog ID (`SAP_FIN_BC_TRM_*`). The Fiori catalog `SUI_TM_MM_APP` stores app IDs as GUIDs — do not filter it by SIA6 app name.
- Do not use JOINs or subqueries — ABAP Open SQL forbids them in this dialect.

### When the matrix says "violation" but it isn't

1. **Display-only wildcard:** ACTVT = `03` (display) is never an SoD violation regardless of TRFCT. If you see D2+03, it is legitimate read access.
2. **High-value range:** `LOW_VALUE = 'D1'`, `HIGH_VALUE = 'D3'` in a single row means all TRFCT values are included. This will produce many Cartesian hits. Confirm the app is truly assigned to a mixed catalog before flagging.
3. **Catalog mismatch:** You are applying the FOE ruleset to an app in a BOE catalog, or vice versa. Always confirm catalog assignment (Step 2) before choosing which matrix to apply.
4. **Status = D:** A row with `STATUS = 'D'` in `APPAUV` is a soft-delete marker. Treat as inactive.

### Verifying your conclusion

After concluding "App X violates BOE SoD", confirm by reverse-querying:

```sql
SELECT FIELD, LOW_VALUE, HIGH_VALUE FROM APS_IAM_W_APPAUV
WHERE APP_ID = '<APP_ID>'
```

Filter manually for the UUID of the offending instance and show the auditor the exact row. This eliminates any doubt about derived Cartesian products and lets the finding stand on raw evidence.

---

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
