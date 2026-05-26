# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

IAM (Identity & Access Management) analysis assistant that queries the SAP ABAP system **ER6** to analyze authorizations, roles, packages, transactions, and related IAM data.

## Memo System

At the start of every session, read `.claude/memo/INDEX.md`. If any memos have `Status: In Progress`, surface them to the user:

> Found in-progress memo: **[title]** — last updated YYYY-MM-DD. Load it to resume?

Use `/memo` (see `.claude/skills/memo.md`) to save, load, update, and manage persistent memos across sessions. Memos store: IAM findings, decisions with rationale, work in progress, and known-good baselines.

## Running Queries Against ER6

**Always prefer the `er6` MCP tools over Bash/sapcli for ER6 queries.** The MCP server is the default and recommended way to access ER6.

### Available MCP Tools (preferred)

| Tool | Purpose |
|------|---------|
| `mcp__er6__query_sql` | Run ABAP Open SQL SELECT statements |
| `mcp__er6__read_table_def` | Read DDIC table/structure definitions |
| `mcp__er6__read_cds_view` | Read CDS view (DDLS) source |
| `mcp__er6__read_class` | Read ABAP class source |
| `mcp__er6__read_program` | Read ABAP program/report source |
| `mcp__er6__list_package` | List objects in an ABAP package |

### Bash/sapcli Fallback (only if MCP tool is insufficient)

1. Activate the connection environment:
   ```bash
   source .sapcli.env
   ```

2. Run a query:
   ```bash
   conda run -n sapcli-env sapcli datapreview osql "SELECT * FROM TABLE_NAME UP TO 10 ROWS"
   ```

### Key Notes

- SQL dialect is **ABAP Open SQL** — use the `rows` parameter on `mcp__er6__query_sql` for row limits (not `TOP` or `FETCH FIRST`)
- **Do NOT use `UP TO N ROWS` inline when a `WHERE` clause is present** — the ER6 backend rejects this combination. Always pass `rows` as a separate parameter instead.
- `UP TO N ROWS` without a `WHERE` clause is accepted inline (e.g. `SELECT ... FROM TABLE UP TO 10 ROWS`) but using the `rows` parameter is always safe and preferred.
- Output from sapcli is `|`-separated, similar to CSV with a header row
- Authentication: username/password (`ANZEIGER`/`display`), read-only access, SSL enabled

## Data Dictionary

### TDEVC — ABAP Packages
- `DEVCLASS`: Package name (PK)
- `PACKTYPE`: `C`=Cloud, `D`=Deactivated, `H`=Home, `O`=On-Premise, `F`=Future Cloud

### TADIR — ABAP Object Registry
- `OBJ_NAME`: Object name
- `OBJECT`: Object type
- `PGMID`: Program ID

### USOBT / USOBX — Authorization Defaults
Maps T-Codes to required Authorization Objects.
- `USOBX`: Whether a check is active
- `USOBT`: Proposed values (the "Variant")
- `NAME`: Transaction code, `OBJECT`: Authorization Object, `TYPE`: Object type

### USOBHASH — Authorization Defaults Hash Keys
- `NAME`: Hash key, `TYPE`: Auth object type
- `OBJ_NAME`, `OBJECT`, `PGMID`: same as TADIR

### TSTCV — Transaction Variants
Maps T-Codes to visual/functional variants.
- `TCODE`: Base transaction, `VARIANT`: Variant name

### T001 — Company Codes

### SUI_TM_MM_APP — Fiori Launchpad App-to-Catalog Assignment
Maps apps to their technical catalog(s). **Note:** For Treasury apps (FTR*, TM*, TS* prefixes), APP_ID values in this table are stored as GUIDs, not SIA6 names — use `APS_IAM_W_BC_APP` or `APS_IAM_W_BUCAPP` instead for business catalog lookups by app name.
- `APP_ID`: App identifier (GUID format for Treasury apps; SIA6 name for others)
- `CAT_ID`: Catalog identifier (FK to SUI_TM_MM_CAT)

