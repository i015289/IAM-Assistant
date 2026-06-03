---
name: fin-iam
description: Use this skill when the user asks about Finance IAM for Accounts Payable (CLOUD_FI_AP_IAM), Accounts Receivable (CLOUD_FI_AR_IAM), General Ledger (CLOUD_FI_GL_IAM), or Bank Accounting (CLOUD_FI_BA_IAM) — including app/catalog analysis, SoD validation, auth object inspection, BRT coverage, and IAM health checks.
---

## Suggested Prompts

When this skill is activated, greet the user and offer the following prompt suggestions before waiting for their input:

> **Finance IAM (AP / AR / GL / BA) — Example Prompt Library**
>
> **Authorization & App Analysis**
> 1. For IAM App ID `<APP_ID>`, show all active authorization object instances and their field values.
> 2. For IAM App ID `<APP_ID>`, verify whether the activity set is complete and aligned with the app's intended business purpose.
>
> **Catalog & BRT Structure**
> 3. For Business Catalog `<BC_ID>`, list all assigned apps and verify catalog–BRT linkage.
> 4. For Business Role Template `<BRT_ID>`, show the full catalog and app footprint.
>
> **SoD & Four-Eyes Validation**
> 5. For a given user or role combination, check whether AP invoice creation and AP payment approval are held by the same role (4-eyes violation).
> 6. For AR, verify that dunning and incoming payment posting are not both held by a single role without oversight.
>
> **Payment Flow Analysis**
> 7. For the AP payment run flow (`F0770_TRAN` → `F0771_TRAN` → `F0673A_TRAN`), trace auth objects and confirm SoD between proposal, revision, and approval.
> 8. For AR clearing (`F0773_TRAN`) and incoming payment posting (`F1345_TRAN`), validate the authorization setup against expected activities.
>
> **GL Journal Entry Controls**
> 9. For the GL journal entry flow (post / park / verify), trace auth objects `F_BKPF_BUK`, `F_BKPF_BLA`, `F_BKPF_KOA` and confirm posting controls.
> 10. For IAM App ID `<APP_ID>` in GL, run a full IAM health check: auth objects, activity sets, catalog assignment, BRT coverage.

---

# Finance IAM Skill

You are a Finance IAM specialist for SAP S/4HANA Cloud, analyzing apps in ER6.

Use MCP tools (`mcp__er6__query_sql`, etc.) for all queries.
- ABAP Open SQL — no JOINs, no subqueries
- Use the `rows` parameter for row limits; **never** use `UP TO N ROWS` inline when a `WHERE` clause is present

---

## Packages in Scope

| Package | Area |
|---|---|
| `CLOUD_FI_AP_IAM` | Accounts Payable |
| `CLOUD_FI_AR_IAM` | Accounts Receivable |
| `CLOUD_FI_GL_IAM` | General Ledger |
| `CLOUD_FI_BA_IAM` | Bank Accounting |

To list all SIA6 apps in a package:
```sql
SELECT PGMID, OBJECT, OBJ_NAME FROM TADIR
WHERE DEVCLASS = '<PACKAGE>' AND OBJECT = 'SIA6'
```

---

## Business Role Templates (Core Global)

### Accounts Payable

| BRT ID | Display Name | Key Catalogs |
|---|---|---|
| `SAP_BR_AP_ACCOUNTANT` | Accounts Payable Accountant | `SAP_FIN_BC_AP_INVOICES_PC`, `SAP_FIN_BC_AP_OPE_PROC_PC`, `SAP_FIN_BC_AP_CLEARING_PC`, `SAP_FIN_BC_AP_REVERSAL_PC`, `SAP_FIN_BC_AP_CHECK_PC`, `SAP_FIN_BC_AP_PAYM_DISP_PC`, `SAP_FIN_BC_AP_MY_INBOX_PC`, `SAP_FIN_BC_AP_PERIODIC_ACT_PC`, `SAP_FIN_BC_APAR_PAY_PC`, `SAP_FIN_BC_AP_ADHOC_PAY_PC`, `SAP_FIN_BC_AP_DPR_VER_PC`, `SAP_FIN_BC_APAR_DP_REQ_PC`, `SAP_FIN_BC_APAR_CORR_PC`, `SAP_FIN_BC_AP_DOC_DISP_PC`, `SAP_FIN_BC_AP_BI_HDL_PC`, `SAP_FIN_BC_AP_PMTMDIA_PROC_PC` |
| `SAP_BR_AP_MANAGER` | Accounts Payable Manager | `SAP_FIN_BC_AP_ANALYTICS_PC`, `SAP_FIN_BC_AP_PAY_APV_PC`, `SAP_FIN_BC_AP_CURR_SET_PC`, `SAP_FIN_BC_AP_CHECK_PC`, `SAP_FIN_BC_AP_WRKFLW_PC`, `SAP_FIN_BC_AP_DPR_VER_PC` |

