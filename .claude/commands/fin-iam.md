
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

