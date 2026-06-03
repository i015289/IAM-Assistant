# Treasury IAM Skill Enhancement — Design

**Date:** 2026-06-03
**Scope:** `/Users/I015289/Joule_Workspace/iam-assistant/.claude/skills/treasury-iam.md` (single-file rewrite)
**Goal:** Enhance the Treasury IAM skill from ~300 lines (focused on T_DEAL_* / T_TOE_HR SoD only) to a more complete operational manual covering business context, the full set of authorization objects encountered in Treasury IAM apps, complex audit scenarios, and troubleshooting techniques. Backed by live ER6 data already gathered.

## Rationale

The current skill is a precise but narrow SoD validator: T_DEAL_PD/PF/DP/AG and T_TOE_HR matrices, with one workflow for "is this app FOE or BOE?". Real Treasury IAM work involves more:

- **Other auth objects** that show up in Treasury apps (T_DEAL_LC, T_BP_DEAL, T_POS_ASS, T_DEPOT, T_STAM_GAT, F_T_VTBLV, F_T_TRANSB, plus FI-cross-cutting like F_BKPF_BUK and F_INFO_BUK) are silent — the skill never explains them.
- **Business context** (Treasury overview, FOE/MOE/BOE responsibilities, why SoD here) is missing — non-Treasury staff who get tasked with audits have to look elsewhere first.
- **Multi-app audit scenarios** (a whole BRT, country variants, migration before/after diff) aren't covered — only single-app validation.
- **Troubleshooting** (false-positive patterns, performance pitfalls, reverse SQL → SoD inference) is not addressed.

Live ER6 data (gathered 2026-06-03 from `APS_IAM_W_APPAUI` filtered to FTR/TM/TS app prefixes, `INACTIVE = ''`) confirms the broader auth-object footprint: **at least 30 distinct auth objects** appear in active Treasury IAM app instances. The skill should at minimum acknowledge them, classify them (SoD-relevant vs scoping vs unrelated), and tell readers when each one matters.

## Target structure (final state)

The enhanced skill keeps the existing front matter and example prompt library intact, restructures the body into a hierarchical reference manual, and adds three new top-level sections. Approximate target length: 600–700 lines (still single-file; not split — these things change together and Claude reads them as one unit).

```
# Treasury IAM Skill
  --- (preamble unchanged: package, MCP, SQL caveats) ---

## Example Prompts                          (kept as-is)
## Quick Start                              (kept; cross-refs updated)

## Business Context                         [NEW]
  ### What Treasury IAM covers
  ### Front Office vs Middle Office vs Back Office
  ### Why SoD matters in Treasury
  ### Country variants and split derivation

## FOE vs BOE                               (kept)

## Authorization Objects Reference          [EXPANDED]
  ### T_DEAL_* family (SoD-critical)        (kept core; expanded with T_DEAL_LC, T_BP_DEAL)
  ### Position management                   [NEW] T_POS_ASS, T_TEX_POS, T_TEX_REXP
  ### Hedge accounting                      [NEW] T_TOE_HR (move detail here), T_HREL_AUT
  ### External securities & gateways        [NEW] T_EXT_SEC, T_STAM_GAT, T_DEPOT, T_ASGTTMPL
  ### Valuation                             [NEW] F_T_VTBLV, F_T_NPV
  ### Trading & settlement                  [NEW] F_T_TRANSB, FW_BES_BUK
  ### Cross-cutting FI                      [NEW] F_BUKRS_MD, F_BKPF_*, F_INFO_BUK, F_BUK_BUPL, F_FAGL_*, F_BNKA_BUK, F_SKA1_BUK
  ### Business partner                      [NEW] B_BUPA_CRS / RLT / RAT / GRP, B_BUPR_BZT
  ### Customer & vendor master              [NEW] F_KNA1_*, V_KNA1_VKO, F_LFA1_*
  ### Cash management overlap               [NEW] F_CLM_BAM
  ### Cost & profit centers                 [NEW] K_CSKS, K_CCA, K_PCA, K_PCA_MD, K_REPO_CCA
  ### Project structure                     [NEW] /S4PPM/PR1, C_PRPS_ART, C_PRPS_KST, C_PRPS_VNR
  ### Generic / utility                     [NEW] S_TABU_NAM, S_APPL_LOG, S_SCD0_OBJ
  ### Custom namespace notes                [NEW] /TMF/SHAEX

## ACTVT / TRFCT Values                     (kept; consolidated)
## Forbidden Combinations                   (kept; small wording fixes)
## TRFCT Patterns in Existing Apps          (kept)
## Business Role Templates                  (kept; cross-referenced from Business Context)

## Workflows                                [REORG]
  ### Single-app SoD validation             (kept as Steps 1–6)
  ### Catalog FOE/BOE split analysis        [NEW WORKFLOW]
  ### Whole-BRT audit                       [NEW WORKFLOW]
  ### Cross-company-code violation scan     [NEW WORKFLOW]
  ### Pre/post-migration diff               [NEW WORKFLOW]
  ### Hedge request SoD                     (kept; move to be a sibling workflow)
  ### Reverse inference: SQL → SoD          [NEW WORKFLOW]

## Troubleshooting & Validation Tips        [NEW]
  ### Common false positives
  ### Inactive vs Copied vs Status
  ### Performance pitfalls (UP TO N + WHERE; row caps)
  ### When the matrix says "violation" but it isn't
  ### Verifying your conclusion by reverse-querying

## Appendix: Live ER6 evidence (2026-06-03)  [NEW]
  ### Distinct AUTH_OBJECTs in active Treasury app instances
  ### Sample query reproducing this list
```