Country variants (`_CN`, `_JP`, `_DE`, etc.) follow the same core catalog pattern plus country-specific reporting catalogs.

### Accounts Receivable

| BRT ID | Display Name | Key Catalogs |
|---|---|---|
| `SAP_BR_AR_ACCOUNTANT` | Accounts Receivable Accountant | `SAP_FIN_BC_AR_INVOICE_PC`, `SAP_FIN_BC_AR_DOC_PROC_PC`, `SAP_FIN_BC_AR_INC_PAY_PC`, `SAP_FIN_BC_AR_OUT_PAYM_PC`, `SAP_FIN_BC_AR_CLEARING_PC`, `SAP_FIN_BC_AR_DUNNING_PC`, `SAP_FIN_BC_AR_DISPUTES_PC`, `SAP_FIN_BC_AR_COLWL_PC`, `SAP_FIN_BC_AR_SEPA_EDIT_PC`, `SAP_FIN_BC_AR_PERIODIC_ACT_PC`, `SAP_FIN_BC_AR_PAYM_ADV_PC`, `SAP_FIN_BC_APAR_PAY_PC`, `SAP_FIN_BC_APAR_DP_REQ_PC`, `SAP_FIN_BC_APAR_CORR_PC`, `SAP_FIN_BC_AR_DOC_DISP_PC`, `SAP_FIN_BC_AR_DM_PERIOD_PC` |
| `SAP_BR_AR_MANAGER` | Accounts Receivable Manager | `SAP_FIN_BC_AR_ANALYTICS_PC`, `SAP_FIN_BC_AR_COL_ANALY_PC`, `SAP_FIN_BC_AR_SUP_COLWL_PC`, `SAP_FIN_BC_AR_COL_SETTINGS_PC`, `SAP_FIN_BC_AR_DM_ANALYTICS_PC`, `SAP_FIN_BC_AR_DM_SETTINGS_PC`, `SAP_FIN_BC_AR_CURR_SET_PC`, `SAP_FIN_BC_AR_TRF_AGR_PROC_PC`, `SAP_FIN_BC_AR_TRF_DOC_CANC_PC`, `SAP_FIN_BC_AR_NRO_PC` |

### General Ledger

| BRT ID | Display Name | Key Catalogs |
|---|---|---|
| `SAP_BR_GL_ACCOUNTANT` | General Ledger Accountant | `SAP_FIN_BC_GL_JE_PROC_PC`, `SAP_FIN_BC_GL_PARKDCPRE_PC`, `SAP_FIN_BC_GL_PARKDCPST_PC`, `SAP_FIN_BC_GL_CLOSING_PC`, `SAP_FIN_BC_GL_REPORTING_PC`, `SAP_FIN_BC_GL_ACC_OVR_PC`, `SAP_FIN_BC_GL_ALLOC_PROC_PC`, `SAP_FIN_BC_GL_ALLOC_MAINT_PC`, `SAP_FIN_BC_GL_CASHJE_PC`, `SAP_FIN_BC_GL_JE_CLRING_PC`, `SAP_FIN_BC_GL_PLN_PC`, `SAP_FIN_BC_GL_EBALSHEET_PC`, `SAP_FIN_BC_GL_TX_DCL_PC`, `SAP_FIN_BC_GL_COA_PC`, `SAP_FIN_BC_GL_ANALYTICS_PC`, `SAP_FIN_BC_GL_PER_MGMT_PC` |
| `SAP_BR_GL_ACCOUNTANT_GRP` | General Ledger Accountant - Group Reporting | Same core + group reporting catalogs |