### SUI_TM_MM_CAT — Launchpad Technical Catalog
Master list of Fiori Launchpad technical catalogs.
- `CAT_ID`: Catalog identifier (PK, e.g. `SAP_TC_FIN_TRM_COMMON`)
- `TITLE`: Human-readable catalog title

### APS_IAM_W_ACS — IAM Access Control Sets
Master table of named Access Control Sets (ACS).
- `ACS_ID`: Access Control Set identifier (PK)
- `DESCRIPTION`: Human-readable description
- `CREATE_USER` / `CHANGE_USER`: Audit users
- `CREATE_TIMESTAMP` / `CHANGE_TIMESTAMP`: Audit timestamps

### APS_IAM_W_ACSR — IAM Access Control Set Roles
Maps Access Control Sets to roles.
- `ACS_ROLE_ID`: Role identifier within the ACS (PK)
- `ACS_ID`: FK to APS_IAM_W_ACS
- `ACS_ROLE_TYPE`: Type of role assignment
- `CREATE_USER` / `CHANGE_USER`: Audit users
- `CREATE_TIMESTAMP` / `CHANGE_TIMESTAMP`: Audit timestamps

### APS_IAM_W_APP — IAM App Registry
Master table of IAM-managed apps (SIA6 objects).
- `APP_ID`: App identifier (PK, e.g. `F1443A_TRAN`)
- `APP_TYPE`: Type of app (e.g. `TRAN` for transaction-based)
- `TCODE`: Linked SAP transaction code
- `READ_ONLY`: Whether the app is read-only
- `SCOPE_DEPENDENT`: Whether app is scope-dependent
- `EXCLUDE_START_AUTH`: Whether start authorization check is excluded
- `FORBID_USE_WITH_SUCCESSOR`: Whether app is forbidden when a successor exists
- `NO_DIRECT_ASSIGNMENT`: Whether app cannot be directly assigned to users
- `RTYPE_MIG_STATUS`: Restriction type migration status
- `REL_FOR_CUST_CAT_EXT`: Whether app is released for customer catalog extensions
- `CREATE_USER` / `CHANGE_USER`: Responsible users
- `CREATE_TIMESTAMP` / `CHANGE_TIMESTAMP`: Audit timestamps

### APS_IAM_W_APP_RT — IAM App Restriction Types
Maps apps to restriction types and their access permissions.
- `APP_ID`: App identifier (FK to APS_IAM_W_APP)
- `RESTRICTION_TYPE_ID`: Restriction type (FK to APS_IAM_W_RT)
- `READ_ACCESS` / `WRITE_ACCESS` / `F4_ACCESS`: Access flags (X = granted)
- `INACTIVE`: Whether this restriction is inactive
- `READ_ACCESS_STATUS` / `WRITE_ACCESS_STATUS` / `F4_ACCESS_STATUS`: Status of each access type

### APS_IAM_W_APPAUI — IAM App Authorization Object Instances
Detailed authorization object instances per app, with UUID-based hierarchy.
- `APP_ID`: App identifier
- `UUID`: Unique ID of this instance
- `AUTH_OBJECT`: Authorization object
- `AUTH_OBJECT_INST_ID`: Instance ID
- `STATUS`: Status flag
- `IBS_SOURCE`, `IBS_SOURCE_TYPE`: Source tracing fields
- `INACTIVE`, `COPIED`: State flags

### APS_IAM_W_APPAUO — IAM App Authorization Objects (Outbound)
Maps apps to authorization objects that must NOT be checked (exclusions/overrides).
- `APP_ID`: App identifier
- `AUTH_OBJECT`: Authorization object (e.g. `S_TABU_NAM`, `B_BUP_DCPD`)
- `STATUS`: Status flag (e.g. `S`)

### APS_IAM_W_APPAUV — IAM App Authorization Values
Field-level authorization values for each auth object instance.
- `APP_ID`: App identifier
- `UUID`: This value record's UUID
- `PARENT_ID`: UUID of the parent auth object instance (links to APS_IAM_W_APPAUI)
- `FIELD`: Authorization field name (e.g. `ACTVT`)
- `LOW_VALUE` / `HIGH_VALUE`: Value range
- `STATUS`: Status flag
- `COPIED`: Whether value was copied

