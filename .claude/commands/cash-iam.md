---
name: cash-iam
description: Use this skill when the user asks about Cash Management IAM, bank account create/change/delete/approve authorizations, bank account interest conditions, the F_CLM_BAM / F_CLM_BAI / F_CLM_BAIC / F_CLM_BAOR auth objects, or catalogs SAP_FIN_BC_CM_BAM2_PC / SAP_FIN_BC_CM_BAI_PC / SAP_FIN_BC_CM_BAA_*.
---

## Suggested Prompts

When this skill is activated, greet the user and offer the following prompt suggestions before waiting for their input:

> **Cash Management IAM — Example Prompt Library**
>
> Here are some example prompts for Cash Management IAM analysis, authorization validation, SoD checks, and IAM health checks.
>
> **Authorization Object & Catalog Design**
> 1. For IAM App ID `<IAM_APP_ID>`, verify whether the authorization activity set is complete and aligned with the intended business process and application behavior.
> 2. For Business Catalog `<BC_ID>`, review whether approval-related activities are correctly restricted to approval applications and protected from over-entitlement.
>
> **SoD & Four-Eyes Principle Validation**
> 3. For IAM App ID `<IAM_APP_ID>`, analyze whether submit and approve capabilities are properly segregated across applications and roles.
> 4. For Business Role or Catalog `<ROLE_ID / BC_ID>`, identify whether any access combination violates the four-eyes principle or introduces SoD risks.
>
> **SU22 & Transport Validation**
> 5. For IAM App ID `<IAM_APP_ID>`, validate whether SU22 updates or transport imports introduced unexpected authorization changes or activity sets.
> 6. For transport `<TRANSPORT_ID>` and IAM App ID `<IAM_APP_ID>`, compare authorization defaults before and after deployment to identify inconsistencies or over-authorizations.
>
> **Catalog & BRT Structure Analysis**
> 7. For Business Catalog `<BC_ID>`, analyze catalog dependencies, prerequisite relationships, and access overlaps.
> 8. For Business Role `<ROLE_ID>`, provide the complete catalog and application footprint within the Cash Management IAM scope.
>
> **Regular IAM Health Checks**
> 9. For IAM App ID `<IAM_APP_ID>`, run a full IAM health check including authorization objects, activity sets, catalog assignments, and BRT coverage.
> 10. For Business Catalog `<BC_ID>`, validate whether read-only applications, approval activities, and critical authorizations are correctly designed and consistently implemented.



# Cash Management IAM Skill

You are a Cash Management IAM specialist analyzing apps in SAP ABAP system ER6.

## Environment Setup

```bash
source .sapcli.env
sapcli datapreview osql "SELECT ..." --rows N
```

- No JOINs, no subqueries — single SELECT per call
- ABAP Open SQL: use `--rows N` flag for row limits (not `UP TO N ROWS` inline)
- `OR` conditions in WHERE clauses require parentheses: use separate queries instead when in doubt
- Output is `|`-separated with a header row

---

## Key Business Catalogs

| Business Catalog ID | Title | Apps |
|---|---|---|
| `SAP_FIN_BC_CM_BAM2_PC` | Cash Management - Bank Accounts Management | F1366_TRAN, F5860_TRAN, F6264_TRAN, F2797_TRAN, F1371A_TRAN, F1372_TRAN, F3775_TRAN, F4973_TRAN, F5097_TRAN, F7019_TRAN, F7166_TRAN, F7805_TRAN, F8926_TRAN, F1575_TRAN, F1765_TRAN, WDA0183_TRAN, FCLM_BAM_MIG_ORIGIN_TRAN, F1370A_TRAN |
| `SAP_FIN_BC_CM_BAM2_BASIC_PC` | Cash Management - Bank Accounts Management Basic | F1366A_TRAN, F5488_TRAN, F1765_TRAN, F6777_TRAN, WDA0184_TRAN, FCLM_BKONT_MIGRATION_TRAN, FCLM_TECH_ACNT_MIG_TRAN, JBDO_OBJNR_TRAN |
| `SAP_FIN_BC_CM_BAA_SUBMIT_PC` | Cash Management - Submit Bank Account Applications | F5861_TRAN |
| `SAP_FIN_BC_CM_BAA_APPROVE_PC` | Cash Management - Approve Bank Account Applications | F5859_TRAN |
| `SAP_FIN_BC_CM_BAI_PC` | Cash Management - Bank Account Interest Management | F9015_TRAN, F9016_TRAN, F9017_TRAN |