## Section-by-section design

### Business Context (NEW)

200–300 words. No queries — pure orientation:

- Treasury manages cash, FX, money market, derivatives, securities. The IAM package `CLOUD_FI_TR_IAM` partitions apps along the trade lifecycle.
- FOE = origination (D1/D2 — orders and contracts). BOE = back-office (D3 — settlement and accounting). MOE = middle-office (risk, exposure, hedge accounting). Accountant = financial postings of treasury results.
- Why SoD: a single user able to BOTH originate a trade AND settle it can disguise unauthorized trades or money laundering. Industry rule: front-office traders never settle their own deals.
- Country variants (`_CN`, `_SG`, `_TH`, `_BR`) inherit the same SoD model from the global BRT but typically tighten company-code scoping (via `BUKRS` field on `T_DEAL_*`).

This section grounds the rest. Anyone reading the skill should be able to skip from here straight to "Forbidden Combinations" without backtracking.

### Authorization Objects Reference (EXPANDED)

The current single table for T_DEAL_* fans out into 14 sub-sections. Each sub-section has the same shape:

```
### <Group name>
**Objects:** T_X, T_Y
**Shared fields:** ACTVT, BUKRS, ...
**SoD relevance:** Yes / Indirect / No
**Common in apps:** F*, T*, FTRCAI*, ...
**Notes:** <one-paragraph operational guidance — what to verify, what to ignore>
```

For SoD-relevant objects (T_DEAL_*, T_TOE_HR, T_DEAL_LC for "limit check"), point to the matrix sections.

For *indirect* SoD objects (T_BP_DEAL, T_POS_ASS, T_HREL_AUT) — explain what they govern (business-partner-deal binding, position assignments, hedge relationship maintenance) and **when** they become SoD-relevant (e.g., "T_BP_DEAL gives the user counterparty selection power; combined with T_DEAL_PD D2/01 this enables a trader to create a contract for any counterparty without back-office review").

For *unrelated-to-SoD* objects (S_TABU_NAM, S_APPL_LOG, F_FAGL_*) — say so plainly, with one sentence on what the object actually checks. This prevents readers from spending audit effort on irrelevant objects.

### Workflows (REORG, several NEW)

Existing 6-step single-app flow becomes the first workflow and is preserved verbatim. Five new workflows added:

