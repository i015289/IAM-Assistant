---
name: cash-iam
description: Use this skill when the user asks about Cash Management IAM, bank account create/change/delete/approve authorizations, bank account interest conditions, the F_CLM_BAM / F_CLM_BAI / F_CLM_BAIC / F_CLM_BAOR auth objects, or catalogs SAP_FIN_BC_CM_BAM2_PC / SAP_FIN_BC_CM_BAI_PC / SAP_FIN_BC_CM_BAA_*.
---

## Suggested Prompts

When this skill is activated, greet the user and offer the following prompt suggestions before waiting for their input:

> **Cash Management IAM — ready. Here are some things you can ask:**
>
> **General Troubleshooting — app not found or not accessible**
> - "App `F5859_TRAN` is not showing in the launchpad"
> - "User cannot find Approve Bank Account Applications"
> - "T-Code F9017 is missing for a user"
>
> **Missing Authorization Translation — trace an error to the right BRT**
> - "User is missing `F_CLM_BAOR` ACTVT 31"
> - "User cannot approve bank account applications — what authorization is needed?"
> - "Authorization error for `F_CLM_BAIC` ACTVT 06"
>
> **SU22 Review — validate an app's authorization setup**
> - "Review F1366A_TRAN" *(Manage Bank Accounts — central app)*
> - "Check SU22 for F9017_TRAN" *(Manage Interest Conditions)*
> - "Validate authorization setup for F5861_TRAN" *(Submit Bank Account Applications)*
>
> **SoD & 4-eyes validation**
> 1. Does any single BRT combine both Submit and Approve on bank account applications? *(self-approval risk)*
> 2. Can a user who creates bank accounts (`F1366_TRAN`) also approve change requests (`F6264_TRAN`)? *(creator = approver risk)*
> 3. Which catalogs grant write access to `F_CLM_BAOR` — and do any of them also grant `ACTVT 31` (Approve)?
>
> **Auth object & activity completeness**
> 4. Verify `F9017_TRAN` (Manage Interest Conditions) has the correct activities on `F_CLM_BAIC` — should Delete (06) be present?
> 5. Why does `F9016_TRAN` (Schedule Interest Jobs) have `F_CLM_BAI` with write activities (01/02) — is that expected for a scheduling app?
> 6. What is ACTVT `69` on `F_CLM_BAOR`, and which apps use it?
>
> **Catalog assignment checks**
> 7. Are all apps in `SAP_FIN_BC_CM_BAM2_PC` correctly classified — are any display-only apps in the wrong (write) catalog?
> 8. What catalog dependencies exist between the BAM2 and BAA catalogs — is there a required prerequisite chain for the bank account workflow?
> 9. Which BRTs include `SAP_FIN_BC_CM_BAI_PC`, and is the interest management catalog correctly restricted to Cash Manager / Cash Specialist only?
>
> **Cross-catalog / BRT analysis**
> 10. Show the full catalog footprint of `SAP_BR_CASH_SPECIALIST` — all catalogs and their apps.




# Cash Management IAM Skill

You are a Cash Management IAM specialist analyzing apps in SAP ABAP system ER6.

---

## Overview: Cash Management IAM

### What is Cash Management IAM?

Cash Management IAM governs who can access and operate on bank accounts, bank account applications, bank account interest conditions, and related cash operations in SAP S/4HANA Cloud. It is built on the SAP IAM framework using **Business Catalogs**, **Business Role Templates (BRTs)**, and **Authorization Objects** — the three layers that together define what a user can do.

### The Three Layers

**1. Authorization Objects (the lowest level)**
Authorization objects are the actual security checks performed by ABAP code at runtime. For Cash Management, the core objects are:
- `F_CLM_BAM` — controls create/change/delete/display of bank account master data
- `F_CLM_BAOR` — controls submit/approve/cancel of bank account opening requests
- `F_CLM_BKCR` — controls bank account change requests
- `F_CLM_BAIC` — controls bank account interest conditions
- `F_CLM_BAI` — controls bank account interest records
- `F_CLM_BAH2` — controls bank account hierarchy management

Each auth object has **fields** (e.g., `ACTVT` for activity, `BUKRS` for company code) and **values** (e.g., `01`=Create, `03`=Display). An app is authorized for an action only if the user's role contains a matching auth object with the correct field values.

**2. Business Catalogs (the middle level)**
A Business Catalog is a named collection of Fiori apps grouped by business function. Each catalog defines the apps a user can see and use, and maps those apps to the required authorization objects. Cash Management has five main catalogs:
- `SAP_FIN_BC_CM_BAM2_PC` — full bank accounts management (19 apps, write-capable)
- `SAP_FIN_BC_CM_BAM2_BASIC_PC` — basic/display bank accounts management (8 apps)
- `SAP_FIN_BC_CM_BAA_SUBMIT_PC` — submit bank account applications (1 app)
- `SAP_FIN_BC_CM_BAA_APPROVE_PC` — approve bank account applications (1 app)
- `SAP_FIN_BC_CM_BAI_PC` — bank account interest management (3 apps)

**3. Business Role Templates (the highest level)**
A BRT is a pre-defined bundle of Business Catalogs assigned to a job role. Administrators assign BRTs to users. The two Cash Management BRTs are:
- `SAP_BR_CASH_MANAGER` — Cash Manager
- `SAP_BR_CASH_SPECIALIST` — Cash Management Specialist (37 catalogs, broadest access)

### The Bank Account Lifecycle & Authorization Flow

```
New Account Request
  └─ F5861_TRAN (Submit)       → F_CLM_BAOR: 01/02/03/06/69  [BAA_SUBMIT_PC]
       └─ F5859_TRAN (Approve) → F_CLM_BAOR: 03/31           [BAA_APPROVE_PC]

Existing Account Management
  └─ F1366A_TRAN (Manage Bank Accounts — central app)
                               → F_CLM_BAM: 01/02/03/06      [BAM2_BASIC_PC]
       └─ F6264_TRAN (Approve Changes)
                               → F_CLM_BAM: 03/63            [BAM2_PC]
                                 F_CLM_BKCR: 01/02/03

Bank Group Hierarchy
  └─ F1366_TRAN (Manage Bank Group Hierarchies)
                               → F_CLM_BAM: 01/02/03         [BAM2_PC]
                                 F_CLM_BAH2: 01/02/03/06

Interest Management
  └─ F9017_TRAN (Manage)       → F_CLM_BAIC: 01/02/03/06/F4  [BAI_PC]
  └─ F9016_TRAN (Schedule)     → F_CLM_BAI:  01/02/03/06     [BAI_PC]
  └─ F9015_TRAN (Monitor)      → F_CLM_BAI:  03/06           [BAI_PC]
```

### 2-Person Verification (4-Eyes Principle)

All submit/approve and create/approve separations in Cash Management are **enforced at the application/workflow code level**, not at the IAM authorization level. The system requires a different user ID at the approval step — holding both catalogs in the same BRT is therefore not an IAM violation. There are no catalog-level SoD rules to configure or enforce for these workflows.

