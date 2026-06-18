# IAM Multi-Hop Query Cookbook — CDS View Paths

**Date:** 2026-06-18
**Domain:** IAM (cross-cutting)
**Status:** Reference baseline — first cookbook entry, expand as new patterns are validated
**Scope:** Recipe for resolving multi-hop IAM questions (BRT → BC → App → AuthObject → AuthField → Activity) using the `SR_APS_IAM_*` CDS view layer instead of hand-written joins on `APS_IAM_W_*` tables. Validated end-to-end on `SAP_BR_CASH_MANAGER` (SIA1 catalogs).

## Summary

SAP IAM ships **1263 CDS views across 75 sub-packages** under `SR_APS_IAM_*` — they are the supported semantic layer over the raw `APS_IAM_W_*` tables and pre-join most multi-hop paths the assistant cares about. **Always prefer the CDS path over hand-written joins on raw tables**, with one important caveat: a few key views (`APS_IAM_BRT_APP`, `APS_IAM_INFO_BC_APP_BASIC`) hard-filter to `app_migration_status = '3'` (catalog migrated to IAM-Apps / SIA6). Treasury and Cash Management catalogs are still on **SIA1** today, so those views return empty for those BRTs — fall back to raw `APS_IAM_W_BC_APP` for the BC → App hop only. Activity values in `APS_IAM_AUTH_FIELD_VAL` are pre-translated (English text like "Display", "Display in Value Help", "Change", "Read", "Execute" — no `TACTT` join needed).

ADT Data Preview (the backend behind both `mcp__er6__query_sql` and sapcli) imposes **four hard SQL limitations** that force multi-hop questions to be staged: no JOIN, no subquery, no table aliases, and total SQL string length is bounded (long IN lists fail with "text literal longer than 255 characters" or "Literals across more than one line"). Each hop must therefore be its own query, with intermediate results filtered by `LIKE '<prefix>%'` or `BETWEEN '<lo>' AND '<hi>'` rather than long `IN (...)` lists.

## Findings

### The three high-value views

| CDS view | Pre-joins / replaces | Key columns | Caveats |
|---|---|---|---|
| `I_APS_BUSINESS_CATALOG` | `APS_IAM_W_BUC` (which is not directly queryable) plus 12 associations (`_App`, `_Successor`, `_RestrictionType`, `_BusinessRoleTemplate`, `_BusinessRoleAssignment`, `_Dependencies`, `_DependingOn`, …) | `BusinessCatalogID`, `Restrictable`, `IsDeprecated`, `Component`, `BusinessRoleAssignmentCount`, `BusinessCatalogSuccessorCount`, `IsMigrated` | Search-enabled; safe entry point |
| `APS_IAM_INFO_BRT_BC_BASIC` | `APS_IAM_W_BRTBUC` ⋈ `APS_IAM_W_BRT` ⋈ `APS_IAM_W_BRTT` ⋈ `APS_TADIR` | `TemplateID`, `BusinessCatalogID`, `BusinessCatalogText`, `BusinessCatalogComponent`, `TemplateName` | Hidden filter: `_TemplateScope.scope_state = '3'` OR `BRT.scope_dependent = ''`. Cash/Treasury main BRTs are covered; some country variants (`_ID`, `_KR`, `_PL`, `_TH`, …) have `scope_state = '1'` and are missing — fall back to raw `APS_IAM_W_BRTBUC` for those. |
| `APS_IAM_AUTH_FIELD_VAL` | `APS_IAM_W_APPAUI` ⋈ `APS_IAM_AUTHOBJ_FIELDS_ACT` ⋈ `aps_iam_auth_field_ddl` ⋈ `APS_IAM_W_APPAUV` ⋈ `TACTT` (translated) ⋈ `APS_IAM_W_RT_AO` | `AppId`, `AuthObject`, `AuvField`, `LowValue`, `HighValue`, `ActivityValue` (translated text), `Inactive`, `AppAuiStatus`, `rtype_id` | No scope filter — works for **all** apps (SIA1 + SIA6). Filter by `AppId`. |

### Routing rule for BRT → App