### APS_IAM_W_APPDEP — IAM App Dependencies
Defines dependencies between apps (e.g. navigation targets).
- `APP_ID`: Source app identifier
- `DEP_APP_ID`: Dependent/required app identifier
- `DEP_TYPE`: Dependency type (e.g. `2` = navigation dependency)
- `NAVIGATION_TARGET`: Optional explicit navigation target

### APS_IAM_W_APPSRV — IAM App Services
Maps apps to their OData/HTTP services.
- `APP_ID`: App identifier
- `SRVC_NAME`: Service name
- `SRVC_TYPE`: Service type (e.g. `HT` = HTTP/OData)
- `ACTIVE`: Whether the service is active (X = yes)
- `UIAD_SRC`: UI adaptation source

### APS_IAM_W_APPT — IAM App Texts
Human-readable descriptions for apps.
- `APP_ID`: App identifier (FK to APS_IAM_W_APP)
- `TEXT`: Display text / description
- `LANGU`: Language key

### APS_IAM_W_AU — IAM Authorization Objects Registry
Master registry of authorization objects used in IAM.
- `AUTH_OBJECT_ID`: Authorization object identifier (PK, may differ from `AUTH_OBJECT` in case of aliases)
- `AUTH_OBJECT`: SAP authorization object name
- `ACTIVITY_FIELD`: Activity field name (e.g. `ACTVT`)
- `BADI_IMPLEMENTED`: Whether a BAdI is implemented
- `ACCESS_CAT_RELEVANCE`: Access category relevance flag
- `CREATE_USER` / `CHANGE_USER`: Audit users
- `CREATE_TIMESTAMP` / `CHANGE_TIMESTAMP`: Audit timestamps

### APS_IAM_W_AUACTM — IAM Auth Object Activity Mapping
Maps authorization objects to activities and their access categories.
- `AUTH_OBJECT_ID`: Auth object identifier (FK to APS_IAM_W_AU)
- `ACTIVITY`: Activity value (e.g. `03` for display)
- `ACCESS_CATEGORY`: Access category (`R`=Read, `W`=Write, `F`=F4/search help)

### APS_IAM_W_BC_APP — Business Catalog App Content
Defines which apps (including folders and structure tiles) belong to a Business Catalog, with placement details.
- `BU_CATALOG_ID`: Business Catalog identifier (FK to APS_IAM_W_BUC)
- `OBJECT_ID`: Object identifier within the catalog (padded numeric string)
- `PARENT_ID`: Parent object ID for hierarchical structure
- `APP_ID`: App identifier (FK to APS_IAM_W_APP)
- `SORT_ORDER`: Sort order within the catalog
- `IS_FOLDER`: Whether this entry is a folder
- `ACTIVE`: Whether the entry is active
- `RELEASE_STATUS`: Release/deployment status

### APS_IAM_W_BC_APT — Business Catalog App Content Texts
Texts for catalog content items (folders, group headers).
- `BU_CATALOG_ID`: Business Catalog identifier
- `LANGU`: Language key
- `OBJECT_ID`: Object identifier (FK to APS_IAM_W_BC_APP)
- `TEXT`: Display text

### APS_IAM_W_BCAPPS — Business Catalog App Assignments (Legacy)
Tracks app-to-catalog assignments including change type and chip ID.
- `BU_CATALOG_APP_ID`: Assignment identifier (PK)
- `BU_CATALOG_ID`: Business Catalog identifier
- `APP_ID`: App identifier
- `ROLE_CHANGE` / `CATALOG_CHANGE` / `GROUP_CHANGE`: Change type flags (`A`=Added)
- `CHIP_ID`: Launchpad chip/tile ID
- `CREATE_USER` / `CHANGE_USER`: Audit users
- `CREATE_TIMESTAMP` / `CHANGE_TIMESTAMP`: Audit timestamps