---

## AI Tool Strategy for Cash Management IAM

### What This Tool Can Do Today

This AI assistant has live read access to the ER6 system and full knowledge of the Cash Management IAM structure. It can:

1. **Validate authorization completeness** — for any app, verify that the correct auth objects and ACTVT values are present and no unexpected activities are granted
2. **Investigate unknown activity codes** — look up what an undocumented ACTVT means by tracing it back to RAP behavior code and business context
3. **Audit catalog app classification** — confirm whether apps in a catalog are correctly flagged as read-only or write, and identify misclassifications
4. **Map catalog dependencies** — show what prerequisite catalogs a given catalog requires and what downstream catalogs depend on it
5. **Produce BRT footprint reports** — list every catalog assigned to a BRT, grouped by functional area
6. **Answer "who can do what" questions** — trace from a business action (e.g., "approve bank account changes") back to the exact app, catalog, auth object, and activity required

### Proposed Future Use Cases

**Regression validation after IAM changes**
When a new app version or auth object change is delivered, run a structured check: pull the new auth values from the system and compare against the documented baseline in this skill. Flag any delta for review before transport to production.

**Onboarding new Cash Management apps**
When a new app is added to a catalog, use the tool to: (1) confirm its catalog assignment, (2) verify its auth object instances match its intended access level (read vs. write), (3) check it does not introduce unintended ACTVT values on sensitive objects like `F_CLM_BAOR`.

**Audit support**
For internal or external audits requiring evidence of authorization design, generate structured reports directly from the live system — catalog contents, BRT assignments, auth object activity matrices — without manual extraction.

**Expanding to other Cash Management catalogs**
The current skill covers bank account and interest management. The same query patterns can be applied to other catalogs in `SAP_BR_CASH_SPECIALIST` (e.g., POA, Bank Fee Management, Liquidity Planning) to build out equivalent documented baselines.

**Cross-BRT comparison**
Compare `SAP_BR_CASH_MANAGER` vs. `SAP_BR_CASH_SPECIALIST` catalog-by-catalog to document the exact privilege delta between the two roles — useful for role design reviews and least-privilege analysis.

---

## Environment Setup

```bash
source .sapcli.env
sapcli datapreview osql "SELECT ..." --rows N
```

- No JOINs, no subqueries — single SELECT per call
- ABAP Open SQL: use `--rows N` flag for row limits (not `UP TO N ROWS` inline)
- `OR` conditions in WHERE clauses hit length limits — query per value instead
- Output is `|`-separated with a header row

---

## Key Business Catalogs

| Business Catalog ID | Title | App Count |
|---|---|---|
| `SAP_FIN_BC_CM_BAM2_PC` | Cash Management - Bank Accounts Management | 19 |
| `SAP_FIN_BC_CM_BAM2_BASIC_PC` | Cash Management - Bank Accounts Management Basic | 8 |
| `SAP_FIN_BC_CM_BAA_SUBMIT_PC` | Cash Management - Submit Bank Account Applications | 1 |
| `SAP_FIN_BC_CM_BAA_APPROVE_PC` | Cash Management - Approve Bank Account Applications | 1 |
| `SAP_FIN_BC_CM_BAI_PC` | Cash Management - Bank Account Interest Management | 3 |
| `SAP_FIN_BC_CM_CASH_OPS_PC` | Cash Management - Cash Operations | 46 |
| `SAP_FIN_BC_CM_OPS_BASIC_PC` | Cash Management - Cash Operations Basic | 38 |
| `SAP_FIN_BC_CM_CASH_SAC_OPS_PC` | Cash Management - Liquidity Planning | 2 |
| `SAP_FIN_BC_CM_SNAPSHOT_PC` | Cash Management - Cash Snapshots | 2 |
| `SAP_FIN_BC_CM_POA_PC` | Cash Management - Power of Attorney for Banking Transactions | 3 |
| `SAP_FIN_BC_CM_POA_APPROVE_PC` | Cash Management - Approve Powers of Attorney for Banking Transactions | 1 |

## Key Apps — Bank Accounts Management (SAP_FIN_BC_CM_BAM2_PC)

All apps below are correctly classified. READ_ONLY flag and catalog placement are intentional.

| App ID | T-Code | Description | Read-Only |
|---|---|---|---|
| `F1366_TRAN` | F1366 | Manage Bank Group Hierarchies | No |
| `F1370A_TRAN` | F1370A | Review Bank Accounts (Deprecated) | No |
| `F1371A_TRAN` | F1371A | My Sent Requests - For Bank Accounts | Yes |
| `F1372_TRAN` | F1372 | Maintain Payment Approver | No |
| `F1575_TRAN` | F1575 | Foreign Bank Account Report | Yes |
| `F1765_TRAN` | F1765 | User Default Parameters | No |
| `F2797_TRAN` | F2797 | My Inbox - For Bank Accounts | No |
| `F3775_TRAN` | F3775 | Bank Relationship Overview | Yes |
| `F4973_TRAN` | F4973 | Manage Bank Account Hierarchies | No |
| `F5097_TRAN` | F5097 | Application Jobs - Import/Export Global Hierarchies | Yes |
| `F5860_TRAN` | F5860 | Bank Account Applications | Yes |
| `F6264_TRAN` | F6264 | Approve Bank Account Changes | No |
| `F6265_TRAN` | F6265 | Bank Account Change Request Overview | Yes |
| `F7019_TRAN` | F7019 | Application Jobs - Activate Global Hierarchies | Yes |
| `F7166_TRAN` | F7166 | Workflow Change Requests In Approval | Yes |
| `F7805_TRAN` | F7805 | Define Bank Accounts for Instant Balances | No |
| `F8926_TRAN` | F8926 | Bank Relationship Management via API | Yes |
| `FCLM_BAM_MIG_ORIGIN_TRAN` | FCLM_BAM_MIG_ORIGIN | Adapt Inactive Bank Accounts - Origination Process | No |
| `WDA0183_TRAN` | WDA0183 | Maintain Bank Hierarchy | No |

## Key Apps — Bank Accounts Management Basic (SAP_FIN_BC_CM_BAM2_BASIC_PC)

| App ID | T-Code | Description |
|---|---|---|
| `F1366A_TRAN` | F1366A | Manage Bank Accounts (central app — create/change/delete/display) | No |
| `F5488_TRAN` | F5488 | — |
| `F1765_TRAN` | F1765 | User Default Parameters |
| `F6777_TRAN` | F6777 | Display Bank Account Logs |
| `WDA0184_TRAN` | WDA0184 | — |
| `FCLM_BKONT_MIGRATION_TRAN` | FCLM_BKONT_MIGRATION | — |
| `FCLM_TECH_ACNT_MIG_TRAN` | FCLM_TECH_ACNT_MIG | — |
| `JBDO_OBJNR_TRAN` | JBDO_OBJNR | — |