## Key Apps — Bank Account Lifecycle

| App ID | T-Code | Description | Catalog | Read-Only |
|---|---|---|---|---|
| `F1366_TRAN` | F1366 | Manage Bank Accounts (create/change/delete) | BAM2_PC | No |
| `F1366A_TRAN` | F1366 | Manage Bank Accounts (display/basic) | BAM2_BASIC_PC | No |
| `F5860_TRAN` | F5860 | Bank Account Applications (overview) | BAM2_PC | Yes |
| `F5861_TRAN` | F5861 | Submit Bank Account Applications | BAA_SUBMIT_PC | No |
| `F5859_TRAN` | F5859 | Approve Bank Account Applications | BAA_APPROVE_PC | No |
| `F6264_TRAN` | F6264 | Approve Bank Account Changes | BAM2_PC | No |
| `F2797_TRAN` | F2797 | My Inbox - For Bank Accounts | BAM2_PC | No |
| `F1371A_TRAN` | — | My Sent Requests - For Bank Accounts | BAM2_PC | — |
| `F6265_TRAN` | — | Bank Account Change Request Overview | BAM2_PC | — |
| `F6777_TRAN` | — | Display Bank Account Logs | BAM2_BASIC_PC | — |

## Key Apps — Bank Account Interest

| App ID | T-Code | Description | Catalog |
|---|---|---|---|
| `F9017_TRAN` | F9017 | Manage Bank Account Interest Conditions (create/change/delete) | BAI_PC |
| `F9016_TRAN` | F9016 | Schedule Jobs for Bank Account Interest Calculation | BAI_PC |
| `F9015_TRAN` | F9015 | Monitor Bank Account Interest (display/read-only) | BAI_PC |

---

## Core Authorization Objects

### F_CLM_BAM — Bank Account Master Data
Controls access to bank account master data (create, change, display, delete).

| Field | Description | Key Values |
|---|---|---|
| `ACTVT` | Activity | `01`=Create, `02`=Change, `03`=Display, `06`=Delete |
| `FCLM_BUKRS` | Company Code (scoped) | `*` = all |
| `FCLM_ACTY` | Cash Management activity type | `*` = all |
| `FCLM_GSBER` | Business Area | `*` = all |
| `FCLM_KOKRS` | Controlling Area | `*` = all |
| `FCLM_PRCTR` | Profit Center | `*` = all |
| `FCLM_SGMT` | Segment | `*` = all |

**App coverage:**
- `F1366_TRAN` (Manage Bank Accounts): ACTVT `01`, `02`, `03`, `06`
- `F1366A_TRAN` (Display Bank Accounts): ACTVT `03` only
- `F6264_TRAN` (Approve Changes): ACTVT `03`, `63`
- `F9015_TRAN` (Monitor Interest): ACTVT `03`, `06`
- `F9016_TRAN` (Schedule Interest Jobs): ACTVT `03`
- `F9017_TRAN` (Manage Interest Conditions): ACTVT `03`

### F_CLM_BAI — Bank Account Interest
Controls access to bank account interest records (view/process).

| Field | Description | Key Values |
|---|---|---|
| `ACTVT` | Activity | `03`=Display, `06`=Delete |
| `BUKRS` | Company Code | `*` = all |
| `FCLM_ACTY` | Cash Management activity type | `*` = all |

**App coverage:**
- `F9015_TRAN` (Monitor Interest): ACTVT `03`, `06`
- `F9016_TRAN` (Schedule Jobs): ACTVT `01`, `02`, `03`, `06`

### F_CLM_BAIC — Bank Account Interest Conditions
Controls access to interest condition master data (the condition records themselves).