### APS_IAM_W_BCRTFM — Business Catalog to Business Role Template Field Mapping
Maps restriction type fields from a Business Catalog perspective.
- `BU_CATALOG_ID`: Business Catalog identifier
- `RTYPE_ID`: Restriction type identifier
- `FIELD_NAME`: Field name within the restriction type
- `AUTH_OBJECT`: Related authorization object
- `PFCG_FIELD_NAME`: Corresponding PFCG (role maintenance) field name

### APS_IAM_W_BRT — Business Role Templates
Master table of Business Role Templates (BRT), which are the IAM equivalent of PFCG composite roles.
- `BRT_ID`: Business Role Template identifier (PK, e.g. `SAP_BR_GL_ACCOUNTANT`)
- `SCOPE_DEPENDENT`: Whether the role is scope-dependent (X = yes)
- `FIORI_SPACE_ID`: Default Fiori space assigned to the role
- `CREATE_USER` / `CHANGE_USER`: Audit users
- `CREATE_TIMESTAMP` / `CHANGE_TIMESTAMP`: Audit timestamps

### APS_IAM_W_BRT_FS — Business Role Template Fiori Space Assignments
Maps Business Role Templates to their Fiori spaces/pages.
- `BRT_FIORI_SPACE_ID`: Assignment identifier (PK)
- `BRT_ID`: Business Role Template identifier (FK to APS_IAM_W_BRT)
- `FIORI_SPACE_ID`: Fiori space/page identifier
- `CREATE_USER` / `CHANGE_USER`: Audit users
- `CREATE_TIMESTAMP` / `CHANGE_TIMESTAMP`: Audit timestamps

### APS_IAM_W_BRTBUC — Business Role Template to Business Catalog Assignments
Maps Business Role Templates to Business Catalogs.
- `BRT_BU_CATALOG_ID`: Assignment identifier (PK)
- `BRT_ID`: Business Role Template identifier (FK to APS_IAM_W_BRT)
- `BU_CATALOG_ID`: Business Catalog identifier (FK to APS_IAM_W_BUC)
- `CREATE_USER` / `CHANGE_USER`: Audit users
- `CREATE_TIMESTAMP` / `CHANGE_TIMESTAMP`: Audit timestamps

### APS_IAM_W_BRTT — Business Role Template Texts
Human-readable names for Business Role Templates.
- `LANGU`: Language key
- `BRT_ID`: Business Role Template identifier (FK to APS_IAM_W_BRT)
- `TEXT`: Display name (e.g. `General Ledger Accountant`)

### APS_IAM_W_BU_CAB — Business Catalog Successor (Alternate) Mapping
Maps deprecated/alternate Business Catalog + App combinations to their successor.
- `BU_CATALOG_ID`: Source Business Catalog identifier
- `APP_ID`: Source App identifier
- `BU_CATALOG_ID_SUCCR`: Successor Business Catalog identifier
- `APP_ID_SUCCR`: Successor App identifier

### APS_IAM_W_BU_CAT — Business Catalog Release Notes / Long Texts
Stores release notes and long-text descriptions for Business Catalogs.
- `BU_CATALOG_ID`: Business Catalog identifier
- `LANGU`: Language key
- `LONG_TEXT`: Long text / release notes content

### APS_IAM_W_BUC_RT — Business Catalog Restriction Types
Maps Business Catalogs to their applicable restriction types and access permissions.
- `RESTRICTION_TYPE_ID`: Restriction type identifier
- `BU_CATALOG_ID`: Business Catalog identifier
- `READ_ACCESS` / `WRITE_ACCESS` / `F4_ACCESS`: Access flags
- `INACTIVE`: Whether this mapping is inactive
- `READ_ACCESS_STATUS` / `WRITE_ACCESS_STATUS` / `F4_ACCESS_STATUS`: Status of each access type

### APS_IAM_W_BUCALT — Business Catalog Predecessors (Alternatives)
Records predecessor/alternative catalog relationships for migration.
- `BU_CATALOG_ID`: Current catalog identifier
- `APP_ID`: Current app identifier
- `BU_CATALOG_ID_SUCCR`: Predecessor catalog identifier
- `APP_ID_SUCCR`: Predecessor app identifier

