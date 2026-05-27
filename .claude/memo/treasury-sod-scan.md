# Treasury SoD Compliance Scan

**Date:** 2026-05-20 (revised: 2026-05-22, updated: 2026-05-22)
**Domain:** Treasury
**Status:** Complete — full per-instance re-scan 2026-05-22: 4 violations across 3 apps (FTRTLC04 cleared)

## Findings

Scanned 270 T_DEAL_PD apps and 16 T_TOE_HR apps (25 instances).
Applied corrected scope: T_DEAL_PD against FOE+BOE; T_TOE_HR against MOE/Accountant only (FOE/BOE explicitly out of scope).

**4 UUID-level violations across 3 apps in 2 catalogs** *(revised 2026-05-22 — see Baseline Correction below)*:

### T_DEAL_PD violations (2)

| App | Office | Catalog | UUID (suffix) | TRFCT | ACTVT | Rule hit |
|---|---|---|---|---|---|---|
| F9023_TRAN | FOE | SAP_FIN_BC_TRM_TMPL_PC | …DC11F2CA | `*` | `*` | (D3,01), (D3,85), (D2,AB) |
| FTTM_AI_CREATE_TRAN | FOE | SAP_FIN_BC_TRM_TMPL_PC | …1F98F2CA | `*` | [01] | (D3,01) |

### T_TOE_HR violations (2 — both on TOEHREQO_TA_TRAN, MOE+ACC dual-classified)

| UUID (suffix) | HREQ_CAT | ACTVT | Rule hit |
|---|---|---|---|
| …200520E8 | [A,D] | [43,85] | MOE: A/D × 43/85 |
| …200620E8 | [A,D,G,S,T,X] | [02,03,06,43,85,94] | MOE: A/D × 43/85; ACC: A/D × 02/06 |

## Re-run Summary (2026-05-22 — Full Per-Instance Scan)

Full autonomous Hermes re-scan (8-step plan) executed against live ER6 data using strict per-instance methodology throughout. Population: 270 T_DEAL_PD apps (238 TRFCT candidate UUIDs across 213 apps), 16 T_TOE_HR apps (23 instances).

**Methodology:** All TRFCT candidate UUIDs cross-referenced with their ACTVT values at PARENT_ID level. App-level office classification verified via APS_IAM_W_BC_APP catalog lookup and BRT assignment. No union-of-app-level evaluation used.

**T_DEAL_PD analysis:** 137 per-instance hits before office filtering. After applying FOE/BOE rules per-instance and confirming ACTVT on each wildcard-TRFCT UUID:
- F6157_F/B, FTRTLC00_F/B, TM00_F/B — wildcard TRFCT but ACTVT=03/F4 only → CLEAN
- FWUP, FWKS, TPM series, F498x Alert series — ACTVT=03/F4 on T_DEAL_PD wildcard UUIDs → CLEAN
- All numeric F-series (F0735, F1754-F4984 etc.) — non-TRM catalogs or ACTVT=03 only → CLEAN/out of scope
- **FTRTLC04_TRAN:** Only 1 active T_DEAL_PD instance (UUID `…DB0292`); TRFCT=`*`, ACTVT=AB only. BOE rule is D2×02 — no ACTVT=02 present → **CLEAN**. (UUID `…DFDDC292` with ACTVT=02 seen in APPAUV belongs to a different auth object, not T_DEAL_PD; `…DFDBC292` is INACTIVE=X.)

**T_TOE_HR analysis:** All 16 apps checked per-instance. TPITRO/TX02_F/TX02_B/TX10/TI4B/TOENE_03/TOESNAPO_03 → FOE/BOE scope → out of scope. TOENE/TOESNAPO/TPM100-104 → MOE/ACC scope → all CLEAN. Only TOEHREQO_TA_TRAN has violations (unchanged from baseline).

**Result: 4 violations across 3 apps — identical to the revised baseline. No new violations found.**