### Bank Accounting

| BRT ID | Display Name | Key Catalogs |
|---|---|---|
| `SAP_BR_BANK_INT_SPECIALIST` | Business Integration Specialist - Bank Integration | `SAP_FIN_BC_BA_BANKSTAT_PC`, `SAP_FIN_BC_BA_BANKSTRP_PC`, `SAP_FIN_BC_BA_BSM_JOB_PC`, `SAP_FIN_BC_BA_LOCKBOX_PC`, `SAP_FIN_BC_BA_CHECK_DEP_PC`, `SAP_FIN_BC_BA_CHAINS_PC` |

BA catalogs also appear in `SAP_BR_AR_ACCOUNTANT` (bank statement reprocessing) and `SAP_BR_AP_ACCOUNTANT` (bank chains).

---

## Key Business Catalogs

### Accounts Payable — Core Catalogs

| Catalog ID | Title |
|---|---|
| `SAP_FIN_BC_AP_INVOICES_PC` | Accounts Payable - Invoices |
| `SAP_FIN_BC_AP_OPE_PROC_PC` | Accounts Payable - Operational Processing |
| `SAP_FIN_BC_AP_CLEARING_PC` | *(derive from AR pattern)* AP Clearing |
| `SAP_FIN_BC_AP_REVERSAL_PC` | Accounts Payable - Reversal |
| `SAP_FIN_BC_AP_CHECK_PC` | Accounts Payable - Checks |
| `SAP_FIN_BC_AP_PAYM_DISP_PC` | Accounts Payable - Payments Display |
| `SAP_FIN_BC_AP_MY_INBOX_PC` | Accounts Payable - My Inbox |
| `SAP_FIN_BC_AP_PERIODIC_ACT_PC` | Accounts Payable - Periodic Activities |
| `SAP_FIN_BC_APAR_PAY_PC` | Accounts Payable and Receivable - Payments |
| `SAP_FIN_BC_AP_ADHOC_PAY_PC` | Accounts Payable - Ad Hoc Payments |
| `SAP_FIN_BC_AP_PAY_APV_PC` | Accounts Payable - Payment Approval |
| `SAP_FIN_BC_AP_DPR_VER_PC` | Accounts Payable - Supplier Down Payment Request Verification |
| `SAP_FIN_BC_APAR_DP_REQ_PC` | Accounts Payable and Receivable - Down Payments |
| `SAP_FIN_BC_APAR_CORR_PC` | Accounts Payable and Receivable - Correspondence |
| `SAP_FIN_BC_AP_DOC_DISP_PC` | Accounts Payable - Document Display |
| `SAP_FIN_BC_AP_ANALYTICS_PC` | Accounts Payable - Analytics |
| `SAP_FIN_BC_AP_PMTMDIA_PROC_PC` | Accounts Payable - Payment Media Processing |
| `SAP_FIN_BC_AP_BI_HDL_PC` | Accounts Payable - Batch Input Sessions Handling |
| `SAP_FIN_BC_AP_WRKFLW_PC` | Accounts Payable - Workflow (Manager) |
| `SAP_FIN_BC_AP_CURR_SET_PC` | Accounts Payable - Current Settings |
| `SAP_FIN_BC_APAR_INTCALC_R_PC` | Accounts Payable and Receivable - Interest Calculation Run |
| `SAP_FIN_BC_APAR_INTCALC_D_PC` | Accounts Payable and Receivable - Display Interest Calculation |
| `SAP_FIN_BC_AP_STATIS_POST_PC` | Accounts Payable - Statistical Posting |
| `SAP_FIN_BC_AP_BKACCTVALDTN_PC` | Accounts Payable - Bank Account Validation |
| `SAP_FIN_BC_FACT_SUPPINV_PC` | Supplier Invoice Factoring |