### APS_IAM_W_BUCAPP — Business Catalog Apps (Structured)
Core assignment table mapping apps into Business Catalogs with role/catalog/group change tracking.
- `BU_CATALOG_APP_ID`: Assignment identifier (PK)
- `BU_CATALOG_ID`: Business Catalog identifier
- `APP_ID`: App identifier
- `ROLE_CHANGE` / `CATALOG_CHANGE` / `GROUP_CHANGE`: Change flags
- `CHIP_ID`: Launchpad chip/tile ID
- `CREATE_USER` / `CHANGE_USER`: Audit users
- `CREATE_TIMESTAMP` / `CHANGE_TIMESTAMP`: Audit timestamps

### APS_IAM_W_BUCATT — Business Catalog Attributes / Texts
Short text descriptions and attributes for Business Catalogs.
- `LANGU`: Language key
- `BU_CATALOG_ID`: Business Catalog identifier (FK to APS_IAM_W_BUC)
- `TEXT`: Short display text / title

### APS_IAM_W_BUCDEP — Business Catalog Dependencies
Defines dependencies between Business Catalogs (e.g. prerequisite catalogs).
- `BU_CATALOG_ID`: Source Business Catalog identifier
- `DEP_BU_CATALOG_ID`: Dependent/required Business Catalog identifier
- `DEP_TYPE`: Dependency type (e.g. `2`=navigation, `3`=technical)

### APS_IAM_W_FLD — IAM Restriction Type Fields
Defines fields used in restriction types (the atomic units of scope restrictions).
- `FIELD_NAME`: Field name (PK, e.g. `BUKRS`, `WERKS`)
- `PFCG_FIELD_NAME`: Mapped PFCG field name used in role maintenance
- `IS_RANGE_SUPPORTED`: Whether range values are supported (X = yes)
- `CREATE_USER` / `CHANGE_USER`: Audit users
- `CREATE_TIMESTAMP` / `CHANGE_TIMESTAMP`: Audit timestamps

### APS_IAM_W_FLD_T — IAM Restriction Type Field Texts
Human-readable labels for restriction type fields.
- `LANGU`: Language key
- `FIELD_NAME`: Field name (FK to APS_IAM_W_FLD)
- `TEXT`: Display label (e.g. `Company Code`, `Plant`)

### APS_IAM_W_FLDX — IAM Field Cross-Mapping
Maps IAM field names to alternative PFCG field names for cases where the mapping is not 1:1.
- `FIELD_NAME`: IAM field name
- `PFCG_FIELD_NAME`: Alternative PFCG field name

### APS_IAM_W_INFO — IAM System Information / Configuration
Stores system-level IAM configuration and metadata (key-value style).
- `ID`: Configuration key (PK)
- `CREATE_USER` / `CHANGE_USER`: Audit users
- `CREATE_TIMESTAMP` / `CHANGE_TIMESTAMP`: Audit timestamps

### APS_IAM_W_MCA — IAM Multi-Category Attribute Sets
Defines Multi-Category Attribute (MCA) sets — named groupings of restriction type fields.
- `ID`: MCA set identifier (PK)
- `CREATE_USER` / `CHANGE_USER`: Audit users
- `CREATE_TIMESTAMP` / `CHANGE_TIMESTAMP`: Audit timestamps

### APS_IAM_W_MCAP — IAM Multi-Category Attribute Set Fields
Maps fields to MCA sets.
- `ID`: MCA set identifier (FK to APS_IAM_W_MCA)
- `FIELD_NAME`: Field name (FK to APS_IAM_W_FLD)

### APS_IAM_W_MCAT — IAM Multi-Category Attribute Set Texts
Human-readable labels for MCA sets.
- `LANGU`: Language key
- `ID`: MCA set identifier (FK to APS_IAM_W_MCA)
- `TEXT`: Display label

### APS_IAM_W_RR — IAM Restriction Rules
Master table of restriction rules that constrain scope values.
- `RTYPE_ID`: Restriction type identifier (PK, e.g. `BUKRS`, `BUKRS_GLRLDNR_GLRRCTY_GLRVERS`)
- `CREATE_USER` / `CHANGE_USER`: Audit users
- `CREATE_TIMESTAMP` / `CHANGE_TIMESTAMP`: Audit timestamps
- `AGGREGATION_CATEGORY`: Whether the restriction aggregates multiple fields (`1` = composite)