## Key Apps — Bank Account Applications (Submit/Approve)

| App ID | T-Code | Description | Catalog |
|---|---|---|---|
| `F5861_TRAN` | F5861 | Submit Bank Account Applications | `SAP_FIN_BC_CM_BAA_SUBMIT_PC` |
| `F5859_TRAN` | F5859 | Approve Bank Account Applications | `SAP_FIN_BC_CM_BAA_APPROVE_PC` |

## Key Apps — Bank Account Interest (SAP_FIN_BC_CM_BAI_PC)

| App ID | T-Code | Description | Read-Only |
|---|---|---|---|
| `F9017_TRAN` | F9017 | Manage Bank Account Interest Conditions | No |
| `F9016_TRAN` | F9016 | Schedule Jobs for Bank Account Interest Calculation | No |
| `F9015_TRAN` | F9015 | Monitor Bank Account Interest | No |

## Key Apps — Cash Operations (SAP_FIN_BC_CM_CASH_OPS_PC)

All apps correctly classified. BRTs: `SAP_BR_CASH_MANAGER`, `SAP_BR_CASH_SPECIALIST`.
Dependencies: `SAP_CMD_BC_BP_DISP_PC` (nav), `SAP_CMD_BC_CUSTOMER_DSP_PC` (nav), `SAP_CMD_BC_SUPPLIER_DSP_PC` (nav), `SAP_CORE_BC_UI_SHARE_PC` (technical).

| App ID | Description | Read-Only |
|---|---|---|
| `F2332_TRAN` | Cash Flow Analyzer | Yes |
| `F3266_TRAN` | Manage Cash Pools (Deprecated) | No |
| `F0691_TRAN` | Make Bank Transfers | No |
| `F0735_TRAN` | Check Cash Flow Items | No |
| `F5380_TRAN` | Short-Term Cash Positioning | No |
| `F6123_TRAN` | Display Cash Pool Hierarchies | Yes |
| `F7146_TRAN` | Schedule Jobs for Bank Account Balance Initialization | No |
| `F3418_TRAN` | Reconcile Cash Flows - Intraday Memo Records (Deprecated) | No |
| `F3418A_TRAN` | Reconcile Cash Flows - Intraday | No |
| `F3265_TRAN` | Manage Cash Concentration | No |
| `F3760_TRAN` | Make Bank Transfers - Create with Templates | No |
| `F3759_TRAN` | Define Bank Transfer Templates | No |
| `F3446_TRAN` | Release Cash Flows | No |
| `F4966_TRAN` | Manage Liquidity Item Hierarchies | No |
| `FCLM_CP_PROFILE_TRAN` | Define Cash Position Profiles | No |
| `F1737_TRAN` | Cash Position | Yes |
| `F6385_TRAN` | Manage Liquidity Item Transfer | No |
| `F6459_TRAN` | Check Liquidity Items on G/L Account | Yes |
| `S_ER9_11002196_TRAN` | Set Block Date for Actual Cash Flows | No |
| `S_ER9_11002333_TRAN` | Flow Builder: Stop Condition | No |
| `F6388_TRAN` | Bank Statement Monitor | Yes |
| `F3266A_TRAN` | Manage Cash Pools (Version 2) | No |
| `F7690_TRAN` | Document Chain Trace | Yes |
| `F7725_TRAN` | Reconcile Distributed Cash Flow Data | Yes |
| `F7804_TRAN` | Monitor Instant Balances | No |
| `W0137_TRAN` | Cash Flow Comparison - By Timestamp | Yes |
| `W0128_TRAN` | Cash Flow Comparison - By Date Range | Yes |
| `F7994_TRAN` | Display Bank Account Balance | Yes |
| `F3671_TRAN` | Bank Statement Monitor - Intraday | Yes |
| `F0673A_TRAN` | Approve Bank Payments | No |
| `F6617_TRAN` | Display Bank Payment Approval Jobs | No |
| `F2986_TRAN` | Manage Memo Records | No |
| `W0129_TRAN` | Cash Pool Transfer Report | Yes |
| `F1765_TRAN` | User Default Parameters | No |
| `SP01_SIMPLE_TRAN` | Display Spoolrequests | No |
| `F1760_TRAN` | Factsheet Bank | Yes |
| `F4991_TRAN` | Display Cash Management Logs | Yes |
| `F5284_TRAN` | Schedule Intraday Memo Records Reconciliation (Deprecated) | Yes |
| `F6770_TRAN` | Schedule Job for Rebuild Liq Item | No |
| `F7281_TRAN` | Schedule Job for Replication Cash Flow Item | No |
| `F8307_TRAN` | Schedule Job for Document Chain Traceability | Yes |
| `F7751_TRAN` | Schedule Job for Retrieving Remote Cash Flow Data | No |
| `F5283_TRAN` | Schedule Jobs for Cash Flow Reconciliation | No |
| `F8829_TRAN` | Short-Term Cash Positioning via API | No |
| `F5240_TRAN` | Smart Business - Preview | Yes |
| `F7923_TRAN` | Actual Liquidity Analysis | Yes |

## Key Apps — Cash Operations Basic (SAP_FIN_BC_CM_OPS_BASIC_PC)

All apps correctly classified. BRTs: `SAP_BR_CASH_MANAGER`, `SAP_BR_CASH_SPECIALIST`.
Dependencies: `SAP_CMD_BC_BP_DISP_PC` (nav), `SAP_CMD_BC_CUSTOMER_DSP_PC` (technical), `SAP_CMD_BC_SUPPLIER_DSP_PC` (technical).

