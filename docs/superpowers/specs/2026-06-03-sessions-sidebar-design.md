# Sessions Sidebar — Design

**Date:** 2026-06-03
**Scope:** UI only — `ui/templates/index.html`, `ui/static/style.css`, `ui/static/app.js`
**Goal:** Replace the single-session-per-tab model with a multi-session workspace. Users get a left sidebar listing saved sessions, can switch between them, rename, delete, and create new ones. Sessions persist across browser restarts via localStorage. Existing in-flight conversations migrate cleanly.

## Rationale

The current implementation persists a single conversation in `sessionStorage` (lost when the tab closes) and has no way to revisit prior queries beyond scrolling back in the same tab. Many IAM investigations span days — the user explicitly asked for a session list. localStorage keeps the feature client-side and avoids a backend table.

## Data Model

Two storage layers:

**localStorage** — survives browser restart:
- `iam_sessions` → JSON array of session metadata, newest first:
  ```json
  [
    { "id": "a1b2c3d4", "title": "BRT coverage for SAP_BR_TREASURY_SPECIALIST_FOE", "createdAt": 1717400000000, "updatedAt": 1717410000000 },
    { "id": "e5f6g7h8", "title": "SoD scan on Treasury FOE catalogs", "createdAt": 1717350000000, "updatedAt": 1717350000000 }
  ]
  ```
- `iam_session:<id>` → JSON array of message objects `{ role, content }`. Same shape as today's `iam_chat_history`, just keyed per session.

**sessionStorage** — per-tab pointer:
- `iam_active_session` → the id string of the currently-loaded session in this tab. Lets a refresh restore the same session in the same tab, but a fresh tab opens whichever session was most-recently used (across tabs) by falling back to `iam_sessions[0].id` when `iam_active_session` is unset.

### Title derivation

A new session's `title` starts as `"New session"`. The first time a user message is sent in that session, `title` becomes the first 40 characters of that user message (trimmed; ellipsised with `…` if longer). On subsequent messages the title is left alone unless the user renames it.

### Id generation

`id = crypto.randomUUID().slice(0, 8)`. Eight hex chars are plenty for client-only uniqueness; we read/write by exact string match.

### Migration

One-shot, runs at startup:
- If `localStorage.getItem('iam_sessions')` is null AND `sessionStorage.getItem('iam_chat_history')` exists with at least one message:
  - Create a new session in localStorage from those messages (auto-titled from first user message if any, else `"Imported session"`).
  - Set it as the active session in sessionStorage.
- Always remove `iam_chat_history` from sessionStorage afterwards (orphaned key).

## UI

### Layout

```
┌─────────────────────────────────────────────────────────┐
│ ⚡ IAM Assistant                    ER6 connected  dev  │
├──────────────┬──────────────────────────────────────────┤
│ + New        │                                          │
│ ──────────   │                                          │
│ Treasury …   │           [chat messages]                │
│ SoD scan …   │                                          │
│ Cash mgmt …  │                                          │
│              │           [input bar]                    │
└──────────────┴──────────────────────────────────────────┘
```

- `#sidebar`: 240px fixed width, dark panel, `border-right: 1px solid var(--border)`, full viewport height under the header.
- `+ New` button pinned at the top of the sidebar.
- `.session-row` per session: title (truncated) + a small relative timestamp. Hover surfaces a small `×` delete icon on the right. Active session highlighted with a left accent border (`border-left: 3px solid var(--accent)`).
- The header `+ New session` button (added in the previous change) is **removed** — that affordance now lives in the sidebar.

### Interactions

- **Click a session row** → switch. Active session id updates in sessionStorage. Chat messages re-render from that session's stored history.
- **Click + New** → create a new session (id, default title "New session"), set active, clear the chat area, show the welcome block.
- **Double-click a session title** → enter inline edit (title becomes a text input). Enter saves, Esc cancels, blur saves.
- **Hover row → click ×** → confirm modal (`window.confirm("Delete this session?")`). On confirm: remove from `iam_sessions`, remove `iam_session:<id>`. If the deleted session was active, switch to the next-most-recent one (or create a new empty one if list is now empty).
- **Send a message in a session with default title** → after the user's message lands in history, auto-title from the first user message.
- **Send any message** → bump that session's `updatedAt` and re-sort sidebar (newest on top).

### Welcome behaviour

The welcome block is per-session: shown only when the active session's history is empty. Switching to an empty session shows it; switching to a session with history hides it. The `<template>` clone-and-insert mechanism from the previous change still works.