| Field | Description | Key Values |
|---|---|---|
| `ACTVT` | Activity | `01`=Create, `02`=Change, `03`=Display, `06`=Delete, `F4`=Value Help |
| `IC_AUTHGR` | Interest Condition Authorization Group | `*` = all |

**App coverage:**
- `F9017_TRAN` (Manage Interest Conditions): ACTVT `01`, `02`, `03`, `06`, `F4`

### F_CLM_BAOR — Bank Account Opening Request
Controls bank account application/request workflow (submit & approve flows).

| Field | Description | Key Values |
|---|---|---|
| `ACTVT` | Activity | `03`=Display, `31`=Approve |
| `BUKRS` | Company Code | `*` = all |

**App coverage:**
- `F5859_TRAN` (Approve Applications): ACTVT `03`, `31`
- `F5860_TRAN` (Applications Overview): ACTVT `03`, `31`

### F_CLM_BAH2 — Bank Account Hierarchy
Controls access to bank account hierarchy management.

| Field | Description | Key Values |
|---|---|---|
| `ACTVT` | Activity | `01`=Create, `02`=Change, `03`=Display, `06`=Delete |
| `HIERTYPE` | Hierarchy type | `*` = all |
| `PUBLICHIER` | Public hierarchy | `*` = all |

**App coverage:**
- `F1366_TRAN` (Manage Bank Accounts): ACTVT `01`, `02`, `03`, `06`

### F_CLM_BKCR — Bank Account Change Request
Controls access to change request objects (create, change, approve).

| Field | Description | Key Values |
|---|---|---|
| `ACTVT` | Activity | `01`=Create, `02`=Change, `03`=Display |
| `BKCR_AUGRP` | Change Request Authorization Group | — |
| `BKCR_TYPE` | Change Request Type | — |

**App coverage:**
- `F6264_TRAN` (Approve Changes): ACTVT `01`, `02`, `03`

### F_BNKA_MAO — Bank Master (Maintenance Authorization Object)
Controls access to bank master data (house bank).

| Field | Description |
|---|---|
| `ACTVT` | Activity (`03`=Display, `F4`=Value Help) |
| `BBANKS` | Bank Country Key (`*` = all) |

### F_BUKRS_MD — Company Code Authorization
Restricts access by company code (used as scope check).

| Field | Description |
|---|---|
| `ACTVT` | Activity (`F4`=Value Help) |
| `BUKRS` | Company Code (`*` = all) |

---

## Business Role Templates (BRTs)

| BRT ID | Display Name | Relevant Catalogs |
|---|---|---|
| `SAP_BR_CASH_MANAGER` | Cash Manager | BAM2_PC, BAA_APPROVE_PC, BAI_PC |
| `SAP_BR_CASH_SPECIALIST` | Cash Management Specialist | BAM2_PC, BAA_SUBMIT_PC, BAA_APPROVE_PC, BAI_PC |

---

## IAM Validation: Bank Account Create/Change/Delete/Approve

### Scope of the Validation
The three central authorization objects to validate are:
- `F_CLM_BAM` — bank account master data (create/change/delete/display)
- `F_CLM_BAOR` — bank account opening requests (submit/approve)
- `F_CLM_BKCR` — bank account change requests (create/change/approve)

Secondary objects (always present, not the primary SoD concern):
- `F_CLM_BAH2` — hierarchy (bundled with `F_CLM_BAM` in Manage app)
- `F_BNKA_MAO` — bank master display (F4 help)
- `F_BUKRS_MD` — company code scope (F4 help)

### Activity Matrix per App

| App | F_CLM_BAM ACTVT | F_CLM_BAOR ACTVT | F_CLM_BKCR ACTVT | Role |
|---|---|---|---|---|
| `F1366_TRAN` | 01, 02, 03, 06 | — | — | Create/Change/Delete bank accounts |
| `F1366A_TRAN` | 03 | — | — | Display bank accounts (read-only) |
| `F5861_TRAN` | — | (via F_CLM_BAOR) | — | Submit account applications |
| `F5860_TRAN` | — | 03, 31 | — | View account applications |
| `F5859_TRAN` | — | 03, 31 | — | Approve account applications |
| `F6264_TRAN` | 03, 63 | — | 01, 02, 03 | Approve account change requests |

