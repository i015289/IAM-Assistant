# IAM Health Check — `SAP_FIN_BC_TRM_TMPL_PC`

**Title:** TRM - Financial Transaction Templates with Easy Entry
**Date:** 2026-05-27
**Status:** Completed
**Domain:** Treasury IAM (FOE-only consumption)

## Scope

Full IAM health check on Business Catalog `SAP_FIN_BC_TRM_TMPL_PC` covering: header, app inventory, BRT consumers, restriction-type coverage, app-level RT gaps, auth object instances, dependencies, service binding, and Treasury SoD posture.

## Summary

The catalog is **FOE-clean** at the SoD level, and previously-flagged FOE violations on both apps have been **remediated** since the 2026-05-22 scan (TRFCT and ACTVT wildcards have been replaced with bounded discrete values). The catalog has no app or catalog dependencies and no successor relationships. However, **non-trivial restriction-type coverage gaps** remain between catalog-declared RTs and what each app actually exposes. One field-level data anomaly worth confirming: `ACC_CODE_VAL_AREA_GSART` is declared write-only at the catalog level (no read access).

## Health Findings

### CRITICAL — None
No SoD violations (FOE matrix); no missing required auth objects on FOE-relevant scope.

### WARNING

#### W1. Restriction-type coverage gaps (app vs catalog)

Catalog declares 5 RTs. App-level coverage:

| Catalog RT (declared) | F9023_TRAN | FTTM_AI_CREATE_TRAN |
|---|---|---|
| `ACC_CODE_VAL_AREA_GSART` (W) | ✗ MISSING | R only — direction mismatch |
| `BUKRS_BUPLA` (R+W) | ✗ MISSING | R+W ✓ |
| `BUKRS_GSART_SFHAART` (R+W) | R+W ✓ | R only — missing W |
| `BUKRS_RLDEPO` (R+W) | R+W ✓ | ✗ MISSING |
| `RLTYP` (R+W) | ✗ MISSING | R+W ✓ |

`F9023_TRAN` exposes only 2 of 5 catalog RTs; `FTTM_AI_CREATE_TRAN` exposes 4 of 5 with two access-flag mismatches. Either tighten the catalog RT declarations to match real app needs, or extend each app's RT coverage. Mismatches reduce IAM scope-restriction effectiveness for end users.

#### W2. Catalog-level RT direction anomaly

`ACC_CODE_VAL_AREA_GSART` is declared with `WRITE_ACCESS=X` but `READ_ACCESS=blank` at the catalog level. Unusual for a template catalog where users typically read before writing. Confirm whether this is intentional (write-only restriction).

### INFO

#### I1. SoD remediation since 2026-05-22 baseline

Prior memo `treasury-sod-scan.md` flagged FOE violations on both apps using wildcard TRFCT/ACTVT. Live state today:

| App | Prior (2026-05-22) | Now (2026-05-27) |
|---|---|---|
| F9023_TRAN T_DEAL_PD …11F2CA | TRFCT=`*`, ACTVT=`*` (D3×01, D3×85, D2×AB) | TRFCT={D1,D2}, ACTVT={01,02,03,06} — clean |
| FTTM_AI_CREATE_TRAN T_DEAL_PD …98F2CA | TRFCT=`*`, ACTVT=01 (D3×01) | TRFCT={D1,D2}, ACTVT={01} — clean |

Both apps are now FOE-compliant under the forbidden matrix `(D3∧ACTVT∈{01,85}) ∨ (D2∧ACTVT=AB)`. Update the SoD baseline memo to reflect remediation.

#### I2. Service binding asymmetry

`F9023_TRAN` has both an HTTP service (CDF65064E670234B89286A79929342, active) and a TRAN service (F9023, active). `FTTM_AI_CREATE_TRAN` is TRAN-only (FTTM_AI_CREATE) — no HT/OData service registered. May be intentional if the AI prompt UI is delivered via a different mechanism; verify with the app owner.

#### I3. BC_APP `ACTIVE` and `RELEASE_STATUS` blank

Both rows in `APS_IAM_W_BC_APP` have blank `ACTIVE` and `RELEASE_STATUS`. Apps still resolve through the catalog, but the lifecycle metadata is empty. May be normal for this delivery class — flag for confirmation.