| App | Office | Auth Object | UUID (suffix) | Key Fields | Rule |
|---|---|---|---|---|---|
| F9023_TRAN | FOE | T_DEAL_PD | …DC11F2CA | TRFCT=`*`, ACTVT=`*` | D3×01, D3×85, D2×AB |
| FTTM_AI_CREATE_TRAN | FOE | T_DEAL_PD | …1F98F2CA | TRFCT=`*`, ACTVT=01 | D3×01 |
| TOEHREQO_TA_TRAN | MOE+ACC | T_TOE_HR | …200520E8 | HREQ_CAT={A,D}, ACTVT={43,85} | MOE: A/D×43/85 |
| TOEHREQO_TA_TRAN | MOE+ACC | T_TOE_HR | …200620E8 | HREQ_CAT={A,D,G,S,T,X}, ACTVT={02,03,06,43,85,94} | MOE: A/D×43/85; ACC: A/D×02/06 |

## Baseline Correction (2026-05-22)

Per-instance re-check of FTRTBG02_B_TRAN and FTRTLC02_B_TRAN revealed that D2 (TRFCT) and ACTVT=02 never appear on the **same** auth object instance UUID in either app:

| App | UUID | TRFCT | ACTVT | Verdict |
|---|---|---|---|---|
| FTRTBG02_B_TRAN | …37BD4292 | 04, D3 | 02 | D3 only — no D2 |
| FTRTBG02_B_TRAN | …37BE0292 | D1, D2, D3 | 03, PR | No ACTVT=02 |
| FTRTLC02_B_TRAN | …DC266292 | 04, D3 | 02 | D3 only — no D2 |
| FTRTLC02_B_TRAN | …DC272292 | D2, D3 | 03, PR | No ACTVT=02 |

Prior scans flagged these by evaluating TRFCT and ACTVT at the app level (union across all instances). Correct evaluation is **per instance UUID**. Both apps are clean under the strict per-instance rule.

**Baseline revised: 4 violations across 3 apps in 2 catalogs (was 6 across 5 apps in 4 catalogs).**

## Decisions

- **Rule scope corrections applied this session:**
  - FOE T_DEAL_PD forbidden = `{(D2,AB), (D3,01), (D3,85)}` — D2+01 is allowed for FOE (creating contracts on the front office is permitted).
  - T_TOE_HR is evaluated only for MOE and Accountant; FOE/BOE are out of scope.
- Updated `.claude/skills/treasury-iam.md` Quick Start table and Hedge Request Management section to reflect MOE/Accountant-only scope.

## Re-run Summary (2026-05-20)

Re-scan executed against live ER6 data. All 270 T_DEAL_PD app UUIDs and 16 T_TOE_HR app UUIDs re-checked.
**Result: 0 new violations, 0 remediated — all 6 UUID-level violations from original scan persist unchanged.**

## Re-run Summary (2026-05-21 — run 1)

Targeted re-scan of the 5 baseline violator apps via ER6 MCP.
- T_DEAL_PD population unchanged (270 apps); T_TOE_HR population unchanged (16 apps).
- All 6 baseline UUIDs still present with identical TRFCT/ACTVT (or HREQ_CAT/ACTVT) signatures.
- Catalog assignments for violator apps unchanged.
**Result: 0 delta vs. 2026-05-20. Same 6 UUID-level violations across 5 apps in 4 catalogs.**

## Re-run Summary (2026-05-21 — run 2)

Full re-scan via ER6 MCP. Population confirmed: 270 T_DEAL_PD apps, 16 T_TOE_HR apps.
All 5 violating apps re-queried with live APPAUV data:
- F9023_TRAN: wildcard TRFCT+ACTVT on UUID …DC11F2CA — unchanged
- FTTM_AI_CREATE_TRAN: TRFCT=*, ACTVT=01 on UUID …1F98F2CA — unchanged
- FTRTBG02_B_TRAN: D2+02 on UUID …37BE0292 — unchanged
- FTRTLC02_B_TRAN: D2+02 on UUID …DC272292 — unchanged
- TOEHREQO_TA_TRAN: UUIDs …200520E8 and …200620E8 — unchanged
**Result: 0 delta vs. all prior runs. All 6 UUID-level violations persist across 5 apps in 4 catalogs.**