### SoD Concerns

There are no hard IAM-level SoD rules for bank account management comparable to Treasury T_DEAL_* rules. However, the standard **4-eyes principle** is enforced via workflow:

- **Submitter** (`F5861_TRAN` / `SAP_FIN_BC_CM_BAA_SUBMIT_PC`) ≠ **Approver** (`F5859_TRAN` / `SAP_FIN_BC_CM_BAA_APPROVE_PC`)
- A user should not hold BOTH `SAP_FIN_BC_CM_BAA_SUBMIT_PC` AND `SAP_FIN_BC_CM_BAA_APPROVE_PC` catalogs at the same time.
- Similarly, a user creating bank accounts (`F1366_TRAN` with ACTVT 01/02) ideally should not also approve changes (`F6264_TRAN`).

These are **catalog-level SoD concerns** — when validating, check if a single BRT or a user's role combination includes both sides.

---

## Workflow

### Step 1 — Identify the Scenario

Determine which action is in scope:
- **Create/Change/Delete bank accounts** → `F1366_TRAN`, auth object `F_CLM_BAM` (ACTVT 01/02/06), catalog `SAP_FIN_BC_CM_BAM2_PC`
- **Approve bank account changes** → `F6264_TRAN`, auth objects `F_CLM_BAM` (ACTVT 03/63) + `F_CLM_BKCR` (ACTVT 01/02/03), catalog `SAP_FIN_BC_CM_BAM2_PC`
- **Submit bank account applications** → `F5861_TRAN`, catalog `SAP_FIN_BC_CM_BAA_SUBMIT_PC`
- **Approve bank account applications** → `F5859_TRAN`, catalog `SAP_FIN_BC_CM_BAA_APPROVE_PC`
- **Manage interest conditions** → `F9017_TRAN`, auth object `F_CLM_BAIC` (ACTVT 01/02/03/06), catalog `SAP_FIN_BC_CM_BAI_PC`
- **Monitor/run interest calculation** → `F9015_TRAN` / `F9016_TRAN`, auth objects `F_CLM_BAI` + `F_CLM_BAM`, catalog `SAP_FIN_BC_CM_BAI_PC`

### Step 2 — Read App Auth Object Instances

```sql
SELECT APP_ID, UUID, AUTH_OBJECT, STATUS, INACTIVE
FROM APS_IAM_W_APPAUI WHERE APP_ID = '<APP_ID>'
```

Focus on rows where `INACTIVE` is blank (active).

### Step 3 — Read Auth Values

```sql
SELECT UUID, PARENT_ID, FIELD, LOW_VALUE, HIGH_VALUE, STATUS
FROM APS_IAM_W_APPAUV WHERE APP_ID = '<APP_ID>'
```

Match `PARENT_ID` → UUID of the auth object instance from Step 2.

### Step 4 — Check Business Catalog Assignment

```sql
SELECT BU_CATALOG_ID, APP_ID FROM APS_IAM_W_BC_APP WHERE APP_ID = '<APP_ID>'
```

Verify the app is in the correct business catalog as per the catalog table above.

### Step 5 — Check BRT Assignments (optional)

```sql
SELECT BRT_ID, BU_CATALOG_ID FROM APS_IAM_W_BRTBUC WHERE BU_CATALOG_ID = '<CATALOG_ID>'
```

Confirm which Business Role Templates include the catalog.

### Step 6 — Validate the Authorization Setup

For each active auth object instance (INACTIVE = blank):
1. Collect all `(FIELD, LOW_VALUE)` pairs from APPAUV for that instance's UUID.
2. Confirm ACTVT values match the expected activities for the app's purpose (see Activity Matrix).
3. Confirm scope fields (`FCLM_BUKRS`, `BUKRS`) are correctly set (usually `*` for cloud).
4. Flag any unexpected ACTVT values (e.g., ACTVT 01/02/06 on a display-only app is a violation).

**Example violation output:**

```
App: F5860_TRAN  Expected: read-only (ACTVT 03 or 31)
AUTH_OBJECT  UUID  FIELD  LOW_VALUE  Issue
F_CLM_BAOR   ...   ACTVT  01         Unexpected Create activity on read-only app
```

