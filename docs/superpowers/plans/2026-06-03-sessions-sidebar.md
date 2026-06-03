# Sessions Sidebar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the single-session sessionStorage chat with a multi-session workspace: a left sidebar listing sessions with create/switch/rename/delete, persisted in localStorage, with a one-shot migration of any in-flight conversation.

**Architecture:** Add a `Sessions` JS module that owns all storage (`iam_sessions` list in localStorage, one `iam_session:<id>` blob per session, `iam_active_session` pointer in sessionStorage). `loadHistory`/`saveHistory` become thin shims over `Sessions.getMessages` / `Sessions.saveMessages`. A `renderSidebar()` function rebuilds the row list from `Sessions.list()` after every mutation. The header `+ New session` button moves into the sidebar.

**Tech Stack:** Vanilla JS, plain CSS, Jinja HTML template.

**Reference spec:** `docs/superpowers/specs/2026-06-03-sessions-sidebar-design.md`

**Testing:** No JS unit tests in this repo. Manual browser verification consolidated in Task 6.

---

## File Structure

- **Modify** `ui/templates/index.html` — restructure `#layout` to flex sidebar + chat. Remove header `+ New session` button. Add `<aside id="sidebar">` with `+ New` button and an empty `<div id="session-list">`.
- **Modify** `ui/static/style.css` — remove `#new-session-btn` rule. Add `#layout` flex-row, `#sidebar`, `#sidebar-new-btn`, `#session-list`, `.session-row`, `.session-row.active`, `.session-title`, `.session-title.editing`, `.session-time`, `.session-delete` rules.
- **Modify** `ui/static/app.js` — add `Sessions` module; rewrite `loadHistory`/`saveHistory` as shims; add `renderSidebar`, `switchSession`, sidebar event handlers, migration code; rewire `sendMessage` for auto-titling; replace the old "New session" header-button handler with a sidebar `+ New` handler.

No new files. Three files touched, ~280 LOC of JS, ~50 LOC of CSS, ~15 LOC of HTML.

---

## Task 1: Restructure HTML layout (sidebar shell)

**Files:** Modify `ui/templates/index.html`

This task only adds the empty sidebar shell and removes the header button. JS in later tasks will populate it.

- [ ] **Step 1: Remove the header `+ New session` button**

In `ui/templates/index.html`, find:

```html
  <div class="header-right">
    <button id="new-session-btn" type="button" title="Clear conversation and start fresh">+ New session</button>
    <span id="mcp-indicator" class="indicator {{ 'connected' if mcp_status == 'connected' else 'disconnected' }}">
      ● ER6 {{ mcp_status }}
    </span>
    <span class="username">{{ username }}</span>
    <a href="/auth/logout" class="signout">Sign out</a>
  </div>
```

Replace with:

```html
  <div class="header-right">
    <span id="mcp-indicator" class="indicator {{ 'connected' if mcp_status == 'connected' else 'disconnected' }}">
      ● ER6 {{ mcp_status }}
    </span>
    <span class="username">{{ username }}</span>
    <a href="/auth/logout" class="signout">Sign out</a>
  </div>
```

- [ ] **Step 2: Add the sidebar inside `#layout` before `#chat-panel`**

Find the `#layout` block:

```html
<div id="layout">

  <!-- Chat panel (full viewport) -->
  <div id="chat-panel">
```

Replace with:

```html
<div id="layout">

  <!-- Left: sessions sidebar -->
  <aside id="sidebar">
    <button id="sidebar-new-btn" type="button">+ New</button>
    <div id="session-list"></div>
  </aside>

  <!-- Right: chat panel -->
  <div id="chat-panel">
```

(The closing tags below `#chat-panel` and `#layout` stay unchanged.)

- [ ] **Step 3: Commit**

```bash
git add ui/templates/index.html
git commit -m "feat(ui): add sidebar shell, drop header New session button"
```

---

## Task 2: CSS for the sidebar layout

**Files:** Modify `ui/static/style.css`

- [ ] **Step 1: Remove the now-unused `#new-session-btn` rule**

