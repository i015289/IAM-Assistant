# Treasury SoD Compliance Scan

**Date:** 2026-05-20
**Domain:** Treasury
**Status:** Complete

## Findings

Scanned 270 T_DEAL_PD apps (full TRFCT+ACTVT coverage, 3,875 ACTVT rows) and 16 T_TOE_HR apps (22 unique UUIDs).
Applied corrected scope: T_DEAL_PD against FOE+BOE; T_TOE_HR against MOE/Accountant only (FOE/BOE explicitly out of scope).

**6 UUID-level violations across 5 apps in 4 catalogs:**

### T_DEAL_PD violations (4)

| App | Office | Catalog | UUID (suffix) | TRFCT | ACTVT | Rule hit |
|---|---|---|---|---|---|---|
| F9023_TRAN | FOE | SAP_FIN_BC_TRM_TMPL_PC | …DC11F2CA | [D1,D2,D3] | `*` | (D3,01), (D3,85), (D2,AB) |
| FTTM_AI_CREATE_TRAN | FOE | SAP_FIN_BC_TRM_TMPL_PC | …1F98F2CA | [D1,D2,D3] | [01] | (D3,01) |
| FTRTBG02_B_TRAN | BOE | SAP_FIN_BC_TRM_FTTFCP_2_PC | …37BE0292 | [D1,D2,D3] | [02,03,PR] | (D2,02) |
| FTRTLC02_B_TRAN | BOE | SAP_FIN_BC_TRM_FTTFCP_2_PC | …DC272292 | [D2,D3] | [02,PR] | (D2,02) |

### T_TOE_HR violations (2 — both on TOEHREQO_TA_TRAN, MOE+ACC dual-classified)

| UUID (suffix) | HREQ_CAT | ACTVT | Rule hit |
|---|---|---|---|
| …200520E8 | [A,D] | [43,85] | MOE: A/D × 43/85 |
| …200620E8 | [A,D,G,S,T,X] | [02,03,06,43,85,94] | MOE: A/D × 43/85; ACC: A/D × 02/06 |

## Decisions

- **Rule scope corrections applied this session:**
  - FOE T_DEAL_PD forbidden = `{(D2,AB), (D3,01), (D3,85)}` — D2+01 is allowed for FOE (creating contracts on the front office is permitted).
  - T_TOE_HR is evaluated only for MOE and Accountant; FOE/BOE are out of scope.
- Updated `.claude/skills/treasury-iam.md` Quick Start table and Hedge Request Management section to reflect MOE/Accountant-only scope.

## Work in Progress

*(none — scan complete)*

## Known Good Baselines

- 270/270 T_DEAL_PD apps have full ACTVT coverage in `/tmp/actvt_master.tsv`.
- 264/270 T_DEAL_PD apps are SoD-clean under the corrected FOE/BOE matrix.
- 15/16 T_TOE_HR apps are SoD-clean under the MOE/Accountant matrix; only `TOEHREQO_TA_TRAN` is in scope and violating.
- `TOEHREQO_TRAN` (FOE-only catalog) is no longer flagged — correctly excluded under updated skill scope.

## Remediation Recommendations

1. **F9023_TRAN** — wildcard ACTVT `*` is overly permissive on a FOE template; restrict to creation activities and exclude AB on D2 plus 01/85 on D3.
2. **FTTM_AI_CREATE_TRAN** — drop D3 from TRFCT or remove ACTVT 01 (settlement-create belongs in BOE).
3. **FTRTBG02_B_TRAN / FTRTLC02_B_TRAN** — strip D2 from these BOE apps (contract editing is a FOE responsibility).
4. **TOEHREQO_TA_TRAN** — root cause is dual classification (assigned to both `SAP_FIN_BC_HEDGE_MGT_PC` MOE and `SAP_FIN_BC_HM_HR_ACCT_PC` Accountant). Either split into two app variants or tighten UUID …200620E8 (currently 6 HREQ_CAT × 6 ACTVT — near-wildcard).

## Artifacts

- `/tmp/sod_final_report.json` — full violation report (note: `T_TOE_HR rules apply only to MOE and Accountant; FOE/BOE out of scope`)
- `/tmp/sod_tdeal_violations.json` — T_DEAL_PD violations
- `/tmp/sod_thr_moe_acc_violations.json` — T_TOE_HR MOE/Accountant violations
- `/tmp/actvt_master.tsv` — 3,875-row ACTVT master, 100% coverage of 270 T_DEAL_PD apps
- `/tmp/sod_master.json` — population master (270 tdeal apps, 16 thedge apps)
- `/tmp/sod_app_brts.json` — app → office (FOE/BOE/MOE/ACC/RSK) classification
- `/tmp/sod_thedge_data.json` — T_TOE_HR per-UUID HREQ_CAT + ACTVT