### Accounts Receivable — Core Catalogs

| Catalog ID | Title |
|---|---|
| `SAP_FIN_BC_AR_INVOICE_PC` | Accounts Receivable - Invoices |
| `SAP_FIN_BC_AR_DOC_PROC_PC` | Accounts Receivable - Document Processing |
| `SAP_FIN_BC_AR_INC_PAY_PC` | Accounts Receivable - Incoming Payments |
| `SAP_FIN_BC_AR_OUT_PAYM_PC` | Accounts Receivable - Outgoing Payments |
| `SAP_FIN_BC_AR_CLEARING_PC` | Accounts Receivable - Clearing |
| `SAP_FIN_BC_AR_DUNNING_PC` | Accounts Receivable - Dunning |
| `SAP_FIN_BC_AR_DISPUTES_PC` | Accounts Receivable - Dispute Resolution |
| `SAP_FIN_BC_AR_COLWL_PC` | Accounts Receivable - Collections |
| `SAP_FIN_BC_AR_SEPA_EDIT_PC` | Accounts Receivable - SEPA Mandates |
| `SAP_FIN_BC_AR_SEPA_DISP_PC` | Accounts Receivable - SEPA Mandates Display |
| `SAP_FIN_BC_AR_PERIODIC_ACT_PC` | Accounts Receivable - Periodic Activities |
| `SAP_FIN_BC_AR_PAYM_ADV_PC` | Accounts Receivable - Payment Advices |
| `SAP_FIN_BC_AR_DOC_DISP_PC` | Accounts Receivable - Document Display |
| `SAP_FIN_BC_AR_ANALYTICS_PC` | Accounts Receivable - Analytics |
| `SAP_FIN_BC_AR_DM_PERIOD_PC` | Accounts Receivable - Periodic Activities for Dispute Management |
| `SAP_FIN_BC_AR_DM_ANALYTICS_PC` | Accounts Receivable - Dispute Management Analytics |
| `SAP_FIN_BC_AR_DM_SETTINGS_PC` | Accounts Receivable - Dispute Management Settings |
| `SAP_FIN_BC_AR_COL_ANALY_PC` | Accounts Receivable - Collections Analytics |
| `SAP_FIN_BC_AR_SUP_COLWL_PC` | Accounts Receivable - Supervise Collections Worklist |
| `SAP_FIN_BC_AR_COL_SETTINGS_PC` | Accounts Receivable - Collections Settings |
| `SAP_FIN_BC_AR_CURR_SET_PC` | Accounts Receivable - Current Settings |
| `SAP_FIN_BC_AR_TRF_AGR_PROC_PC` | Accounts Receivable - Receivables Financing Agreements |
| `SAP_FIN_BC_AR_TRF_DOC_PROC_PC` | Accounts Receivable - Receivables Financing Documents |
| `SAP_FIN_BC_AR_TRF_DOC_CANC_PC` | Accounts Receivable - Receivables Financing Document Cancellation |
| `SAP_FIN_BC_AR_NRO_PC` | Accounts Receivable - Adjust Number Ranges |
| `SAP_FIN_BC_AR_STATIS_POST_PC` | Accounts Receivable - Statistical Posting |
| `SAP_FIN_BC_DCO_DISPUTE_PC` | Dispute/Collections Management |
| `SAP_FIN_BC_DCO_PROC_PC` | Dispute/Collections Processing |

### General Ledger — Core Catalogs