| Catalog state | Path |
|---|---|
| Migrated to IAM-Apps (SIA6) | `APS_IAM_BRT_APP` (one query, BRT → App with `BusinessCatalogID`, `AppType`, `ChipID`, app-type text) |
| Still on SIA1 (Cash, Treasury, most non-FIN areas today) | (a) BRT → BC via `APS_IAM_INFO_BRT_BC_BASIC` (or raw `APS_IAM_W_BRTBUC`); (b) BC → App via raw `APS_IAM_W_BC_APP` (or legacy `APS_IAM_W_BUCAPP`). The downstream App → Auth view (`APS_IAM_AUTH_FIELD_VAL`) is unaffected. |

How to tell ahead of time: query `APS_IAM_INFO_BC_APP_BASIC` for the catalog. Empty = SIA1, take the fallback. (Or check `aps_iam_bc_ddl.app_migration_status` directly: `'3'` = migrated; in ER6 today **all 1231 catalogs are status '3'**, but the SIA1 vs SIA6 distinction is enforced separately in `Document.scope = #aps_bc_scope_state.3`.)

### ADT Data Preview hard limitations (apply to MCP and sapcli paths)

The backend wraps every SELECT into an ABAP `SELECT … INTO TABLE @DATA(...)` block before executing it. Symptoms and workarounds:

| Limitation | Symptom (verbatim error) | Workaround |
|---|---|---|
| No `JOIN` | `Only one SELECT statement is allowed.` | Use CDS view associations (e.g. `I_APS_BUSINESS_CATALOG._App`) or split into multiple queries and combine in the application layer. |
| No subqueries | Same as JOIN, sometimes with `Unknown column name "<truncated>"` | Pull intermediate results, then issue a follow-up query with a tighter filter. |
| No table aliases (`AS x`) | Same as JOIN | Use the unqualified table/column name. |
| Total SQL string length bounded (~255 chars per literal) | `The text literal "..." is longer than 255 characters` or `Literals across more than one line are not allowed.` | Replace long `IN (...)` lists with `LIKE '<prefix>%'` or `BETWEEN '<lo>' AND '<hi>'`. As a rule of thumb keep IN-list literals under ~5–10 short entries. |

### Worked example: "Which apps does `SAP_BR_CASH_MANAGER` reach, and what activities does it grant?"

Cash Manager catalogs are SIA1, so we use the fallback path for hop 2. Three queries, no joins:

**Hop 1 — BRT → BC** (12 rows: `SAP_FIN_BC_CM_*`, `SAP_CMD_BC_*`, `SAP_MM_BC_*_DSP_PC`, `SAP_SD_BC_*_DISPL_PC`, `SAP_FIN_BC_DSPL_ACDOC_PC`, `SAP_FIN_BC_FACT_BAM_PC`):
```sql
SELECT BusinessCatalogID
FROM APS_IAM_INFO_BRT_BC_BASIC
WHERE TemplateID = 'SAP_BR_CASH_MANAGER'
ORDER BY BusinessCatalogID
```

**Hop 2 — BC → App** (per catalog, raw fallback because SIA1):
```sql
SELECT DISTINCT APP_ID
FROM APS_IAM_W_BC_APP
WHERE BU_CATALOG_ID = 'SAP_FIN_BC_CM_OPS_BASIC_PC'
  AND APP_ID <> ''
ORDER BY APP_ID
```

**Hop 3 — App → AuthObject + Activity** (one query per app, or use a `LIKE '<prefix>%'` filter to span related apps):
```sql
SELECT AppId, AuthObject, AuvField, LowValue, HighValue, ActivityValue
FROM APS_IAM_AUTH_FIELD_VAL
WHERE AppId = 'F0735_TRAN'
ORDER BY AuthObject, AuvField, LowValue
```

For aggregating activity counts across many apps, replace the long `IN (...)` with a range or prefix filter:
```sql
SELECT AppId, ActivityValue, COUNT( * ) AS CNT
FROM APS_IAM_AUTH_FIELD_VAL
WHERE AuvField = 'ACTVT'
  AND AppId BETWEEN 'F0' AND 'FZZZ'
  AND AppId LIKE '%_TRAN'
GROUP BY AppId, ActivityValue
ORDER BY AppId, ActivityValue
```

### CDS view naming convention (VDM)