| App ID | Description | Read-Only |
|---|---|---|
| `F0735_TRAN` | Check Cash Flow Items | No |
| `F3804_TRAN` | Schedule Jobs for Flow Builder | No |
| `FCLM_VALUT_CORR_TRAN` | Value Date Correction | No |
| `F2332_TRAN` | Cash Flow Analyzer | Yes |
| `F4991_TRAN` | Display Cash Management Logs | Yes |
| `F3940_TRAN` | Bank Account Balance (Deprecated) | Yes |
| `F2986_TRAN` | Manage Memo Records | No |
| `F3029_TRAN` | Quick Create Memo Record | No |
| `F3030_TRAN` | Schedule Jobs for Health Check | Yes |
| `F5285_TRAN` | Schedule Health Check for Cash Management | Yes |
| `F5936_TRAN` | Schedule Jobs for FQM_DELETE | No |
| `F6679_TRAN` | Schedule Jobs for Value Date Correction | No |
| `F6799_TRAN` | Schedule Job for Rebuild Flow Type of Accounting Documents | No |
| `FCLM_BANK_RECONCIL_TRAN` | Bank Account Balance Reconciliation With Drill Down | Yes |
| `FCLM_BNK_AC_RECONCIL_TRAN` | Bank Account Reconciliation (New) | Yes |
| `FCLM_FB2_RECOVERY_TRAN` | Recovery Failed Entries FI Stagings | No |
| `FQM_AGGREGATE_FLOWS_TRAN` | Aggregate Flows | No |
| `FQM_DELETE_TRAN` | Delete Data from One Exposure | No |
| `FQM_INTBAL_AUTOCRT_TRAN` | Automatically Create Initial Balance | No |
| `FQM_DELETE_BS_TRAN` | Delete Data from One Exposure for BS | No |
| `F2388_TRAN` | Monitor Payments | No |
| `FCLM_DEF_BNK_ID_TRAN` | Default Bank Accounts for One Exposure | No |
| `OT30_TRAN` | Planning Correction | No |
| `F7403_TRAN` | Schedule Job for Init One Exposure | No |
| `F1868_TRAN` | Manage Payment Media | No |
| `BIC2S_TRAN` | Import Bank Directories | No |
| `F111_TRAN` | Automatic Payment Transactions for Payment Requests | No |
| `F1765_TRAN` | User Default Parameters | No |
| `F7188_TRAN` | Schedule Job for House Bank Bseg | No |
| `F7609_TRAN` | Schedule Job for Planning Correction | No |
| `F3804_FB_TRAN` | Schedule Job for Flow Builder | No |
| `F3804_FLOW_TYPE_TRAN` | Schedule Jobs for Rebuild Flow Type for Accounting Documents | No |
| `F3804_INIT_TRAN` | Schedule Jobs for Initialize Flows for One Exposure | No |
| `F3804_INS_HOUSE_BANK_TRAN` | Schedule Jobs for Insert House Bank and House Bank Account Data | No |
| `F3804_LIQUIDITY_ITEM_TRAN` | Schedule Jobs for Rebuild Liquidity Item for Accounting Documents | No |
| `F3804_PLANNING_CORR_TRAN` | Schedule Jobs for Planning Correction | No |
| `F8948_TRAN` | Schedule Jobs for Cash Register | No |
| `F8949_TRAN` | Schedule Jobs for Flow Builder: Utility Tool | No |

## Key Apps — Liquidity Planning (SAP_FIN_BC_CM_CASH_SAC_OPS_PC)

BRTs: `SAP_BR_CASH_MANAGER`, `SAP_BR_CASH_SPECIALIST`. No catalog dependencies.

| App ID | Description | Read-Only |
|---|---|---|
| `F7902_CASH_TRAN` | Schedule Plan Data Jobs for Integration in Cash Management | No |
| `SAC_INT_PULL_CASH_TRAN` | Manage Financial Plan Data Jobs for SAP Analytics Cloud Integration | No |

## Key Apps — Cash Snapshots (SAP_FIN_BC_CM_SNAPSHOT_PC)

BRTs: `SAP_BR_CASH_MANAGER`, `SAP_BR_CASH_SPECIALIST`. No catalog dependencies.

| App ID | Description | Read-Only |
|---|---|---|
| `F8945_TRAN` | Schedule Jobs for Cash Snapshots | No |
| `F8962_TRAN` | Manage Cash Snapshots | No |

## Key Apps — Power of Attorney (SAP_FIN_BC_CM_POA_PC & SAP_FIN_BC_CM_POA_APPROVE_PC)

BRTs: `SAP_BR_CASH_MANAGER`, `SAP_BR_CASH_SPECIALIST` (both catalogs).
Dependencies: `SAP_CMD_BC_BP_DISP_PC` — nav dependency for POA_PC, technical for POA_APPROVE_PC.

| App ID | Description | Read-Only | Catalog |
|---|---|---|---|
| `F6959_TRAN` | Manage Payment Approval Rules | No | `POA_PC` |
| `F5742_TRAN` | Manage Powers of Attorney for Banking Transactions | No | `POA_PC` |
| `F6374_TRAN` | Implement Powers of Attorney for Banking Transactions | No | `POA_PC` |
| `F5742_APPROVE_TRAN` | Approve Powers of Attorney for Banking Transactions | No | `POA_APPROVE_PC` |
## Catalog Dependencies

### Outbound (catalogs required by Cash Management catalogs)

| Catalog | Depends On | Dep Type | Title |
|---|---|---|---|
| `SAP_FIN_BC_CM_BAM2_PC` | `SAP_CMD_BC_BP_DISP_PC` | 2 (navigation) | Master Data - Business Partner Display |
| `SAP_FIN_BC_CM_BAM2_PC` | `SAP_CMD_BC_BP_MAINT_PC` | 3 (technical) | Master Data - Business Partner |
| `SAP_FIN_BC_CM_BAM2_PC` | `SAP_CORE_BC_UI_SHARE_PC` | 3 (technical) | User Interface - View Sharing |
| `SAP_FIN_BC_CM_BAM2_BASIC_PC` | `SAP_CMD_BC_BP_DISP_PC` | 2 (navigation) | Master Data - Business Partner Display |
| `SAP_FIN_BC_CM_BAM2_BASIC_PC` | `SAP_CMD_BC_BP_MAINT_PC` | 2 (navigation) | Master Data - Business Partner |
| `SAP_FIN_BC_CM_BAM2_BASIC_PC` | `SAP_CORE_BC_UI_SHARE_PC` | 3 (technical) | User Interface - View Sharing |
| `SAP_FIN_BC_CM_BAM2_BASIC_PC` | `SAP_FIN_BC_BSNAGT_PC` | 3 (technical) | Business Integration - Bank Integration |
| `SAP_FIN_BC_CM_BAM2_BASIC_PC` | `SAP_FIN_BC_PF_IHB_PC` | 3 (technical) | Advanced Payment Management - In-House Banking |
| `SAP_FIN_BC_CM_CASH_OPS_PC` | `SAP_CMD_BC_BP_DISP_PC` | 2 (navigation) | Master Data - Business Partner Display |
| `SAP_FIN_BC_CM_CASH_OPS_PC` | `SAP_CMD_BC_CUSTOMER_DSP_PC` | 2 (navigation) | Master Data - Customer Display |
| `SAP_FIN_BC_CM_CASH_OPS_PC` | `SAP_CMD_BC_SUPPLIER_DSP_PC` | 2 (navigation) | Master Data - Supplier Display |
| `SAP_FIN_BC_CM_CASH_OPS_PC` | `SAP_CORE_BC_UI_SHARE_PC` | 3 (technical) | User Interface - View Sharing |
| `SAP_FIN_BC_CM_OPS_BASIC_PC` | `SAP_CMD_BC_BP_DISP_PC` | 2 (navigation) | Master Data - Business Partner Display |
| `SAP_FIN_BC_CM_OPS_BASIC_PC` | `SAP_CMD_BC_CUSTOMER_DSP_PC` | 3 (technical) | Master Data - Customer Display |
| `SAP_FIN_BC_CM_OPS_BASIC_PC` | `SAP_CMD_BC_SUPPLIER_DSP_PC` | 3 (technical) | Master Data - Supplier Display |
| `SAP_FIN_BC_CM_POA_PC` | `SAP_CMD_BC_BP_DISP_PC` | 2 (navigation) | Master Data - Business Partner Display |
| `SAP_FIN_BC_CM_POA_APPROVE_PC` | `SAP_CMD_BC_BP_DISP_PC` | 3 (technical) | Master Data - Business Partner Display |