| Catalog ID | Title |
|---|---|
| `SAP_FIN_BC_GL_JE_PROC_PC` | General Ledger - Journal Entry Processing |
| `SAP_FIN_BC_GL_PARKDCPRE_PC` | General Ledger - Submit Journal Entries for Verification |
| `SAP_FIN_BC_GL_PARKDCPST_PC` | General Ledger - Verify Journal Entries |
| `SAP_FIN_BC_GL_CLOSING_PC` | General Ledger - Closing |
| `SAP_FIN_BC_GL_REPORTING_PC` | General Ledger - Reporting |
| `SAP_FIN_BC_GL_ACC_OVR_PC` | General Ledger - Accountant Overview |
| `SAP_FIN_BC_GL_ALLOC_PROC_PC` | General Ledger - Allocation |
| `SAP_FIN_BC_GL_ALLOC_MAINT_PC` | General Ledger - Allocation Master Data |
| `SAP_FIN_BC_GL_CASHJE_PC` | General Ledger - Cash Journal Entries |
| `SAP_FIN_BC_GL_JE_CLRING_PC` | General Ledger - Journal Entry Clearing |
| `SAP_FIN_BC_GL_PLN_PC` | General Ledger Accounting - Planning |
| `SAP_FIN_BC_GL_EBALSHEET_PC` | General Ledger - Electronic Balance Sheet |
| `SAP_FIN_BC_GL_TX_DCL_PC` | General Ledger - Tax Declaration |
| `SAP_FIN_BC_GL_COA_PC` | G/L Account Master Data - Configuration |
| `SAP_FIN_BC_GL_ANALYTICS_PC` | General Ledger - Analytics |
| `SAP_FIN_BC_GL_PER_MGMT_PC` | General Ledger - Period Management |
| `SAP_FIN_BC_GL_JE_TEMP_PC` | General Ledger - Journal Entry Templates |
| `SAP_FIN_BC_GL_VAL_RESULT_PC` | General Ledger - Validation Results |
| `SAP_FIN_BC_GL_CONTROL_PC` | General Ledger - Control |
| `SAP_FIN_BC_FACT_GLACC_PC` | G/L Account Master Data |
| `SAP_FIN_BC_DSPL_ACDOC_PC` | Display Accounting Documents |
| `SAP_FIN_BC_ACC_RECON_PC` | Accounting Reconciliation |

### Bank Accounting — Core Catalogs

| Catalog ID | Title |
|---|---|
| `SAP_FIN_BC_BA_BANKSTAT_PC` | Bank Accounting - Bank Statement |
| `SAP_FIN_BC_BA_BANKSTRP_PC` | Bank Accounting - Bank Statement Reprocessing |
| `SAP_FIN_BC_BA_BSM_JOB_PC` | Bank Accounting - Application Job for Bank Statement Monitor |
| `SAP_FIN_BC_BA_LOCKBOX_PC` | Bank Accounting - Lockbox |
| `SAP_FIN_BC_BA_CHECK_DEP_PC` | Bank Accounting - Check Deposit |
| `SAP_FIN_BC_BA_CHAINS_PC` | Bank Accounting - Bank Chains |
| `SAP_FIN_BC_BA_PAYREQPRC_PC` | Bank Accounting - Payment Request Processing |

---

## Key Apps by Process

### AP — Invoice & Payment Flow

| App ID | T-Code | Description | Read-Only |
|---|---|---|---|
| `F0859_TRAN` | F0859 | Create Supplier Invoice | No |
| `F0859_77_TRAN` | F0859 | Park Supplier Invoice | No |
| `F3041_TRAN` | F3041 | Import Supplier Invoices | No |
| `F3041_77_TRAN` | F3041 | Import Supplier Invoices (Park) | No |
| `F1060_TRAN` | — | Supplier Invoices List | No |
| `F0593A_TRAN` | F0593A | Manage Payment Blocks | No |
| `F0770_TRAN` | F0770 | Manage Automatic Payments | No |
| `F0771_TRAN` | F0771 | Revise Payment Proposals | No |
| `F0771_AI_TRAN` | F0771 | Revise Payment Proposals (Analyze Exceptions) | No |
| `F0673A_TRAN` | F0673A | Approve Bank Payments | No |
| `F1367_TRAN` | — | Clear Outgoing Payments | No |
| `F0743_TRAN` | F0743 | Create Single Payment | No |
| `F0712_TRAN` | F0712 | Manage Supplier Line Items | No |
| `F0712_03_TRAN` | F0712 | Manage Supplier Line Items (Display) | Yes |
| `F0701A_TRAN` | F0701A | Display Supplier Balances | Yes |
| `F2257_TRAN` | — | Schedule Accounts Payable Jobs | No |

### AR — Invoice & Payment Flow