1. **Catalog FOE/BOE split analysis** — formalize Step 5 of the existing flow into a standalone repeatable procedure (input: catalog ID; output: FOE-set, BOE-set, split-or-not decision, naming).
2. **Whole-BRT audit** — given a BRT, walk every catalog → every app → every active T_DEAL_* / T_TOE_HR pair and report all violations.
3. **Cross-company-code violation scan** — find apps where a single user could combine FOE+BOE activities ACROSS company codes (often missed by per-app SoD scans).
4. **Pre/post-migration diff** — given two snapshots (e.g., before and after a transport), enumerate auth-value diffs that change SoD posture for any app.
5. **Reverse inference: SQL → SoD** — start from a real ER6 query result (e.g., "I see TRFCT=D2 ACTVT=AB on this app — should I worry?") and walk backward to the matrix to answer.

Hedge SoD section remains as a sibling workflow, not a separate top-level chapter — it's the same shape of question.

Each workflow has:
- One-line intent
- Inputs / outputs
- 3–6 numbered steps with concrete SQL using existing tables (`APS_IAM_W_BRTBUC`, `APS_IAM_W_BC_APP`, `APS_IAM_W_APPAUI`, `APS_IAM_W_APPAUV`)
- A "report shape" example

No SQL beyond `SELECT … FROM <single table> WHERE …` — same dialect rules already in the skill.

### Troubleshooting & Validation Tips (NEW)

About 200 lines. Distilled from common pitfalls in this codebase:

- **Inactive vs Copied vs Status** — the meaning of `INACTIVE`, `COPIED`, and `STATUS` fields in `APS_IAM_W_APPAUI`/`APPAUV`. `INACTIVE = 'X'` means inactive; `STATUS = 'M'` (manual) vs `'S'` (supplied) vs `'D'` (deleted) — gotcha for naive analysts.
- **Apps with no auth instances** — read-only Fiori apps that delegate auth to backend service objects; not a violation, just a different model.
- **Cartesian explosion** — when an instance has many TRFCT and many ACTVT values, the cross-product can flag "violations" that the runtime never actually allows because of additional fields (BUKRS, RFART, etc.).
- **Cloud-only T_DEAL_AG** — the skill already notes this; reinforce with a "what to do when you see it anyway" rule.
- **Performance** — `mcp__er6__query_sql` rejects `UP TO N ROWS` inline with a `WHERE` clause; use the `rows` parameter. Don't add JOINs (ABAP Open SQL forbids them in this dialect).
- **Reverse verification** — after concluding "App X violates BOE", run the actual TRFCT/ACTVT lookup in `APS_IAM_W_APPAUV` directly so you can show the auditor the row that triggered it.

### Appendix: Live ER6 evidence (NEW)

A small, concrete table of auth objects observed today in Treasury IAM apps, with the exact reproducing query so a future reader can refresh it. This anchors the skill in reality and lets a reviewer challenge the auth-object reference if the situation changes.

The table is short — names + a count or category, no values.

## Verification

Acceptance criteria after the rewrite:

1. The skill front matter (`name`, `description` block) is unchanged.
2. The Example Prompt Library is preserved verbatim (it's referenced by the welcome cards in the UI).
3. Every section that exists today still exists and has at least the same content (no regression).
4. Auth Objects Reference covers the 30+ objects observed in live ER6 data (organized by category).
5. At least 4 new workflows present (catalog split, whole-BRT, cross-BUKRS, pre/post diff, reverse inference — pick at least 4).
6. Troubleshooting section present with at least 5 distinct pitfalls.
7. Appendix has a SQL block that, run today, would reproduce the underlying observation.
8. Skill is still a single file under `.claude/skills/treasury-iam.md`.
9. Total length 600–800 lines (vs current ~300). Not a hard cap; structure matters more than length.

## Out of scope

- Splitting the skill into multiple files (the existing single-file pattern is fine for a few hundred lines).
- Updating `cash-iam.md` to follow the same structure (separate effort if desired).
- Updating UI prompt cards (already covers the user-visible Treasury prompts).
- Generating any code or non-skill artifacts.
- Asking the AI to invent new SoD rules — the rules in the skill are operational truth; we only describe them clearly.