`SAP_FIN_BC_CM_BAA_SUBMIT_PC`, `SAP_FIN_BC_CM_BAA_APPROVE_PC`, `SAP_FIN_BC_CM_CASH_SAC_OPS_PC`, and `SAP_FIN_BC_CM_SNAPSHOT_PC` have no dependencies — self-contained.

### Inbound (catalogs that depend on Cash Management catalogs)

| Catalog | Depends On | Dep Type | Title |
|---|---|---|---|
| `SAP_FIN_BC_FACT_BAM_PC` | `SAP_FIN_BC_CM_BAM2_BASIC_PC` | 2 (navigation) | Financials - Bank Account Display |


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
- `F1366A_TRAN` (Manage Bank Accounts — central app): ACTVT `01`, `02`, `03`, `06`
- `F1366_TRAN` (Manage Bank Group Hierarchies): ACTVT `01`, `02`, `03`
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
- `F9015_TRAN` (Monitor Interest): ACTVT `03`, `06` (delete needed — app supports transactional behavior), `F_CLM_BAM` F4 only
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
| `ACTVT` | Activity | `03`=Display, `31`=Approve, `69`=Discard/Cancel |
| `BUKRS` | Company Code | `*` = all |

ACTVT `69` is checked by the RAP behavior (`cancelaccountopeningrequest` action) when a user cancels/discards a bank account application they submitted.

**App coverage:**
- `F5859_TRAN` (Approve Applications): ACTVT `03`, `31`
- `F5860_TRAN` (Applications Overview): ACTVT `03` only
- `F5861_TRAN` (Submit Applications): ACTVT `01`, `02`, `03`, `06`, `69`

### F_CLM_BAH2 — Bank Account Hierarchy
Controls access to bank account hierarchy management.

| Field | Description | Key Values |
|---|---|---|
| `ACTVT` | Activity | `01`=Create, `02`=Change, `03`=Display, `06`=Delete |
| `HIERTYPE` | Hierarchy type | `*` = all |
| `PUBLICHIER` | Public hierarchy | `*` = all |

**App coverage:**
- `F1366_TRAN` (Manage Bank Group Hierarchies): ACTVT `01`, `02`, `03`, `06`

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

| BRT ID | Display Name | Notes |
|---|---|---|
| `SAP_BR_CASH_MANAGER` | Cash Manager | All 11 Cash Management catalogs |
| `SAP_BR_CASH_SPECIALIST` | Cash Management Specialist | 37 catalogs total — includes all 11 Cash Management catalogs plus cross-module display |

Both BRTs share identical access to all Cash Management catalogs: BAM2, BAM2_BASIC, BAA_SUBMIT, BAA_APPROVE, BAI, CASH_OPS, OPS_BASIC, CASH_SAC_OPS, SNAPSHOT, POA, POA_APPROVE.

### SAP_BR_CASH_SPECIALIST — Full Catalog Footprint (37 catalogs)

**Bank Account Management**
| Catalog | Title |
|---|---|
| `SAP_FIN_BC_CM_BAM2_PC` | Cash Management - Bank Accounts Management |
| `SAP_FIN_BC_CM_BAM2_BASIC_PC` | Cash Management - Bank Accounts Management Basic |
| `SAP_FIN_BC_CM_BAA_SUBMIT_PC` | Cash Management - Submit Bank Account Applications |
| `SAP_FIN_BC_CM_BAA_APPROVE_PC` | Cash Management - Approve Bank Account Applications |
| `SAP_FIN_BC_CM_BAI_PC` | Cash Management - Bank Account Interest Management |
| `SAP_FIN_BC_CM_BAL_PC` | Cash Management - Bank Account Balances Management |
| `SAP_FIN_BC_CM_BAR_MANAGE_PC` | Cash Management - Manage Bank Account Reviews |
| `SAP_FIN_BC_CM_BAM_UUID_JOB_PC` | Cash Management - Schedule Jobs for Generating Bank Account Unique IDs |
| `SAP_FIN_BC_FACT_BAM_PC` | Financials - Bank Account Display |

**Cash Operations**
| Catalog | Title |
|---|---|
| `SAP_FIN_BC_CM_CASH_OPS_PC` | Cash Management - Cash Operations |
| `SAP_FIN_BC_CM_OPS_BASIC_PC` | Cash Management - Cash Operations Basic |
| `SAP_FIN_BC_CM_SNAPSHOT_PC` | Cash Management - Snapshots |
| `SAP_FIN_BC_CM_CASH_SAC_OPS_PC` | Cash Management - Liquidity Planning |
| `SAP_FIN_BC_CM_MEMO_MANAGE_PC` | Cash Management - Manage Memo Records |
| `SAP_FIN_BC_CM_MEMO_IMPORT_PC` | Cash Management - Import Memo Records |
| `SAP_FIN_BC_CM_BNK_PC` | Cash Management - Banks Management |
| `SAP_FIN_BC_CM_BFM_PC` | Cash Management - Bank Fee Management |
| `SAP_FIN_BC_CM_CONF_PC` | Cash Management - Configuration |

**Power of Attorney & Payments**
| Catalog | Title |
|---|---|
| `SAP_FIN_BC_CM_POA_PC` | Cash Management - Power of Attorney for Banking Transactions |
| `SAP_FIN_BC_CM_POA_APPROVE_PC` | Cash Management - Approve Powers of Attorney for Banking Transactions |
| `SAP_FIN_BC_BCM_PAYM_DISP_PC` | Bank Communication Management - Payments Display |
| `SAP_FIN_BC_BCM_PAYM_APPR_PC` | Bank Communication Management - Payment Approvals Jobs |

**Bank Accounting**
| Catalog | Title |
|---|---|
| `SAP_FIN_BC_BA_BANKSTAT_PC` | Bank Accounting - Bank Statement |
| `SAP_FIN_BC_BA_CHECK_DEP_PC` | Bank Accounting - Check Deposit |
| `SAP_FIN_BC_BA_PAYREQPRC_PC` | Bank Accounting - Payment Request Processing |
| `SAP_FIN_BC_BA_NRO_PC` | Bank Accounting - Adjust Number Ranges |

**Master & Reference Data**
| Catalog | Title |
|---|---|
| `SAP_CMD_BC_BP_DISP_PC` | Master Data - Business Partner Display |
| `SAP_CMD_BC_CUSTOMER_DSP_PC` | Master Data - Customer Display |
| `SAP_CMD_BC_SUPPLIER_DSP_PC` | Master Data - Supplier Display |
| `SAP_CA_BC_BNK_PC` | Bank - Maintenance |
| `SAP_FIN_BC_PF_IHB_PC` | Advanced Payment Management - In-House Banking |