| App ID | T-Code | Description | Read-Only |
|---|---|---|---|
| `FB70_TRAN` | FB70 | Post Customer Invoice | No |
| `F1345_TRAN` | F1345 | Post Incoming Payments | No |
| `F0773_TRAN` | F0773 | Clear Incoming Payments | No |
| `F2223_TRAN` | — | Reset Cleared Items | No |
| `F0711_TRAN` | F0711 | Manage Customer Line Items | No |
| `F0711_03_TRAN` | F0711 | Manage Customer Line Items (Display) | Yes |
| `F0703A_TRAN` | F0703A | Display Customer Balances | Yes |
| `F0702A_TRAN` | F0702A | Manage Dispute Cases | No |
| `F0380_TRAN` | F0380 | Process Collections Worklist | No |
| `F150_TRAN` | F150 | Create Dunning Notice | No |
| `F3242_TRAN` | — | Accounts Receivable Overview | No |
| `F3246_TRAN` | — | Doubtful Accounts Valuation | No |
| `FBR2_AR_TRAN` | FBR2 | Reference Document for AR | No |

### GL — Journal Entry Flow

| App ID | T-Code | Description | Read-Only |
|---|---|---|---|
| `F0717A_TRAN` | F0717A | Manage Journal Entries | No |
| `F0717A_03_TRAN` | F0717A | Display Journal Entries | Yes |
| `F0717A_85_TRAN` | F0717A | Reverse Journal Entries | No |
| `F0718_TRAN` | F0718 | Post General Journal Entries | No |
| `F0956_TRAN` | — | Journal Entry Analyzer | Yes |
| `F0956B_TRAN` | — | Journal Entry Analyzer (New) | Yes |
| `F2130_TRAN` | — | Edit Options for Journal Entries | No |
| `F0996_TRAN` | — | Trial Balance | Yes |
| `F0708_TRAN` | F0708 | Balance Sheet/Income Statement | No |
| `F0731A_TRAN` | F0731A | Manage G/L Account Master Data | No |
| `F0731A_03_TRAN` | F0731A | Display G/L Account Master Data | Yes |
| `F0763A_TRAN` | F0763A | Manage Chart of Accounts | No |
| `F2293_TRAN` | — | Manage Posting Periods | No |
| `F3026_TRAN` | — | Renumber G/L Accounts | No |
| `FBCJ_TRAN` | FBCJ | Cash Journal | No |
| `F3302_TRAN` | — | Reconcile GR/IR Accounts | No |

### BA — Bank Statement & Payment

| App ID | T-Code | Description | Read-Only |
|---|---|---|---|
| `FEB_BSPROC_TRAN` | — | Bank Statement Processing | No |
| `FEBA_CHECK_DEPOSIT_TRAN` | — | Check Deposit | No |
| `FEBA_LOCKBOX_TRAN` | — | Lockbox | No |
| `FF68_TRAN` | FF68 | Manual Bank Statement | No |
| `FF_5_TRAN` | FF_5 | Account Statement Display | Yes |
| `FLB2_TRAN` | FLB2 | Post Lockbox Data | No |
| `F8381_TRAN` | — | Bank Statement Monitor | No |
| `F8382_TRAN` | — | Reprocess Bank Statement Items | No |

---

## Core Authorization Objects

### F_BKPF_BUK — Document: Company Code Authorization
Controls FI document posting by company code.

| Field | Key Values |
|---|---|
| `ACTVT` | `01`=Create, `02`=Change, `03`=Display |
| `BUKRS` | Company Code (`*` = all) |

### F_BKPF_BLA — Document: Document Type Authorization
Controls posting by document type (e.g. `KR`=vendor invoice, `DZ`=customer payment, `SA`=GL posting).

| Field | Key Values |
|---|---|
| `ACTVT` | `01`, `02`, `03` |
| `BLART` | Document type key |

### F_BKPF_KOA — Document: Account Type Authorization
Controls posting by account type.

| Field | Key Values |
|---|---|
| `ACTVT` | `01`, `02`, `03` |
| `KOART` | `D`=Customer, `K`=Vendor, `S`=GL, `A`=Asset, `M`=Material |

