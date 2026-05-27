# F9016 Authorization & Restriction-Type Review

**Date:** 2026-05-21
**Domain:** Cash Management
**Status:** Complete — review only, no remediation applied
**Scope:** All `F9016*` IAM apps in ER6 (matched: `F9016_TRAN` only)

## Summary

`F9016_TRAN` ("Schedule Jobs for Bank Account Interest Calculation", TCODE F9016) is the only F9016* app in ER6. It belongs to one Business Catalog (`SAP_FIN_BC_CM_BAI_PC` — Bank Account Interest Management) and is reachable from both `SAP_BR_CASH_MANAGER` and `SAP_BR_CASH_SPECIALIST`. Scope-dependent, not read-only. The auth profile contains 5 active auth objects; F_CLM_BAI grants full CRUD (ACTVT 01/02/03/06), which is broader than the app description ("Schedule Jobs") suggests and broader than its sibling display app `F9015_TRAN` (ACTVT 03/06).

## Findings

### App Master

| APP_ID | TCODE | Description | APP_TYPE | SCOPE_DEPENDENT | READ_ONLY |
|---|---|---|---|---|---|
| F9016_TRAN | F9016 | Schedule Jobs for Bank Account Interest Calculation | TRAN | X | (blank) |

### Catalog & Role Assignment

| Catalog | Title | BRTs |
|---|---|---|
| SAP_FIN_BC_CM_BAI_PC | Cash Management - Bank Account Interest Management | SAP_BR_CASH_MANAGER, SAP_BR_CASH_SPECIALIST |

### Authorization Objects (APS_IAM_W_APPAUI / APPAUV)

| Auth Object | Inst | UUID (suffix) | STATUS | ACTVT | Other Fields |
|---|---|---|---|---|---|
| F_BNKA_BUK | 0001 | …61934A | S | 03 | BUKRS=* |
| F_BNKA_MAO | 0001 | …61F34A | G | F4 | BBANKS=* |
| F_BUKRS_MD | 0001 | …62534A | S | F4 | BUKRS=* |
| F_CLM_BAI | 0001 | …62B34A | G | **01, 02, 03, 06** | BUKRS=*, FCLM_ACTY=* |
| F_CLM_BAM | 0001 | …63934A | G | 03, F4 | FCLM_BUKRS=*, FCLM_ACTY=*, FCLM_GSBER=*, FCLM_KOKRS=*, FCLM_PRCTR=*, FCLM_SGMT=* |

### Restriction Types (APS_IAM_W_APP_RT)

| RTYPE_ID | Description | R | W | F4 | Fields | Bound Auth Object(s) |
|---|---|---|---|---|---|---|
| BUKRS | Company Code | X |  |  | BUKRS | many (incl. F_BNKA_BUK, F_BUKRS_MD) |
| BBANKS | Bank Country/Region Key | X |  |  | BBANKS | F_BNKA_MAO |
| FCLM_BAM | Bank Account Management | X |  |  | FCLM_ACTY, BUKRS, PRCTR, SEGMENT | F_CLM_BAM |
| F_CLM_BAI | Bank Account Interest | X | X |  | BUKRS, FCLM_ACTY | F_CLM_BAI |

### Backing Services (APS_IAM_W_APPSRV)

- 1 transaction (F9016)
- 5 OData/HTTP services (3 active, 2 inactive)

### USOBT/USOBX

- USOBT: no proposed defaults for F9016
- USOBX: 1 row, OKFLAG = N (inherits)

## Anomalies

1. **F_CLM_BAI grants full CRUD on a job-scheduling app.** ACTVT = `{01, 02, 03, 06}` (Create / Change / Display / Delete). Sibling apps in the same catalog:
   - `F9015_TRAN` (Monitor): ACTVT `03, 06`
   - `F9017_TRAN` (Manage Conditions): ACTVT `03` on F_CLM_BAI (CRUD lives on F_CLM_BAIC)
   F9016 holding 01/02 on F_CLM_BAI lets a Cash Specialist create/modify interest records via the scheduling app — bypasses the boundary that F9017 enforces via F_CLM_BAIC.
2. **F_CLM_BAI restriction type is Read+Write (X/X)** — self-consistent with ACTVT 01/02 in the auth object, but the write surface deserves explicit business sign-off given the app description.
3. **Wildcards on all restriction fields** (BUKRS=*, FCLM_ACTY=*, BBANKS=*) — acceptable at the app level (BRT/role narrows scope) but BRT placement should be confirmed.
4. **Skill documentation drift** — `.claude/skills/cash-iam.md` Quick Start summary line states F9016 has ACTVT `03` on F_CLM_BAI; the detail table (and live ER6) shows `01, 02, 03, 06`. Detail table is correct; summary needs an update.
5. **No SoD violations** under documented Cash Management rules — F9016 is in BAI_PC only and doesn't co-exist with bank-account create/approve/reverse paths in the same app.

## Decisions

*(none — review only)*

## Work in Progress

*(none — review complete)*

## Known Good Baselines

- 1/1 F9016* apps reviewed; no SoD violations detected.
- ACTVT signature for F_CLM_BAI on F9016_TRAN: `{01, 02, 03, 06}` (live ER6 as of 2026-05-21).
- Catalog membership: `SAP_FIN_BC_CM_BAI_PC` only.
- BRT membership: `SAP_BR_CASH_MANAGER`, `SAP_BR_CASH_SPECIALIST`.

## Remediation Recommendations

1. Confirm with the Cash Management product team whether ACTVT 01/02 on `F_CLM_BAI` is intentional for `F9016_TRAN`. If not, restrict to `03, 06` (matching `F9015_TRAN`) and rely on `F9017_TRAN` for write access.
2. Update `.claude/skills/cash-iam.md` Quick Start summary to show F9016 ACTVT `01/02/03/06` (or post-remediation narrowed set).
3. If kept as-is, document rationale here so future scans don't flag drift.
4. No catalog or BRT changes recommended.

## Artifacts

*(none — all data sourced live from ER6 MCP queries; no intermediate files)*