In `ui/static/style.css`, find and delete this block (it was added in the previous change):

```css
#new-session-btn {
  background: transparent; color: var(--muted);
  border: 1px solid var(--border); border-radius: 6px;
  padding: 4px 10px; font-size: 12px; font-family: inherit;
  cursor: pointer;
}
#new-session-btn:hover { color: var(--text); border-color: var(--accent); }
```

- [ ] **Step 2: Confirm `#layout` is already flex**

`#layout` should already have `display: flex; height: calc(100vh - var(--header-h)); overflow: hidden;`. If it doesn't, fix it. Direction defaults to `row`, which is what we want; do not add an explicit `flex-direction`.

- [ ] **Step 3: Add the sidebar rules**

Add these rules immediately after the `#layout` rule (and before the `#chat-panel` rule):

```css
/* Sessions sidebar */
#sidebar {
  width: 240px; flex-shrink: 0;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex; flex-direction: column;
  overflow: hidden;
}
#sidebar-new-btn {
  margin: 12px; padding: 8px 12px;
  background: transparent; color: var(--text);
  border: 1px solid var(--border); border-radius: 6px;
  font-size: 13px; font-family: inherit; cursor: pointer;
  text-align: left;
}
#sidebar-new-btn:hover { border-color: var(--accent); color: var(--accent); }

#session-list {
  flex: 1; overflow-y: auto; padding: 0 4px 12px;
  display: flex; flex-direction: column; gap: 2px;
}
.session-row {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 10px; border-radius: 6px;
  cursor: pointer; user-select: none;
  border-left: 3px solid transparent;
}
.session-row:hover { background: var(--bg); }
.session-row.active { background: var(--bg); border-left-color: var(--accent); }
.session-title {
  flex: 1; min-width: 0;
  font-size: 13px; color: var(--text);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.session-title.editing {
  background: var(--bg); border: 1px solid var(--accent); border-radius: 4px;
  padding: 2px 4px; outline: none;
}
.session-time { font-size: 11px; color: var(--muted); flex-shrink: 0; }
.session-delete {
  width: 20px; height: 20px; border: none; background: transparent;
  color: var(--muted); cursor: pointer; font-size: 14px; line-height: 1;
  visibility: hidden; flex-shrink: 0;
}
.session-row:hover .session-delete { visibility: visible; }
.session-delete:hover { color: var(--red); }
```

- [ ] **Step 4: Commit**

```bash
git add ui/static/style.css
git commit -m "style(ui): sidebar, session-row, inline-edit styling"
```

---

## Task 3: Add the `Sessions` storage module

**Files:** Modify `ui/static/app.js`

This task adds the `Sessions` module **alongside** the existing `loadHistory`/`saveHistory`. We do not yet rewire those — that's Task 4. This isolates the storage abstraction so we can verify it standalone before flipping the read/write path.

- [ ] **Step 1: Add the module near the top of `app.js`**

Find the existing top of `ui/static/app.js`:

```js
// Conversation history is persisted in sessionStorage so a refresh inside
// the same browser tab keeps the prior conversation visible.
const HISTORY_KEY = 'iam_chat_history';

function loadHistory() {
  try { return JSON.parse(sessionStorage.getItem(HISTORY_KEY) || '[]'); }
  catch { return []; }
}

function saveHistory(messages) {
  sessionStorage.setItem(HISTORY_KEY, JSON.stringify(messages));
}
```

Replace with:

```js
// Sessions are stored in localStorage so they survive browser restart.
//   iam_sessions       → JSON array of {id, title, createdAt, updatedAt}
//   iam_session:<id>   → JSON array of {role, content}
// The active session id lives in sessionStorage (per-tab).
const SESSIONS_KEY = 'iam_sessions';
const ACTIVE_SESSION_KEY = 'iam_active_session';
const sessionDataKey = (id) => `iam_session:${id}`;

const Sessions = {
  list() {
    try {
      const raw = JSON.parse(localStorage.getItem(SESSIONS_KEY) || '[]');
      // Newest first by updatedAt (then createdAt as tiebreaker).
      return raw.slice().sort((a, b) =>
        (b.updatedAt || b.createdAt || 0) - (a.updatedAt || a.createdAt || 0));
    } catch { return []; }
  },

  _writeList(list) {
    localStorage.setItem(SESSIONS_KEY, JSON.stringify(list));
  },

  getMessages(id) {
    try { return JSON.parse(localStorage.getItem(sessionDataKey(id)) || '[]'); }
    catch { return []; }
  },

  saveMessages(id, messages, { now = Date.now() } = {}) {
    localStorage.setItem(sessionDataKey(id), JSON.stringify(messages));
    const list = Sessions.list();
    const idx = list.findIndex(s => s.id === id);
    if (idx >= 0) {
      list[idx] = { ...list[idx], updatedAt: now };
      Sessions._writeList(list);
    }
  },

  create({ title = 'New session', now = Date.now() } = {}) {
    const id = crypto.randomUUID().slice(0, 8);
    const list = Sessions.list();
    list.push({ id, title, createdAt: now, updatedAt: now });
    Sessions._writeList(list);
    return id;
  },

  setTitle(id, title) {
    const list = Sessions.list();
    const idx = list.findIndex(s => s.id === id);
    if (idx < 0) return;
    list[idx] = { ...list[idx], title };
    Sessions._writeList(list);
  },

  delete(id) {
    const list = Sessions.list().filter(s => s.id !== id);
    Sessions._writeList(list);
    localStorage.removeItem(sessionDataKey(id));
    return list[0]?.id ?? null;
  },

  getActive() {
    let id = sessionStorage.getItem(ACTIVE_SESSION_KEY);
    const list = Sessions.list();
    if (id && list.some(s => s.id === id)) return id;
    if (list.length > 0) {
      sessionStorage.setItem(ACTIVE_SESSION_KEY, list[0].id);
      return list[0].id;
    }
    // No sessions exist yet — create one.
    id = Sessions.create();
    sessionStorage.setItem(ACTIVE_SESSION_KEY, id);
    return id;
  },

  setActive(id) {
    sessionStorage.setItem(ACTIVE_SESSION_KEY, id);
  },
};

// loadHistory / saveHistory remain shims over the active session for now.
// They're rewired to Sessions in Task 4.
function loadHistory() {
  try { return JSON.parse(sessionStorage.getItem('iam_chat_history') || '[]'); }
  catch { return []; }
}

function saveHistory(messages) {
  sessionStorage.setItem('iam_chat_history', JSON.stringify(messages));
}
```

Notes:
- `crypto.randomUUID()` is available in all modern browsers (and over `https`/`localhost`); we're not running this in legacy contexts.
- `Sessions.saveMessages` accepts an optional `now` argument so future tests/code can pin time. Default `Date.now()` is fine for production.
- `getActive` is the only place that auto-creates an empty session — it's the safety net so the rest of the app can always assume an active id exists.

- [ ] **Step 2: Confirm syntax**

Run: `node --check ui/static/app.js`
Expected: clean exit (no syntax errors).

- [ ] **Step 3: Commit**

```bash
git add ui/static/app.js
git commit -m "feat(ui): add Sessions storage module (not wired yet)"
```

---

## Task 4: Wire `loadHistory`/`saveHistory` to `Sessions`; add migration

**Files:** Modify `ui/static/app.js`

Now the storage abstraction is in place — flip the read/write path and migrate any pre-existing single-session data.

- [ ] **Step 1: Rewrite `loadHistory` / `saveHistory` as `Sessions` shims**

In `ui/static/app.js`, find the shim block we added in Task 3:

```js
// loadHistory / saveHistory remain shims over the active session for now.
// They're rewired to Sessions in Task 4.
function loadHistory() {
  try { return JSON.parse(sessionStorage.getItem('iam_chat_history') || '[]'); }
  catch { return []; }
}

function saveHistory(messages) {
  sessionStorage.setItem('iam_chat_history', JSON.stringify(messages));
}
```