## Work in Progress

*(none — scan complete)*

## Known Good Baselines

- 270/270 T_DEAL_PD apps scanned; 267/270 clean under the corrected FOE/BOE per-instance matrix.
- 15/16 T_TOE_HR apps are SoD-clean under the MOE/Accountant matrix; only `TOEHREQO_TA_TRAN` is in scope and violating.
- `TOEHREQO_TRAN` (FOE-only catalog) correctly excluded under updated skill scope.
- **FTRTBG02_B_TRAN and FTRTLC02_B_TRAN confirmed clean** — D2 and ACTVT=02 are on separate instances, never co-resident.
- **F6157_F/B, FTRTLC00_F/B, TM00_F/B, FTRTLC04_TRAN confirmed clean** — wildcard TRFCT with ACTVT=03/F4/AB only; no D2×02 or D3×{01,85} on any active instance.

## Remediation Recommendations

1. **F9023_TRAN** — wildcard ACTVT `*` is overly permissive on a FOE template; restrict to creation activities and exclude AB on D2 plus 01/85 on D3.
2. **FTTM_AI_CREATE_TRAN** — drop D3 from TRFCT or remove ACTVT 01 (settlement-create belongs in BOE).
3. **TOEHREQO_TA_TRAN** — root cause is dual classification (assigned to both `SAP_FIN_BC_HEDGE_MGT_PC` MOE and `SAP_FIN_BC_HM_HR_ACCT_PC` Accountant). Either split into two app variants or tighten UUID …200620E8 (currently 6 HREQ_CAT × 6 ACTVT — near-wildcard).

## Re-run Summary (2026-05-22)

Full re-scan via ER6 MCP. Population confirmed: 270 T_DEAL_PD apps, 16 T_TOE_HR apps (25 instances).

**T_DEAL_PD deep scan methodology note:** The ACTVT bulk query (FIELD='ACTVT', rows=5000) hits the row cap and truncates before reaching later apps alphabetically. For this run, the 4 known violators were verified directly per-app, and a cross-reference of TRFCT (full dataset, 2090 rows) × forbidden ACTVT identified 19 candidate apps with apparent D2×02 hits. All 19 were investigated:
- FOE-catalog apps (_F_TRAN, FTOPCP_1, FT_FX_F, etc.): D2×02 is not a FOE-forbidden combination → correctly excluded.
- BOE-catalog apps (TM32_B, TM42_B, TM_62_B, TRTM_CHG_PARTNER_B, TS02_B, TX02_B, F9430_B): D2 TRFCT values confirmed to belong to INACTIVE instances (INACTIVE=X in APPAUI). Active APPAUI instances for these apps carry D3-only TRFCT with ACTVT=02 → no BOE violation on active auth.

All 5 baseline violating apps re-queried with live APPAUV data — unchanged.
**Result: 0 delta vs. all prior runs. Same 6 UUID-level violations across 5 apps in 4 catalogs.**

## Artifacts

- `/tmp/sod_rerun_report.json` — re-run violation report (2026-05-20), confirms 0 delta vs prior scan
- `/tmp/sod_tdeal_violations.json` — T_DEAL_PD violations
- `/tmp/sod_thr_moe_acc_violations.json` — T_TOE_HR MOE/Accountant violations
- `/tmp/actvt_master.tsv` — 3,875-row ACTVT master, 100% coverage of 270 T_DEAL_PD apps
- `/tmp/sod_master.json` — population master (270 tdeal apps, 16 thedge apps)
- `/tmp/sod_app_brts.json` — app → office (FOE/BOE/MOE/ACC/RSK) classification
- `/tmp/sod_thedge_data.json` — T_TOE_HR per-UUID HREQ_CAT + ACTVT