| Prefix | Layer | Example |
|---|---|---|
| `I_` | Interface (reuse entry point) | `I_APS_BUSINESS_CATALOG`, `I_APS_IAM_APP_CORE` |
| `C_` | Consumption (OData/Fiori) | `C_APS_IAM_BR`, `C_APS_BUSINESS_CATALOG` |
| `R_` | Restricted / value-help | `R_APS_IAM_APP_TIL` |
| `P_` | Private / technical | `P_APS_IAM_APP` |
| `D_` | RAP draft | `D_APS_IAM_BUSR_RAP_*` |
| `APS_IAM_*_DDL`, `APS_IAM_*_BASIC` | Pre-VDM legacy | `APS_IAM_BR_DDL`, `APS_IAM_BRT_DDL`, `APS_IAM_INFO_*_BASIC` |

### High-value packages to browse (`mcp__er6__list_package`)

- `SR_APS_IAM_BUSINESS_CATALOG` (14) — BC-centric views
- `SR_APS_IAM_BRT_ODATA` (11) — BRT relationships (BRT→APP/BC/BR/Spaces)
- `SR_APS_IAM_BROLE_D_ODATA` (89) — Business role views with cross-table joins
- `SR_APS_IAM_APP_CORE` (36) — App-centric (App↔BC/BR/AuthObject/RestrictionType)
- `SR_APS_IAM_INFO` (102) and `SR_APS_IAM_INFO_RAP` (71) — aggregation views

## Decisions

1. **Phase-1 KG materialisation plan is withdrawn.** SAP already shipped the semantic layer as 1263 CDS views; further materialisation would duplicate work without adding capability. The remaining gap is *routing* (which CDS view for which question), not *materialising* anything new.
2. **CDS-first, raw-table fallback only when CDS hard-filters out the data we need** (the SIA1 vs SIA6 case for the BC → App hop today). Other hops always go through CDS.
3. **Multi-hop questions are staged, not joined.** ADT Data Preview's hard limits make this non-negotiable on the query side; the CDS associations carry the relational structure that JOIN would otherwise express.

## Work in Progress

*(none — cookbook seeded; expand on next multi-hop question.)*

## Known Good Baselines

- `SAP_BR_CASH_MANAGER` reaches 12 Business Catalogs via `APS_IAM_INFO_BRT_BC_BASIC` (live ER6, 2026-06-18).
- `SAP_FIN_BC_CM_OPS_BASIC_PC` exposes 38 distinct apps via raw `APS_IAM_W_BC_APP` (live ER6, 2026-06-18) — `APS_IAM_INFO_BC_APP_BASIC` returns 0 for the same catalog because of its `Document.scope = #aps_bc_scope_state.3` filter.
- `APS_IAM_AUTH_FIELD_VAL` returns translated activity text directly (no `TACTT` join needed): "Display", "Display in Value Help", "Change", "Read", "Execute", "Create or generate", "Delete", …
- ER6 today: all 1231 entries in `aps_iam_bc_ddl` have `app_migration_status = '3'`. Despite this, SIA1 catalogs are still gated out of `APS_IAM_INFO_BC_APP_BASIC` via the separate `Document.scope = #aps_bc_scope_state.3` filter — i.e. `app_migration_status` is *not* the SIA1/SIA6 discriminator, the view's `scope` enum is.

## Remediation Recommendations

1. When adding a new multi-hop question to the assistant, search this memo and `CLAUDE.md` "Recommended CDS Views" first; only fall back to raw `APS_IAM_W_*` joins when a CDS view is verified to hard-filter out the data.
2. When a new CDS-vs-raw routing decision is made (e.g. for a hop not yet covered here), append a row to the relevant table above.
3. If a Cash/Treasury catalog migrates from SIA1 to SIA6, revisit hop 2 — at that point `APS_IAM_BRT_APP` becomes the one-shot path and the fallback can be retired.

## Artifacts

- `CLAUDE.md` updated in three places: (a) ADT Data Preview limitations subsection in `Key Notes`; (b) `APS_IAM_W_BUC` entry now points to `I_APS_BUSINESS_CATALOG`; (c) new `## Recommended CDS Views` chapter (high-value views table, SIA1/SIA6 routing, VDM naming, package list). All decisions in this memo are reflected there.
- `scripts/sapwiki.py` — Confluence wiki fetcher used to verify SAP has no published IAM knowledge-graph project that this assistant should align with.
- `docs/iam-wiki.md`, `docs/wiki-authz-s4hana-cloud.md` — wiki content snapshots that informed the "no upstream KG, use the CDS layer instead" decision.