### APS_IAM_W_RR_T — IAM Restriction Rule Texts
Human-readable labels for restriction rules/types.
- `LANGU`: Language key
- `ID`: Restriction rule/type identifier (FK to APS_IAM_W_RR)
- `TEXT`: Display label (e.g. `Company Code`, `Company Code/Ledger/Record Type/Version`)

### APS_IAM_W_RRFLD — IAM Restriction Rule Fields
Maps restriction rules to their constituent fields with sort order.
- `RTYPE_ID`: Restriction type identifier (FK to APS_IAM_W_RR)
- `FIELD_NAME`: Field name (FK to APS_IAM_W_FLD)
- `SORT_ORDER`: Display/processing order of this field within the restriction type

### APS_IAM_W_RT — IAM Restriction Types (Business Catalog level)
Defines restriction types available at the Business Catalog level (higher-level than APS_IAM_W_RR).
- `RESTRICTION_TYPE_ID`: Restriction type identifier (PK)
- `AUTH_OBJECT`: Associated authorization object
- `CREATE_USER` / `CHANGE_USER`: Audit users
- `CREATE_TIMESTAMP` / `CHANGE_TIMESTAMP`: Audit timestamps

### APS_IAM_W_RT_AO — IAM Restriction Type Auth Objects
Maps restriction types to the authorization objects they control.
- `RTYPE_ID`: Restriction type identifier
- `AUTH_OBJECT`: Authorization object name

### APS_IAM_W_RT_AOM — IAM Restriction Type Auth Object Field Mappings
Detailed field-level mapping between restriction types and auth object fields.
- `RTYPE_ID`: Restriction type identifier
- `FIELD_NAME`: IAM field name
- `AUTH_OBJECT_ID`: Authorization object identifier (FK to APS_IAM_W_AU)
- `PFCG_FIELD_NAME`: Corresponding PFCG field name in that auth object

### APS_IAM_W_RT_T — IAM Restriction Type Texts
Human-readable labels for restriction types.
- `LANGU`: Language key
- `ID`: Restriction type identifier
- `TEXT`: Display label

### APS_IAM_W_RTFLD — IAM Restriction Type to Field Assignments
Maps restriction types to their fields with sort ordering (similar to APS_IAM_W_RRFLD but at the catalog-restriction-type level).
- `RTYPE_ID`: Restriction type identifier
- `FIELD_NAME`: Field name
- `SORT_ORDER`: Display order of this field

### APS_IAM_W_TACT — IAM Activity Definitions
Defines standard SAP activities and their access categories used across authorization objects.
- `ACTIVITY`: Activity code (e.g. `01`=Create, `02`=Change, `03`=Display)
- `ACCESS_CATEGORY`: Access category (`R`=Read, `W`=Write, `F`=F4 value help)

### APS_IAM_W_USRATT — IAM User Attribute Types
Defines user attribute type codes and their associated attribute sets.
- `USER_CATEGORY_ID`: User category identifier
- `USER_ATTRIBUTE_TYPE`: Type of attribute (e.g. `DEVSUPPORT`, `DRAFTSHARE`, `MONITORING`)
- `USER_ATTRIBUTE_ID`: Attribute identifier

### APS_IAM_W_USRCAR — IAM User Category Role Assignments
Maps user categories to role patterns (PFCG or business roles) with relevance levels.
- `USER_CATEGORY_ID`: User category identifier
- `ROLE_TYPE`: Type of role (`R`=business role, `P`=PFCG profile)
- `ROLE_ID`: Role or profile name/pattern (may include wildcards like `SAP_BCR_$`)
- `ROLE_RELEVANCE`: Relevance level (1=mandatory, 2=recommended, 3=optional)