Replace with:

```js
// loadHistory / saveHistory operate on the active session.
function loadHistory() {
  return Sessions.getMessages(Sessions.getActive());
}

function saveHistory(messages) {
  Sessions.saveMessages(Sessions.getActive(), messages);
}
```

- [ ] **Step 2: Add a one-shot migration helper near the bottom of the file**

Find the bottom-of-file block (currently):

```js
// Drop the orphaned tab-state key from older versions; harmless if absent.
sessionStorage.removeItem('iam_chat_tabs');

// "New session" button: clear history and DOM, restore welcome.
document.getElementById('new-session-btn').addEventListener('click', () => {
  sessionStorage.removeItem(HISTORY_KEY);
  document.getElementById('messages').innerHTML = '';
  const input = document.getElementById('input');
  input.value = '';
  input.style.height = 'auto';
  showWelcome();
  input.focus();
});

if (loadHistory().length === 0) {
  showWelcome();
}

restoreChatMessages();
```

Replace with:

```js
// Drop orphaned keys from older versions; harmless if absent.
sessionStorage.removeItem('iam_chat_tabs');

// One-shot migration: hoist any pre-feature in-flight conversation
// (sessionStorage-only) into a real session, then clear the legacy key.
function migrateLegacyHistory() {
  if (localStorage.getItem(SESSIONS_KEY)) return; // already migrated or fresh install
  let legacy;
  try { legacy = JSON.parse(sessionStorage.getItem('iam_chat_history') || '[]'); }
  catch { legacy = []; }
  if (legacy.length === 0) return;
  const firstUser = legacy.find(m => m.role === 'user');
  const title = firstUser
    ? firstUser.content.trim().slice(0, 40) || 'Imported session'
    : 'Imported session';
  const id = Sessions.create({ title });
  Sessions.saveMessages(id, legacy);
  Sessions.setActive(id);
}

migrateLegacyHistory();
sessionStorage.removeItem('iam_chat_history');

// Sidebar `+ New` button: create a fresh session and switch to it.
document.getElementById('sidebar-new-btn').addEventListener('click', () => {
  const id = Sessions.create();
  switchSession(id);
});

if (loadHistory().length === 0) {
  showWelcome();
}

renderSidebar();
restoreChatMessages();
```

Note: this references `switchSession()` and `renderSidebar()` which are added in Task 5. The file will not run correctly until Task 5 lands. Do not test in browser between Task 4 and Task 5.

- [ ] **Step 3: Confirm syntax**

Run: `node --check ui/static/app.js`
Expected: clean exit (the missing-function references are runtime-only; node --check is syntax-only and will pass).

- [ ] **Step 4: Commit**

```bash
git add ui/static/app.js
git commit -m "feat(ui): route history through Sessions, migrate legacy key"
```

---

## Task 5: Sidebar rendering, switching, rename, delete; auto-title

**Files:** Modify `ui/static/app.js`

Now the dynamic sidebar UI: render rows, handle clicks, double-click rename, hover delete, plus the auto-title hook in `sendMessage`. After this task the file is runnable end-to-end.

- [ ] **Step 1: Add helper functions above `restoreChatMessages`**

In `ui/static/app.js`, find the line `// --- Startup: replay prior session into the DOM --------------------------`. Insert the following block immediately above it:

```js
// --- Sidebar rendering & session switching -------------------------------

function relativeTime(ts) {
  if (!ts) return '';
  const diff = Date.now() - ts;
  if (diff < 60_000) return 'just now';
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h`;
  return `${Math.floor(diff / 86_400_000)}d`;
}