**Cross-Module Display**
| Catalog | Title |
|---|---|
| `SAP_FIN_BC_GL_CASHJE_PC` | General Ledger - Cash Journal Entries |
| `SAP_FIN_BC_DSPL_ACDOC_PC` | Finance - Show Accounting Document |
| `SAP_MM_BC_PURCH_DOC_DSP_PC` | Materials Management - Purchasing Document Display |
| `SAP_MM_BC_SOURC_DOC_DSP_PC` | Materials Management - Sourcing Document Display |
| `SAP_SD_BC_SO_DISPL_PC` | Sales - Sales Order Display |
| `SAP_SD_BC_SSA_DISPL_PC` | Sales - Sales Scheduling Agreement Display |

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
| `F1366A_TRAN` | 01, 02, 03, 06 | — | — | Central app — create/change/delete bank accounts |
| `F1366_TRAN` | 01, 02, 03 | — | — | Manage bank group hierarchies (also has F_CLM_BAH2) |
| `F5861_TRAN` | — | 01, 02, 03, 06, 69 | — | Submit account applications (69=cancel own request) |
| `F5860_TRAN` | — | 03 | — | View account applications (read-only) |
| `F5859_TRAN` | — | 03, 31 | — | Approve account applications |
| `F6264_TRAN` | 03, 63 | — | 01, 02, 03 | Approve account change requests |

### SoD Concerns

There are no IAM-level SoD rules for bank account management. All 4-eyes / 2-person verification controls are enforced at the **application/workflow code level**:

- **Submit vs. Approve bank account applications** (`F5861_TRAN` vs. `F5859_TRAN`): self-approval is blocked in code — a different user ID is required for approval. Holding both catalogs (`BAA_SUBMIT_PC` + `BAA_APPROVE_PC`) is not an IAM violation.
- **Create bank accounts vs. approve change requests** (`F1366_TRAN` vs. `F6264_TRAN`): the 2-person verification procedure requires a different user ID at approval time, enforced in code. Holding both in the same BRT/catalog is not an IAM violation.

No catalog-level SoD separation is required for these workflows.

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

### F1366_TRAN — Manage Bank Group Hierarchies

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
| 69 | Discard / Cancel (cancel bank account application — `cancelaccountopeningrequest` RAP action) |
| F4 | Value help (F4 search) |

---

## Use Case: General Troubleshooting — App Not Found / Not Accessible

### Purpose
Diagnose why a user cannot find or access a Fiori app. Walk through a systematic checklist to identify the root cause and recommend a resolution.

### Trigger
User says any of:
- "App `<APP_ID>` is not showing in the launchpad"
- "User cannot find `<T-Code or app name>`"
- "App not found in system"
- "`<APP_ID>` is missing for a user"

### Diagnostic Checklist — 5 Root Causes in Order

Work through each check in sequence. Stop and report as soon as a failure is found.

---

**Check 1 — Does the app exist in the system?**
```sql
SELECT APP_ID, APP_TYPE, TCODE, READ_ONLY FROM APS_IAM_W_APP WHERE APP_ID = '<APP_ID>'
SELECT TEXT FROM APS_IAM_W_APPT WHERE APP_ID = '<APP_ID>' AND LANGU = 'E'
```
- If no rows returned → **Root Cause 1: App does not exist.** Check spelling. If user provided a T-Code instead of App ID, query: `SELECT APP_ID, TCODE FROM APS_IAM_W_APP WHERE TCODE = '<TCODE>'`
- If app name contains "Deprecated" → **Root Cause 1b: App is deprecated.** Identify the successor app.

---

**Check 2 — Is the app assigned to a catalog?**
```sql
SELECT BU_CATALOG_ID, APP_ID FROM APS_IAM_W_BC_APP WHERE APP_ID = '<APP_ID>'
```
- If no rows returned → **Root Cause 2: App exists but is not assigned to any catalog.** This is an IAM configuration gap — the app needs to be added to the appropriate catalog.
- If rows returned → note the catalog ID(s) and proceed.

---

**Check 3 — Is the catalog assigned to a BRT?**
```sql
SELECT BRT_ID FROM APS_IAM_W_BRTBUC WHERE BU_CATALOG_ID = '<CATALOG_ID>'
```
- If no rows returned → **Root Cause 3: Catalog exists but no BRT carries it.** The catalog is orphaned — no standard role delivers this app. Escalate to IAM team for role design review.
- If rows returned → note the BRT ID(s) and proceed.

---

**Check 4 — Does the user have the BRT?**
This check cannot be done via IAM tables alone — user-to-role assignment is in PFCG/user master data. Advise the user to:
- Check in SAP via `SU01` → user → Roles tab, look for the BRT name
- Or ask their system administrator to confirm the BRT assignment

If the BRT is not assigned → **Root Cause 4: User does not have the required BRT.**
Recommendation: Assign `<BRT_ID>` to the user.

---

**Check 5 — Are there catalog dependencies missing?**
```sql
SELECT DEP_BU_CATALOG_ID, DEP_TYPE FROM APS_IAM_W_BUCDEP WHERE BU_CATALOG_ID = '<CATALOG_ID>'
```
Even if the user has the correct BRT, missing prerequisite catalogs can cause navigation failures or app visibility issues.
- If dependency rows returned → verify the user also has the dependent catalogs (especially type 2 = navigation dependencies)
- If prerequisites are missing → **Root Cause 5: Missing prerequisite catalog.**

---

### Output Format

```
APP: <APP_ID> — <Description>
T-Code: <TCODE>

DIAGNOSTIC RESULT
-----------------
✓ Check 1 — App exists in system
✓ Check 2 — App assigned to catalog: <CATALOG_ID>
✓ Check 3 — Catalog carried by BRT: <BRT_ID>
✗ Check 4 — User does not have BRT <BRT_ID>

ROOT CAUSE
----------
User is missing BRT <BRT_ID> (<BRT display name>).

RESOLUTION
----------
Assign <BRT_ID> to the user via user administration (SU01 / role assignment).
<Any SoD or prerequisite catalog notes>
```

Use ✓ for passed checks, ✗ for the failing check. Stop at the first failure.

---

### Quick Lookup: App ID from T-Code

If the user provides a T-Code instead of an App ID:
```sql
SELECT APP_ID, TCODE, READ_ONLY FROM APS_IAM_W_APP WHERE TCODE = '<TCODE>'
```
Note: multiple apps can share the same T-Code (e.g. `F1366` is used by both `F1366_TRAN` and `F1366A_TRAN`). Present all matches and ask the user to confirm which one they are looking for.



### Purpose
Translate a missing authorization error into a business recommendation — identify which app carries the required auth object and activity, which catalog it belongs to, and which BRT to assign.