## File-level changes

### `ui/templates/index.html`

- Restructure `#layout` to `display: flex; flex-direction: row` containing `#sidebar` and `#chat-panel`.
- Remove the header `+ New session` button.
- Add `<aside id="sidebar">` containing a `+ New` button at top and a `<div id="session-list">` for the rows.

### `ui/static/style.css`

- Add `#sidebar`, `#sidebar-new-btn`, `#session-list`, `.session-row`, `.session-row.active`, `.session-row .session-title`, `.session-row .session-time`, `.session-row .session-delete`, `.session-row .session-title.editing` rules.
- Adjust `#layout` to flex-row.
- Remove `#new-session-btn` rule (header button is gone).

### `ui/static/app.js`

A new internal module-style namespace `Sessions` with:

- `Sessions.list()` → `Array<{id, title, createdAt, updatedAt}>` (sorted newest first by `updatedAt`)
- `Sessions.getMessages(id)` → `Array<{role, content}>`
- `Sessions.saveMessages(id, messages)` → updates `iam_session:<id>` AND bumps that session's `updatedAt`, re-sorts list, persists `iam_sessions`
- `Sessions.create()` → returns new id; appends to list; default title `"New session"`
- `Sessions.setTitle(id, title)` → persists rename
- `Sessions.delete(id)` → removes both keys; returns next-active-id-suggestion (`null` if list empty)
- `Sessions.getActive()` → reads sessionStorage, falls back to most-recent session, falls back to creating an empty one
- `Sessions.setActive(id)` → writes sessionStorage

Then the existing `loadHistory` / `saveHistory` become thin shims over `Sessions.getMessages(activeId)` / `Sessions.saveMessages(activeId, messages)`.

Sidebar rendering: a `renderSidebar()` function that empties `#session-list` and re-creates rows from `Sessions.list()`. Called on startup, after every mutating action. Each row gets click, dblclick, and a delete-button click handler — all delegated through closures over the session id.

### Switching sessions in-place

`switchSession(id)`:
1. `Sessions.setActive(id)`
2. Clear `#messages` (`.innerHTML = ''`)
3. Re-render messages by reusing existing `restoreChatMessages()` (which already reads from `loadHistory`).
4. Show welcome iff messages are empty
5. Re-render sidebar (to update active highlight)

### First-message auto-title hook

In `sendMessage`, after `appendUserMessage(text)` and `saveHistory(history)` for the user turn, check whether the active session's title is the literal `"New session"` (i.e. untouched). If so, derive a new title from `text` (first 40 chars, trim) and call `Sessions.setTitle(activeId, newTitle)`, then re-render the sidebar.

### Session bumping

`Sessions.saveMessages` is the single point that bumps `updatedAt` and re-sorts. After it, the sidebar re-renders (sidebar render is cheap — it's at most ~50 rows — so we always re-render rather than diff).

## Out of Scope

- Backend persistence (deferred — the "DB" option was explicitly rejected).
- Search across sessions, export/import, pinning, archiving, folder grouping.
- Multi-tab synchronization (two tabs on different sessions are fine; two tabs on the same session would cause last-writer-wins, accepted).
- Storage quota handling (5 MB localStorage cap; for typical text-only IAM chats this hits >100 sessions of substantial length — far beyond user need).

## Verification

After implementation, manually in a browser:

1. Cold load with no prior data: sidebar shows a single empty session ("New session"), welcome visible in main panel.
2. Send a query: title in sidebar updates to first 40 chars; row shows recent timestamp; welcome disappears.
3. Click "+ New": new "New session" appears at top, active; chat clears and welcome reappears.
4. Send a query in the new session, then click the older session in the sidebar: messages of the older session re-render correctly; sidebar active highlight moves.
5. Double-click a title, edit, press Enter: title updates and persists.
6. Hover a non-active row, click ×, confirm: row disappears.
7. Hover the active row, click ×, confirm: another session becomes active and renders.
8. Delete the last session: a fresh empty session is auto-created.
9. Refresh in a tab: same session stays active.
10. Open a new tab: most-recent session is active.
11. Close all browser windows, reopen: sessions still listed.
12. Existing pre-feature `iam_chat_history` in sessionStorage migrates into a new session on first load and is then cleared.
13. DevTools: `iam_sessions` and one or more `iam_session:<id>` keys are present; `iam_chat_history` and `iam_chat_tabs` are gone.