function renderSidebar() {
  const list = document.getElementById('session-list');
  const activeId = Sessions.getActive();
  list.innerHTML = '';
  for (const s of Sessions.list()) {
    const row = document.createElement('div');
    row.className = 'session-row' + (s.id === activeId ? ' active' : '');
    row.dataset.id = s.id;

    const title = document.createElement('div');
    title.className = 'session-title';
    title.textContent = s.title;
    title.title = s.title;

    const time = document.createElement('span');
    time.className = 'session-time';
    time.textContent = relativeTime(s.updatedAt);

    const del = document.createElement('button');
    del.className = 'session-delete';
    del.type = 'button';
    del.title = 'Delete session';
    del.textContent = '×';

    row.appendChild(title);
    row.appendChild(time);
    row.appendChild(del);

    // Click row → switch (but ignore clicks that originated on the delete
    // button or while editing the title).
    row.addEventListener('click', (e) => {
      if (e.target === del) return;
      if (title.classList.contains('editing')) return;
      if (s.id !== Sessions.getActive()) switchSession(s.id);
    });

    // Double-click title → inline rename.
    title.addEventListener('dblclick', (e) => {
      e.stopPropagation();
      beginRename(title, s.id, s.title);
    });

    // Click × → confirm and delete.
    del.addEventListener('click', (e) => {
      e.stopPropagation();
      if (!confirm(`Delete session "${s.title}"?`)) return;
      const wasActive = (s.id === Sessions.getActive());
      const nextActive = Sessions.delete(s.id);
      if (wasActive) {
        if (nextActive) {
          switchSession(nextActive);
        } else {
          // List empty — getActive will auto-create a fresh one.
          const fresh = Sessions.getActive();
          switchSession(fresh);
        }
      } else {
        renderSidebar();
      }
    });

    list.appendChild(row);
  }
}

function beginRename(titleEl, id, originalTitle) {
  titleEl.classList.add('editing');
  titleEl.contentEditable = 'plaintext-only';
  titleEl.textContent = originalTitle;
  titleEl.focus();
  // Select all text inside the editable element.
  const range = document.createRange();
  range.selectNodeContents(titleEl);
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);

  let finished = false;
  const finish = (commit) => {
    if (finished) return;
    finished = true;
    titleEl.contentEditable = 'false';
    titleEl.classList.remove('editing');
    const newTitle = titleEl.textContent.trim().slice(0, 80);
    if (commit && newTitle && newTitle !== originalTitle) {
      Sessions.setTitle(id, newTitle);
    }
    renderSidebar();
  };

  titleEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); finish(true); }
    else if (e.key === 'Escape') { e.preventDefault(); finish(false); }
  });
  titleEl.addEventListener('blur', () => finish(true), { once: true });
}

function switchSession(id) {
  Sessions.setActive(id);
  document.getElementById('messages').innerHTML = '';
  hideWelcome();
  restoreChatMessages();
  if (loadHistory().length === 0) showWelcome();
  renderSidebar();
  document.getElementById('input').focus();
}
```

Notes:
- `contentEditable = 'plaintext-only'` is supported in WebKit/Blink; Firefox falls back to `'true'` automatically. We accept the slight per-browser variance — a paste with markup will still be cleaned by `textContent.trim()`.
- `confirm()` is the spec-mandated confirmation; we don't replace it with a custom modal.
- `relativeTime` returns short strings (`5m`, `2h`, `3d`); ASCII-only to match the rest of the UI.

- [ ] **Step 2: Add the auto-title hook in `sendMessage`**

In `ui/static/app.js`, find the block in `sendMessage`:

```js
  appendUserMessage(text);

  const history = loadHistory();
  history.push({ role: 'user', content: text });
  saveHistory(history);
```

Replace with:

```js
  appendUserMessage(text);

  const history = loadHistory();
  history.push({ role: 'user', content: text });
  saveHistory(history);

  // Auto-title an untouched session from the first user message.
  const activeId = Sessions.getActive();
  const meta = Sessions.list().find(s => s.id === activeId);
  if (meta && meta.title === 'New session') {
    const t = text.trim();
    const newTitle = t.length > 40 ? t.slice(0, 40) + '…' : t;
    Sessions.setTitle(activeId, newTitle || 'New session');
    renderSidebar();
  }