### Trigger
User says any of:
- "User is missing `F_CLM_*` ACTVT `XX`"
- "Authorization error for `<AUTH_OBJECT>`"
- "User cannot `<business action>` — what authorization is needed?"
- Pastes an SU53 output or runtime dump mentioning an auth object

### Step-by-Step Procedure

**Step 1 — Identify the auth object and activity**

Map the missing auth object + ACTVT to a business meaning using the quick reference:

| Auth Object | ACTVT | Business Meaning |
|---|---|---|
| `F_CLM_BAM` | 01/02/06 | Create/Change/Delete bank accounts |
| `F_CLM_BAM` | 03 | Display bank accounts |
| `F_CLM_BAOR` | 31 | Approve bank account applications |
| `F_CLM_BAOR` | 69 | Cancel/discard bank account applications |
| `F_CLM_BKCR` | 01/02/03 | Create/Change/Display change requests |
| `F_CLM_BAIC` | 01/02/06 | Create/Change/Delete interest conditions |
| `F_CLM_BAI` | 06 | Delete interest records |
| `F_CLM_BAH2` | 01/02/06 | Create/Change/Delete bank group hierarchies |

**Step 2 — Find all active apps carrying that auth object**
```sql
SELECT APP_ID, UUID, AUTH_OBJECT, STATUS, INACTIVE
FROM APS_IAM_W_APPAUI WHERE AUTH_OBJECT = '<AUTH_OBJECT>' AND INACTIVE = ''
```

**Step 3 — Filter to apps that have the specific ACTVT**
```sql
SELECT PARENT_ID, FIELD, LOW_VALUE
FROM APS_IAM_W_APPAUV WHERE PARENT_ID = '<UUID>' AND FIELD = 'ACTVT'
```
Match UUID from Step 2. Keep only apps whose ACTVT list includes the missing value.

**Step 4 — Trace to catalog**
```sql
SELECT BU_CATALOG_ID FROM APS_IAM_W_BC_APP WHERE APP_ID = '<APP_ID>'
```

**Step 5 — Trace to BRT**
```sql
SELECT BRT_ID FROM APS_IAM_W_BRTBUC WHERE BU_CATALOG_ID = '<CATALOG_ID>'
```

**Step 6 — Output recommendation**

---

### Output Format

```
Missing:  <AUTH_OBJECT> / ACTVT <XX> (<business meaning>)
    │
    ▼
App:      <APP_ID> — <App Description>
    │
    ▼
Catalog:  <BU_CATALOG_ID>
    │
    ▼
BRT:      <BRT_ID>  or  <BRT_ID_1> / <BRT_ID_2>

RECOMMENDATION
--------------
Assign catalog <BU_CATALOG_ID> via BRT <BRT_ID>.
<Context note: SoD implications, 2-person enforcement, or scope restrictions if relevant>
```

If multiple apps carry the same ACTVT, list all and help the user identify which one matches their use case based on app description and catalog context.

---

### Known Authorization → App Mappings (verified from ER6)

| Auth Object | ACTVT | App | Catalog | BRT(s) |
|---|---|---|---|---|
| `F_CLM_BAM` | 01, 02, 06 | `F1366A_TRAN` | `SAP_FIN_BC_CM_BAM2_BASIC_PC` | CASH_MANAGER, CASH_SPECIALIST |
| `F_CLM_BAM` | 01, 02, 03 | `F1366_TRAN` | `SAP_FIN_BC_CM_BAM2_PC` | CASH_MANAGER, CASH_SPECIALIST |
| `F_CLM_BAOR` | 31 | `F5859_TRAN` | `SAP_FIN_BC_CM_BAA_APPROVE_PC` | CASH_MANAGER, CASH_SPECIALIST |
| `F_CLM_BAOR` | 01, 02, 06, 69 | `F5861_TRAN` | `SAP_FIN_BC_CM_BAA_SUBMIT_PC` | CASH_SPECIALIST |
| `F_CLM_BKCR` | 01, 02, 03 | `F6264_TRAN` | `SAP_FIN_BC_CM_BAM2_PC` | CASH_MANAGER, CASH_SPECIALIST |
| `F_CLM_BAIC` | 01, 02, 06 | `F9017_TRAN` | `SAP_FIN_BC_CM_BAI_PC` | CASH_MANAGER, CASH_SPECIALIST |
| `F_CLM_BAI` | 01, 02, 06 | `F9016_TRAN` | `SAP_FIN_BC_CM_BAI_PC` | CASH_MANAGER, CASH_SPECIALIST |
| `F_CLM_BAI` | 06 | `F9015_TRAN` | `SAP_FIN_BC_CM_BAI_PC` | CASH_MANAGER, CASH_SPECIALIST |
| `F_CLM_BAH2` | 01, 02, 06 | `F1366_TRAN` | `SAP_FIN_BC_CM_BAM2_PC` | CASH_MANAGER, CASH_SPECIALIST |



### Purpose
Review an app's authorization object setup as a senior IAM developer would — checking for wrong default status, missing activities, unexpected write access, inactive objects that should be active, and non-standard object usage.

### Trigger
User says any of:
- "Review [APP_ID]"
- "Check SU22 for [APP_ID]"
- "Validate authorization setup for [APP_ID]"
- "Is [APP_ID] correctly set up?"

### Step-by-Step Procedure

**Step 1 — Fetch app metadata**
```sql
SELECT APP_ID, APP_TYPE, TCODE, READ_ONLY FROM APS_IAM_W_APP WHERE APP_ID = '<APP_ID>'
SELECT APP_ID, TEXT FROM APS_IAM_W_APPT WHERE APP_ID = '<APP_ID>' AND LANGU = 'E'
SELECT BU_CATALOG_ID, APP_ID FROM APS_IAM_W_BC_APP WHERE APP_ID = '<APP_ID>'
```
Establishes: what the app is, whether it is read-only, and which catalog it belongs to.

**Step 2 — Fetch all auth object instances**
```sql
SELECT APP_ID, UUID, AUTH_OBJECT, STATUS, INACTIVE FROM APS_IAM_W_APPAUI WHERE APP_ID = '<APP_ID>'
```
Note every row. Key columns:
- `STATUS`: `G` = standard (group), `S` = single — both are valid active statuses
- `INACTIVE`: blank = active, `X` = inactive

**Step 3 — Fetch all auth values**
```sql
SELECT APP_ID, UUID, PARENT_ID, FIELD, LOW_VALUE, HIGH_VALUE, STATUS FROM APS_IAM_W_APPAUV WHERE APP_ID = '<APP_ID>'
```
Join `PARENT_ID` → `UUID` from Step 2 to map values to their auth object instance.

**Step 4 — Apply the review checklist (see below)**

**Step 5 — Output structured findings**

---

### Review Checklist

#### Check 1 — Default Status Validation
For every auth object instance, `STATUS` should be either `G` (group/standard) or `S` (single/standard).
- Flag if STATUS is blank or unexpected value
- An auth object with `INACTIVE = X` is intentionally disabled — verify this is deliberate, especially for objects that look like they should be active (e.g., a core auth object like `F_CLM_BAM` marked inactive on a write app is suspicious)