## Catalog Footprint

```
SAP_FIN_BC_TRM_TMPL_PC
├─ Apps (2)
│  ├─ F9023_TRAN              → Manage Templates for Financial Transactions (TCODE F9023)
│  └─ FTTM_AI_CREATE_TRAN     → Create Financial Transaction with AI Prompt (TCODE FTTM_AI_CREATE)
│
├─ Catalog RTs (5)            BUKRS_BUPLA, BUKRS_GSART_SFHAART, BUKRS_RLDEPO,
│                             RLTYP, ACC_CODE_VAL_AREA_GSART
│
├─ Consumed by BRTs (1)       SAP_BR_TREASURY_SPECIALIST_FOE  ← FOE-only
│
├─ Dependencies               none (APPDEP and BUCDEP empty)
└─ Successors / predecessors  none
```

## Auth Object Map

| App | Auth Object | UUID (last 8) | TRFCT | ACTVT | SoD verdict |
|---|---|---|---|---|---|
| F9023_TRAN | T_DEAL_DP | DC1152CA | D1, D2 | 01, 02, 03, 06 | FOE-clean |
| F9023_TRAN | T_DEAL_PD | DC11F2CA | D1, D2 | 01, 02, 03, 06 | FOE-clean |
| FTTM_AI_CREATE_TRAN | B_BUPA_CRS | 1F9752CA | — | — | n/a |
| FTTM_AI_CREATE_TRAN | B_BUPA_RLT | 1F9792CA | — | — | n/a |
| FTTM_AI_CREATE_TRAN | F_BUK_BUPL | 1F9812CA | — | — | n/a |
| FTTM_AI_CREATE_TRAN | F_T_TRANSB | 1F98B2CA | — | — | n/a |
| FTTM_AI_CREATE_TRAN | T_DEAL_PD | 1F98F2CA | D1, D2 | 01 | FOE-clean |
| FTTM_AI_CREATE_TRAN | T_POS_ASS | 1F99B2CA | * | — | TRFCT not SoD-relevant on T_POS_ASS |

## Recommendations

1. **Resolve W1** — decide between (a) trimming catalog RT declarations to match real app coverage, or (b) extending each app's RT coverage. Current asymmetry weakens scope-restriction guarantees in the FOE BRT.
2. **Confirm W2** — verify `ACC_CODE_VAL_AREA_GSART` is intentionally write-only at catalog level.
3. **Update [[treasury-sod-scan]]** — F9023_TRAN and FTTM_AI_CREATE_TRAN are now FOE-clean. Remove from the active violations list and record the remediation date.
4. **Optional re-run** — re-scan all 4 prior FOE-violating apps in the 2026-05-22 memo (FTRTBG02_B_TRAN, FTRTLC02_B_TRAN) to see if remediation extends beyond this catalog.

## Steps Executed

1. ✓ Catalog header confirmed via APS_IAM_W_BUCATT (BUC not directly queryable per CLAUDE.md)
2. ✓ App inventory: 2 apps via APS_IAM_W_BC_APP + APS_IAM_W_APP + APS_IAM_W_APPT
3. ✓ BRT consumers: 1 (FOE only) via APS_IAM_W_BRTBUC
4. ✓ Catalog RTs: 5 declared via APS_IAM_W_BUC_RT + APS_IAM_W_RT_T
5. ✓ App RT gaps: 5 mismatches identified via APS_IAM_W_APP_RT
6. ✓ Auth object coverage: 8 instances (2 + 6) via APS_IAM_W_APPAUI/APPAUO/APPAUV
7. ✓ Dependencies: none via APS_IAM_W_APPDEP and APS_IAM_W_BUCDEP (BU_CAB/BUCALT are not successor maps — CLAUDE.md schema note flagged)
8. ✓ Service bindings: HT+TRAN on F9023, TRAN-only on FTTM_AI_CREATE via APS_IAM_W_APPSRV
9. ✓ FOE SoD scan: no violations against `(D3∧ACTVT∈{01,85}) ∨ (D2∧ACTVT=AB)`
10. ✓ Memo written

## Related

- [[treasury-sod-scan]] — needs update to reflect remediation
- [[f9016-auth-review]] — sibling app-level review pattern