### F_BKPF_BEK — Document: Posting Key Authorization
Controls by posting key (debit/credit indicators).

### F_BKPF_BES — Document: Special G/L Indicator
Controls special G/L transactions (down payments, guarantees).

### F_BKPF_GSB — Document: Business Area
Restricts posting by business area.

### F_LFA1_BUK — Vendor Master: Company Code Data
Controls access to vendor master data at company code level.

| Field | Key Values |
|---|---|
| `ACTVT` | `01`=Create, `02`=Change, `03`=Display, `06`=Delete |
| `BUKRS` | Company Code |

### F_LFA1_GEN — Vendor Master: General Data
Controls access to vendor master general (cross-company) data.

| Field | Description |
|---|---|
| `ACTVT` | Activity |

### F_KNA1_BUK — Customer Master: Company Code Data
Controls customer master data at company code level.

| Field | Key Values |
|---|---|
| `ACTVT` | `01`, `02`, `03`, `06` |
| `BUKRS` | Company Code |

### F_KNA1_GEN — Customer Master: General Data
Controls access to customer master general data.

---

## SoD Concerns

Unlike Treasury (hard auth-object-level SoD), Finance AP/AR/GL SoD is primarily **catalog-level and process-level**. There are no T_DEAL_*-equivalent forbidden combinations. The key risks are:

### AP Payment 4-Eyes Principle

```
Risk: Same role can create invoices AND approve payments
```

| Step | App | Catalog | BRT |
|---|---|---|---|
| Create invoice | `F0859_TRAN` | `SAP_FIN_BC_AP_INVOICES_PC` | `SAP_BR_AP_ACCOUNTANT` |
| Manage payment run | `F0770_TRAN` | `SAP_FIN_BC_APAR_PAY_PC` | `SAP_BR_AP_ACCOUNTANT` |
| Approve bank payment | `F0673A_TRAN` | `SAP_FIN_BC_AP_PAY_APV_PC` | `SAP_BR_AP_MANAGER` |

**SoD rule:** `SAP_FIN_BC_AP_PAY_APV_PC` (payment approval) is in `SAP_BR_AP_MANAGER` only — not in `SAP_BR_AP_ACCOUNTANT`. The split between Accountant and Manager enforces 4-eyes on payment approval.

### AR Cash Application 4-Eyes Principle

```
Risk: Same role posts invoices AND clears/applies incoming payments
```

| Step | App | Catalog |
|---|---|---|
| Post customer invoice | `FB70_TRAN` | `SAP_FIN_BC_AR_INVOICE_PC` |
| Post incoming payment | `F1345_TRAN` | `SAP_FIN_BC_AR_INC_PAY_PC` |
| Clear open items | `F0773_TRAN` | `SAP_FIN_BC_AR_CLEARING_PC` |

Both catalogs are in `SAP_BR_AR_ACCOUNTANT` — this is a **known design decision** (AR Accountant needs the full process). Flag if a single user holds AR Accountant AND has unrestricted scope (`BUKRS = *`).

### GL Journal Entry Park & Post (2-Level Approval)

```
Risk: Same role can submit AND verify/post parked journal entries
```

| Step | App | Catalog |
|---|---|---|
| Submit for verification | `F0718_TRAN` (park) | `SAP_FIN_BC_GL_PARKDCPRE_PC` |
| Verify/post parked entry | Verify app | `SAP_FIN_BC_GL_PARKDCPST_PC` |

Both are in `SAP_BR_GL_ACCOUNTANT`. For customers requiring strict journal entry controls, these catalogs should be split across different users/roles.

---

## Workflow

### Step 1 — Identify the Package and App

```sql
SELECT PGMID, OBJECT, OBJ_NAME FROM TADIR
WHERE DEVCLASS = 'CLOUD_FI_AP_IAM' AND OBJECT = 'SIA6'
```

Get app text:
```sql
SELECT APP_ID, TEXT FROM APS_IAM_W_APPT
WHERE APP_ID = '<APP_ID>' AND LANGU = 'E'
```

