# IAM Assistant — Memo Index

This index lists all saved memos. Claude loads this file at session start to check for relevant prior work.

## How to use

- `/memo save <topic>` — save current session findings to a memo file
- `/memo load <topic>` — load a memo into the current session context
- `/memo list` — show this index
- `/memo clear <topic>` — delete a memo file (irreversible)

## Saved Memos

<!-- Memos are listed below. Each entry: [title](filename.md) — one-line summary | date -->

- [TRM Templates Catalog Health Check](trm_tmpl_pc-healthcheck.md) — SAP_FIN_BC_TRM_TMPL_PC: FOE-clean (prior wildcards remediated); 5 app/catalog RT-coverage mismatches | 2026-05-27
- [Treasury SoD Compliance Scan](treasury-sod-scan.md) — Full per-instance scan: 4 violations across 3 apps (F9023, FTTM_AI_CREATE, TOEHREQO_TA ×2) — baseline confirmed | 2026-05-22
- [F9016 Authorization & Restriction-Type Review](f9016-auth-review.md) — F9016_TRAN auth profile + RT review; F_CLM_BAI grants full CRUD (potential over-permissive) | 2026-05-21