```

- [ ] **Step 3: Re-render sidebar after streamed assistant turn so timestamps update**

In `sendMessage`, find the `[DONE]` branch:

```js
        if (payload === '[DONE]') {
          // Finalize
          aiEl.querySelector('.cursor')?.remove();
          history.push({ role: 'assistant', content: buffer });
          saveHistory(history);
          streamDone = true;
          break;
        }
```

Replace with:

```js
        if (payload === '[DONE]') {
          // Finalize
          aiEl.querySelector('.cursor')?.remove();
          history.push({ role: 'assistant', content: buffer });
          saveHistory(history);
          renderSidebar();
          streamDone = true;
          break;
        }
```

- [ ] **Step 4: Confirm syntax**

Run: `node --check ui/static/app.js`
Expected: clean exit.

- [ ] **Step 5: Commit**

```bash
git add ui/static/app.js
git commit -m "feat(ui): sidebar rendering, switch/rename/delete, auto-title"
```

---

## Task 6: Manual browser verification

**Files:** none modified.

Run through the spec's verification list (`docs/superpowers/specs/2026-06-03-sessions-sidebar-design.md` §Verification).

- [ ] **Step 1: Restart the dev server**

The Jinja env has `auto_reload=False`, so a template change requires a process restart. Stop the running uvicorn and start it again:

```bash
set -a && source .sapcli.env && set +a
conda run -n sapcli-env --no-capture-output uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

Open `http://localhost:8080` in a browser. Hard-refresh (Cmd+Shift+R / Ctrl+Shift+R) to bust HTML cache.

- [ ] **Step 2: Cold load with cleared storage**

In DevTools → Application → Storage → Clear site data. Reload.

Expected:
- Sidebar visible on the left, 240px wide, with `+ New` button at top.
- One session ("New session") in the sidebar, active.
- Welcome block visible in the main panel.

- [ ] **Step 3: Send a query**

Send any message. Expected:
- Sidebar title updates from "New session" to first 40 chars of the user message.
- After `[DONE]`, the row shows a recent timestamp.
- Welcome disappears.

- [ ] **Step 4: New session**

Click `+ New` in the sidebar. Expected:
- New "New session" row appears at the top, marked active.
- Chat panel is cleared, welcome reappears.

- [ ] **Step 5: Switch sessions**

Send something in the new session. Click the older session row. Expected:
- The older session's messages re-render in the chat panel.
- Active highlight (left accent border) moves to the older session.
- Welcome stays hidden because that session has messages.

- [ ] **Step 6: Rename**

Double-click a session title. Expected: the title becomes editable. Type a new title; press Enter. Expected: title updates and persists across reload.

Press Escape during edit on another row → original title restored.

- [ ] **Step 7: Delete (non-active)**

Hover a non-active row → click `×` → confirm in dialog. Expected: row disappears; current chat is unchanged.

- [ ] **Step 8: Delete (active)**

Hover the active row → click `×` → confirm. Expected: another session becomes active and renders.

- [ ] **Step 9: Delete the last session**

Delete sessions one by one until none are left → confirm. Expected: a fresh empty "New session" auto-creates and becomes active; welcome shows.

- [ ] **Step 10: Persistence across browser restart**

Send a couple of messages in two different sessions. Close the browser tab/window. Reopen `http://localhost:8080`. Expected: both sessions still listed; the one that was most recently active is the active one.

- [ ] **Step 11: Migration of pre-feature data**

In DevTools, manually set sessionStorage:
- Key: `iam_chat_history`
- Value: `[{"role":"user","content":"old chat from before the feature"},{"role":"assistant","content":"old reply"}]`

Then clear localStorage `iam_sessions` and `iam_session:*` keys. Reload.

Expected:
- A new session "old chat from before the feature" appears, active, with the two messages rendered in the chat panel.
- `iam_chat_history` is gone from sessionStorage.

- [ ] **Step 12: Console clean**

DevTools Console must be clean: no `Cannot read properties of null`, no missing-element errors, no `crypto.randomUUID is not a function`.

- [ ] **Step 13: If anything fails**

Note the failure, jump to the offending Task, fix, re-commit, return here.

- [ ] **Step 14: Done**

No commit needed — verification only.