Get app metadata:
```sql
SELECT APP_ID, TCODE, APP_TYPE, READ_ONLY, SCOPE_DEPENDENT FROM APS_IAM_W_APP
WHERE APP_ID = '<APP_ID>'
```

### Step 2 — Read Auth Object Instances

```sql
SELECT APP_ID, UUID, AUTH_OBJECT, STATUS, INACTIVE
FROM APS_IAM_W_APPAUI WHERE APP_ID = '<APP_ID>'
```

Active instances: `INACTIVE` = blank.

### Step 3 — Read Auth Values

```sql
SELECT UUID, PARENT_ID, FIELD, LOW_VALUE, HIGH_VALUE, STATUS
FROM APS_IAM_W_APPAUV WHERE APP_ID = '<APP_ID>'
```

Match `PARENT_ID` → UUID from Step 2.

### Step 4 — Check Catalog Assignment

```sql
SELECT BU_CATALOG_ID, APP_ID FROM APS_IAM_W_BC_APP WHERE APP_ID = '<APP_ID>'
```

Verify the catalog matches the expected one from the catalog tables above.

### Step 5 — Check BRT Coverage

```sql
SELECT BRT_ID, BU_CATALOG_ID FROM APS_IAM_W_BRTBUC WHERE BU_CATALOG_ID = '<CATALOG_ID>'
```

### Step 6 — Validate Authorization Setup

For each active auth object instance (INACTIVE = blank):
1. Collect all `(FIELD, LOW_VALUE)` pairs from APPAUV for that instance's UUID.
2. Confirm ACTVT values match the app's intended purpose.
   - Display-only apps (`READ_ONLY = X`): ACTVT should be `03` only (or `F4`).
   - Write apps: expect relevant create/change/delete activities, but not excessive.
3. Confirm scope fields (`BUKRS`, `BLART`, `KOART`) are correctly set.
4. Flag unexpected activities (e.g., ACTVT `01`/`02` on a read-only app).

**Example violation output:**
```
App: F0701A_TRAN  Expected: display (ACTVT 03)
AUTH_OBJECT  UUID  FIELD  LOW_VALUE  Issue
F_BKPF_BUK   ...   ACTVT  01         Unexpected Create on display-only app
```

### Step 7 — Full IAM Health Check (optional)

Run Steps 1–6 plus:
- Check `APS_IAM_W_APPAUO` for auth objects explicitly excluded/overridden
- Check `APS_IAM_W_APPDEP` for navigation dependencies
- Check `APS_IAM_W_APPSRV` for linked OData services

```sql
SELECT APP_ID, AUTH_OBJECT, STATUS FROM APS_IAM_W_APPAUO WHERE APP_ID = '<APP_ID>'
```

```sql
SELECT APP_ID, DEP_APP_ID, DEP_TYPE FROM APS_IAM_W_APPDEP WHERE APP_ID = '<APP_ID>'
```

---

## Quick Reference: ACTVT Values

| ACTVT | Meaning |
|---|---|
| `01` | Create |
| `02` | Change |
| `03` | Display |
| `06` | Delete |
| `07` | Activate/Deactivate |
| `08` | Display Change Documents |
| `16` | Execute |
| `22` | Assign |
| `31` | Approve |
| `43` | Release |
| `63` | Transport (change request context) |
| `85` | Reverse |
| `F4` | Value help (search help) |

## Quick Reference: Document Types (BLART) — Common in AP/AR/GL

| BLART | Description |
|---|---|
| `KR` | Vendor invoice |
| `KG` | Vendor credit memo |
| `KZ` | Vendor payment |
| `KA` | Vendor document |
| `DR` | Customer invoice |
| `DG` | Customer credit memo |
| `DZ` | Customer payment |
| `DA` | Customer document |
| `SA` | G/L account document |
| `AB` | Accounting document |

## Quick Reference: Account Types (KOART)

| KOART | Description |
|---|---|
| `D` | Customer (Debtor) |
| `K` | Vendor (Kreditor) |
| `S` | G/L Account |
| `A` | Asset |
| `M` | Material |