### APS_IAM_W_USRCAT — IAM User Categories
Defines user categories (technical user types) with their properties and user/group patterns.
- `USER_CATEGORY_ID`: User category identifier (PK, e.g. `CUSTOMER_BUSINESS`, `SAP_SUPPORT`)
- `USER_DESCRIPTION`: Human-readable description
- `USER_TYPE`: User type code (`A`=dialog, `B`=background, `S`=system, `L`=reference)
- `USER_BNAME_PATTERN`: Username naming pattern (e.g. `CB%10`)
- `USER_GROUP`: Required user group
- `SECURITY_POLICY_NAME`: Default security policy

### APS_IAM_W_USRPRC — IAM User Pricing/License Categories
Defines IAM user pricing categories with weight values and read-access companion categories.
- `USRPRC_ID`: Pricing category identifier (PK, e.g. `ADVANCED`, `SELFSERVICE`)
- `WEIGHT`: Numeric weight for license calculation (positive = more restrictive)
- `USRPRC_ID_READ`: Associated read-only pricing category

### APS_IAM_W_USRPRT — IAM User Pricing Category Texts
Human-readable labels for user pricing categories.
- `LANGU`: Language key
- `USRPRC_ID`: Pricing category identifier (FK to APS_IAM_W_USRPRC)
- `TEXT`: Display label (e.g. `Advanced`, `Self Service`)

### APS_IAM_W_VAR — IAM App Descriptor Variants
Maps apps to their Fiori descriptor/UI5 variant IDs, controlling app groupability on the launchpad.
- `APP_ID`: App identifier (FK to APS_IAM_W_APP)
- `DESCRIPTOR_VARIANT_ID`: UI5 descriptor variant identifier
- `GROUPABLE`: Whether the app can be grouped on the launchpad (X = yes)

### APS_IAM_W_BUC — Business Catalogs (master)
Master table for Business Catalogs — the primary grouping unit for Fiori apps in IAM.
**⚠ Not directly queryable via `mcp__er6__query_sql`** — use `APS_IAM_W_BRTBUC` to list catalogs by BRT, or `APS_IAM_W_BC_APP` to look up the catalog for a specific app.
- `BU_CATALOG_ID`: Business Catalog identifier (PK, e.g. `SAP_FIN_BC_GL_REPORTING_MY_PC`)
- `BU_CATALOG_TYPE`: Catalog type (`A`=standard)
- `SCOPE_DEPENDENT`: Whether the catalog is scope-dependent (X = yes)
- `CATALOG_ID`: Corresponding Fiori Launchpad catalog ID
- `APP_MIGRATION_STATUS`: Migration status
- `FLP_GROUP_ID`: Fiori Launchpad group ID
- `AGR_NAME`: Associated PFCG role name
- `DERIVABLE` / `RESTRICTABLE` / `READ_ONLY`: Catalog-level flags
- `CREATE_USER` / `CHANGE_USER`: Audit users
- `CREATE_TIMESTAMP` / `CHANGE_TIMESTAMP`: Audit timestamps

## Business Role Templates Quick Reference

### Treasury BRTs

| BRT ID | Display Name | Office |
|--------|--------------|--------|
| `SAP_BR_TREASURY_SPECIALIST_FOE` | Treasury Specialist - Front Office | FOE |
| `SAP_BR_TREASURY_SPECIALIST_BOE` | Treasury Specialist - Back Office | BOE |
| `SAP_BR_TREASURY_SPECIALIST_MOE` | Treasury Specialist - Middle Office | MOE |
| `SAP_BR_TREASURY_ACCOUNTANT` | Treasury Accountant | BOE |
| `SAP_BR_TREASURY_RISK_MANAGER` | Treasury Risk Manager | Mixed |

Country variants (`_CN`, `_SG`, `_TH`, `_BR`) follow the same catalog pattern as their base BRT.

### Cash Management BRTs

| BRT ID | Display Name | Catalogs |
|--------|--------------|---------|
| `SAP_BR_CASH_MANAGER` | Cash Manager | BAM2_PC, BAA_APPROVE_PC, BAI_PC |
| `SAP_BR_CASH_SPECIALIST` | Cash Management Specialist | BAM2_PC, BAA_SUBMIT_PC, BAA_APPROVE_PC, BAI_PC |
