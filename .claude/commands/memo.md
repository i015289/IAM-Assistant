
# Memo Skill

The memo system gives IAM Assistant persistent memory for findings, decisions, work in progress, and known-good baselines across sessions.

## Storage

All memos live in `.claude/memo/`:
- `INDEX.md` — index of all memos (always loaded at session start)
- One `.md` file per topic/investigation (e.g. `trm-sod.md`, `cash-f1366.md`)

## Sub-commands

### `/memo save [topic]`

Save current session findings to a persistent memo file.

1. If `topic` is not provided, infer it from the current conversation (e.g. `trm-sod`, `cash-f9017`, `hedge-moe`).
2. Derive a filename: lowercase, hyphens, `.md` extension (e.g. `trm-catalog-split.md`).
3. Write the file to `.claude/memo/<filename>.md` using this structure:

```markdown
# <Title>

**Date:** <YYYY-MM-DD>
**Domain:** <Treasury / Cash / Both>
**Status:** <In Progress / Complete>

## Findings

<Bullet list of key findings from this session>

## Decisions

<Decisions made and rationale — "We assigned X to FOE because...">

## Work in Progress

<Steps remaining, open questions, next actions>

## Known Good Baselines

<Apps or configs confirmed correct — "F1366A_TRAN: ACTVT 03 only on F_CLM_BAM — correct">
```

4. Update `INDEX.md`: add a line under `## Saved Memos` in the format:
   `- [Title](filename.md) — one-line summary | YYYY-MM-DD`

5. Confirm to the user: `Memo saved: .claude/memo/<filename>.md`

---

### `/memo load [topic]`

Load a previously saved memo into context.

1. Read `.claude/memo/INDEX.md` and show matching entries if `topic` is ambiguous.
2. Read the memo file and summarize its contents to the user:
   - Status, date, domain
   - Key findings (bullet list)
   - Work in progress / next steps
3. Offer to resume: `Resume from where we left off?`

---

### `/memo list`

Show all saved memos.

Read `.claude/memo/INDEX.md` and display the `## Saved Memos` section. If empty, say so.

---

### `/memo clear <topic>`

Delete a memo file.

1. Confirm with the user before deleting: `Delete memo '<topic>'? This cannot be undone.`
2. On confirmation: delete `.claude/memo/<filename>.md` and remove the entry from `INDEX.md`.

---

### `/memo update [topic]`

Update an existing memo with new findings from the current session.

1. Load the existing memo.
2. Append new findings to the relevant sections (do not overwrite existing content).
3. Update the `**Date:**` field to today.
4. Confirm: `Memo updated: .claude/memo/<filename>.md`

---

## Auto-load at session start

At the start of every session, Claude reads `.claude/memo/INDEX.md`. If any memos are marked `Status: In Progress`, Claude mentions them:

> Found in-progress memo: **[title]** (`topic`) — last updated YYYY-MM-DD. Load it to resume?

---

## Content types reference

| Type | What to capture |
|------|----------------|
| **Findings** | SoD violations, app FOE/BOE classification, forbidden combinations found |
| **Decisions** | Catalog split proposals, app-to-catalog assignments with rationale |
| **Work in Progress** | Partially executed `/hermes` plans, open questions, next steps |
| **Known Good Baselines** | Apps/configs confirmed correct — useful for future regression checks |

---

## Example memo filename conventions

| Investigation | Filename |
|---------------|----------|
| TRM catalog FOE/BOE split | `trm-catalog-split.md` |
| T_TOE_HR hedge SoD analysis | `hedge-ttoe-hr-sod.md` |
| Cash F9017 health check | `cash-f9017-healthcheck.md` |
| FOE BRT catalog footprint | `trm-brt-foe-catalog.md` |