#### Check 2 — ACTVT Completeness vs. App Purpose
Compare the actual ACTVT values against the expected set for the app's purpose:

| App Purpose | Expected ACTVT on primary object |
|---|---|
| Full CRUD (create/change/delete) | 01, 02, 03, 06 |
| Approve workflow | 03, 31 |
| Submit workflow | 01, 02, 03, 06 (+ 69 for cancel if BAOR) |
| Display / read-only | 03 only (+ F4 if value help needed) |
| Scheduling job app | Full CRUD on managed object (01/02/03/06) |
| Monitor / reporting | 03 + possibly 06 — monitor apps in Cash Management can support transactional behavior (e.g. delete) even if the name implies read-only. Always confirm with domain knowledge before flagging 06 as unexpected. |

Flag if:
- A **read-only app** (`READ_ONLY = X`) has write activities (01/02/06) on its primary auth object → **violation**
- A **write app** is missing Create (01) or Change (02) when the app description implies it → **gap**
- **Delete (06)** is present on an app that has no delete function — raise as a question
- **Approve (31)** appears on an app that is not an approval app → **violation**

#### Check 3 — Scope Field Coverage
For Cash Management auth objects, scope fields should be `*` (all) in cloud deployments:
- `F_CLM_BAM`: `FCLM_BUKRS`, `FCLM_ACTY`, `FCLM_GSBER`, `FCLM_KOKRS`, `FCLM_PRCTR`, `FCLM_SGMT` — all should be `*`
- `F_CLM_BAOR`: `BUKRS` — should be `*`
- `F_CLM_BAI`: `BUKRS`, `FCLM_ACTY` — should be `*`
- `F_CLM_BAIC`: `IC_AUTHGR` — should be `*`
- `F_CLM_BKCR`: `BKCR_AUGRP`, `BKCR_TYPE` — should be `*`

Flag any scope field with a hardcoded value (not `*`) — in cloud this is usually incorrect and indicates a copy/paste error from on-premise configuration.

#### Check 4 — Non-Standard / Unexpected Auth Objects
Flag any auth object that:
- Does not belong to the `F_CLM_*` or `F_BNKA_*` or `F_BUKRS_*` family for a Cash Management app
- Appears inactive (`INACTIVE = X`) but is a core object — confirm whether deactivation is intentional
- Is a generic cross-app object (e.g., `S_TABU_NAM`, `S_DEVELOP`) — these should not normally appear in a business app's SU22 definition

#### Check 5 — F4 / Value Help Consistency
Apps that have company code or bank country input fields should include:
- `F_BUKRS_MD` with `ACTVT = F4` — for company code value help
- `F_BNKA_MAO` with `ACTVT = F4` (and optionally `03`) — for bank/bank country value help

If these are missing on an app that clearly needs company code or bank input, flag as a potential usability gap (users won't get search help).

---

### Output Format

Always present findings in this structure:

```
APP: <APP_ID> — <App Description>
Catalog: <BU_CATALOG_ID>
Read-Only flag: Yes / No
T-Code: <TCODE>

AUTH OBJECT REVIEW
------------------
<AUTH_OBJECT> | STATUS: <G/S> | INACTIVE: <blank/X>
  ACTVT: <list of values>
  Other fields: <FIELD=VALUE, ...>
  → [OK / FLAG: <reason>]

...repeat for each auth object...

FINDINGS SUMMARY
----------------
[PASS] No issues found.

— or —

[FLAG] <AUTH_OBJECT>: <specific issue and recommendation>
[QUESTION] <AUTH_OBJECT>: <something that needs human confirmation>
```

Use `[FLAG]` for clear violations or gaps.
Use `[QUESTION]` for things that look unusual but may be intentional — always ask rather than assume.
Use `[PASS]` only when all checks are clean.

---

### Known Good Baselines (verified from ER6)

Use these as the reference when reviewing. Any delta from these should be flagged.

| App | Auth Object | Expected ACTVT | Scope Fields |
|---|---|---|---|
| `F1366A_TRAN` | `F_CLM_BAM` | 01, 02, 03, 06 | FCLM_BUKRS=*, FCLM_ACTY=*, FCLM_GSBER=*, FCLM_KOKRS=*, FCLM_PRCTR=*, FCLM_SGMT=* |
| `F1366_TRAN` | `F_CLM_BAM` | 01, 02, 03 | FCLM_BUKRS=*, FCLM_ACTY=*, FCLM_GSBER=*, FCLM_KOKRS=*, FCLM_PRCTR=*, FCLM_SGMT=* |
| `F1366_TRAN` | `F_CLM_BAH2` | 01, 02, 03, 06 | HIERTYPE=*, PUBLICHIER=* |
| `F5859_TRAN` | `F_CLM_BAOR` | 03, 31 | BUKRS=* |
| `F5860_TRAN` | `F_CLM_BAOR` | 03 | BUKRS=* |
| `F5861_TRAN` | `F_CLM_BAOR` | 01, 02, 03, 06, 69 | BUKRS=* |
| `F6264_TRAN` | `F_CLM_BAM` | 03, 63 | FCLM_BUKRS=*, FCLM_ACTY=*, FCLM_GSBER=*, FCLM_KOKRS=*, FCLM_PRCTR=*, FCLM_SGMT=* |
| `F6264_TRAN` | `F_CLM_BKCR` | 01, 02, 03 | BKCR_AUGRP=*, BKCR_TYPE=* |
| `F9015_TRAN` | `F_CLM_BAI` | 03, 06 | BUKRS=*, FCLM_ACTY=* — Delete (06) required: app supports transactional behavior |
| `F9015_TRAN` | `F_CLM_BAM` | F4 | FCLM_BUKRS=*, FCLM_ACTY=*, FCLM_GSBER=*, FCLM_KOKRS=*, FCLM_PRCTR=*, FCLM_SGMT=* |
| `F9016_TRAN` | `F_CLM_BAI` | 01, 02, 03, 06 | BUKRS=*, FCLM_ACTY=* |
| `F9016_TRAN` | `F_CLM_BAM` | 03, F4 | FCLM_BUKRS=*, FCLM_ACTY=*, FCLM_GSBER=*, FCLM_KOKRS=*, FCLM_PRCTR=*, FCLM_SGMT=* |
| `F9017_TRAN` | `F_CLM_BAIC` | 01, 02, 03, 06, F4 | IC_AUTHGR=* |
| `F9017_TRAN` | `F_CLM_BAI` | 03 | BUKRS=*, FCLM_ACTY=* |
| `F9017_TRAN` | `F_CLM_BAM` | 03 | FCLM_BUKRS=*, FCLM_ACTY=*, FCLM_GSBER=*, FCLM_KOKRS=*, FCLM_PRCTR=*, FCLM_SGMT=* |