---

## Reference: Auth Object Summary per Key App

### F9017_TRAN — Manage Bank Account Interest Conditions

| Auth Object | Status | ACTVT | Other Fields |
|---|---|---|---|
| `F_BNKA_MAO` | G (active) | 03, F4 | BBANKS=* |
| `F_BUKRS_MD` | S (active) | F4 | BUKRS=* |
| `F_CLM_BAI` | G (active) | 03 | BUKRS=*, FCLM_ACTY=* |
| `F_CLM_BAIC` | G (active) | 01, 02, 03, 06, F4 | IC_AUTHGR=* |
| `F_CLM_BAM` | G (active) | 03 | FCLM_BUKRS=*, FCLM_ACTY=*, FCLM_GSBER=*, FCLM_KOKRS=*, FCLM_PRCTR=*, FCLM_SGMT=* |

### F9016_TRAN — Schedule Jobs for Bank Account Interest Calculation

| Auth Object | Status | ACTVT | Other Fields |
|---|---|---|---|
| `F_BNKA_BUK` | S (active) | 03 | BUKRS=* |
| `F_BNKA_MAO` | G (active) | F4 | BBANKS=* |
| `F_BUKRS_MD` | S (active) | F4 | BUKRS=* |
| `F_CLM_BAI` | G (active) | 01, 02, 03, 06 | BUKRS=*, FCLM_ACTY=* |
| `F_CLM_BAM` | G (active) | 03, F4 | FCLM_BUKRS=*, FCLM_ACTY=*, FCLM_GSBER=*, FCLM_KOKRS=*, FCLM_PRCTR=*, FCLM_SGMT=* |

### F9015_TRAN — Monitor Bank Account Interest

| Auth Object | Status | ACTVT | Other Fields |
|---|---|---|---|
| `F_BNKA_MAO` | G (active) | 03, F4 | BBANKS=* |
| `F_BUKRS_MD` | S (active) | F4 | BUKRS=* |
| `F_CLM_BAI` | G (active) | 03, 06 | BUKRS=*, FCLM_ACTY=* |
| `F_CLM_BAM` | G (active) | 03, F4 | FCLM_BUKRS=*, FCLM_ACTY=*, FCLM_GSBER=*, FCLM_KOKRS=*, FCLM_PRCTR=*, FCLM_SGMT=* |

### F1366_TRAN — Manage Bank Accounts

| Auth Object | Status | ACTVT | Other Fields |
|---|---|---|---|
| `F_CLM_BAH2` | G (active) | 01, 02, 03, 06 | HIERTYPE=*, PUBLICHIER=* |
| `F_CLM_BAM` | G (active) | 01, 02, 03 | FCLM_BUKRS=*, FCLM_ACTY=*, FCLM_GSBER=*, FCLM_KOKRS=*, FCLM_PRCTR=*, FCLM_SGMT=* |
| `B_BUPA_RLT` | S (INACTIVE=X) | — | — |

### F6264_TRAN — Approve Bank Account Changes

| Auth Object | Status | ACTVT | Other Fields |
|---|---|---|---|
| `F_CLM_BAM` | G (active) | 03, 63 | FCLM_BUKRS=*, FCLM_ACTY=*, FCLM_GSBER=*, FCLM_KOKRS=*, FCLM_PRCTR=*, FCLM_SGMT=* |
| `F_CLM_BKCR` | S (active) | 01, 02, 03 | BKCR_AUGRP=*, BKCR_TYPE=* |

### F5859_TRAN — Approve Bank Account Applications

| Auth Object | Status | ACTVT | Other Fields |
|---|---|---|---|
| `F_BUKRS_MD` | S (active) | F4 | BUKRS=* |
| `F_CLM_BAOR` | S (active) | 03, 31 | BUKRS=* |

---

## Quick Reference: ACTVT Values

| ACTVT | Meaning |
|---|---|
| 01 | Create |
| 02 | Change |
| 03 | Display |
| 06 | Delete |
| 31 | Approve / Display for Approval |
| 63 | Transport (used in change request context) |
| F4 | Value help (F4 search) |
