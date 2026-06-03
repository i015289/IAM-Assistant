# Remove Right Results Panel — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete the right `#results-panel` (tabs, panes, welcome content inside it) so the chat panel fills the viewport. Move welcome guidance into the chat panel as a one-time greeting that disappears on first send.

**Architecture:** Pure UI deletion across three files. No new dependencies. Markdown rendering in the left bubble (already shipped) is the sole rendering surface. `enableSortableTable` and `renderMarkdown` are kept — both still used.

**Tech Stack:** Vanilla JS, plain CSS, Jinja HTML template.

**Reference spec:** `docs/superpowers/specs/2026-06-03-remove-right-panel-design.md`

**Testing:** No JS unit tests in this repo. Manual browser verification in Task 5.

---

## File Structure

- **Modify** `ui/templates/index.html` — delete `<div id="results-panel">…</div>`, add `<div id="welcome" class="welcome">…</div>` inside `#chat-panel` above `#messages`.
- **Modify** `ui/static/style.css` — delete all `#results-panel`, `#tab-bar`, `.tab` (and `.tab.*`), `#tab-content`, `.tab-pane` (and `.tab-pane *`) rules. Change `#chat-panel { width: 50% }` → `width: 100%` and remove `border-right`. Add a small `#welcome` rule.
- **Modify** `ui/static/app.js` — delete tab-related symbols and call sites; add welcome-element show/hide hooks; clean up old `iam_chat_tabs` sessionStorage key on startup.

---

## Task 1: Delete the right-panel HTML and add welcome inside the chat panel

**Files:** Modify: `ui/templates/index.html`

- [ ] **Step 1: Read current template**

Open `ui/templates/index.html`. Confirm `<div id="results-panel">` starts at the comment `<!-- Right: Results panel -->` (line ~39) and ends at its closing `</div>` (line ~58).

- [ ] **Step 2: Replace the right panel and inject welcome inside the chat panel**

Find this block (the entire chat-panel + results-panel layout):

```html
  <!-- Left: Chat panel -->
  <div id="chat-panel">
    <div id="messages"></div>
    <div id="input-bar">
      <textarea
        id="input"
        placeholder="Ask about roles, catalogs, SoD…"
        rows="1"
      ></textarea>
      <button id="send-btn" onclick="sendMessage()">Send</button>
    </div>
  </div>

  <!-- Right: Results panel -->
  <div id="results-panel">
    <div id="tab-bar">
      <div class="tab active" id="tab-welcome" data-tab="welcome">Welcome</div>
    </div>
    <div id="tab-content">
      <div class="tab-pane active" id="pane-welcome">
        <div class="welcome">
          <h2>IAM Assistant</h2>
          <p>Ask a question in the chat to get started. Results with tables, findings, and analysis will appear here.</p>
          <p>Examples:</p>
          <ul>
            <li>Show BRT coverage for SAP_BR_TREASURY_SPECIALIST_FOE</li>
            <li>Run a SoD scan on the Treasury FOE catalogs</li>
            <li>Check restriction type coverage for SAP_FIN_BC_TRM_TMPL_PC</li>
          </ul>
        </div>
      </div>
    </div>
  </div>

</div>
```

Replace with:

```html
  <!-- Chat panel (full viewport) -->
  <div id="chat-panel">
    <div id="welcome" class="welcome">
      <h2>IAM Assistant</h2>
      <p>Ask a question to get started. Examples:</p>
      <ul>
        <li>Show BRT coverage for SAP_BR_TREASURY_SPECIALIST_FOE</li>
        <li>Run a SoD scan on the Treasury FOE catalogs</li>
        <li>Check restriction type coverage for SAP_FIN_BC_TRM_TMPL_PC</li>
      </ul>
    </div>
    <div id="messages"></div>
    <div id="input-bar">
      <textarea
        id="input"
        placeholder="Ask about roles, catalogs, SoD…"
        rows="1"
      ></textarea>
      <button id="send-btn" onclick="sendMessage()">Send</button>
    </div>
  </div>

</div>
```

Notes:
- The outer wrapping `<div id="layout">` is unchanged.
- The welcome `<div>` has `id="welcome"` so JS can target it, and `class="welcome"` so existing `.welcome` styles apply.
- The previous welcome content kept its three example queries verbatim.

- [ ] **Step 3: Commit**

```bash
git add ui/templates/index.html
git commit -m "feat(ui): remove right results panel from layout"
```

---

## Task 2: Delete right-panel CSS and widen chat panel

**Files:** Modify: `ui/static/style.css`

- [ ] **Step 1: Locate the rules to delete**

In `ui/static/style.css`, find these blocks (line numbers approximate; search by content):

- `#results-panel { ... }` — the panel container
- `#tab-bar { ... }`
- `.tab { ... }` and `.tab.active { ... }` and `.tab:hover:not(.active) { ... }`
- `#tab-content { ... }`
- `.tab-pane { ... }` and `.tab-pane.active { ... }`
- `.tab-pane h1, .tab-pane h2 { ... }`
- `.tab-pane h3 { ... }`
- `.tab-pane p { ... }`
- `.tab-pane ul, .tab-pane ol { ... }`
- `.tab-pane li { ... }`
- `.tab-pane code { ... }`
- `.tab-pane pre { ... }`
- `.tab-pane pre code { ... }`
- `.tab-pane table { ... }`
- `.tab-pane th { ... }`
- `.tab-pane th:hover { ... }`
- `.tab-pane td { ... }`
- `.tab-pane tr:hover td { ... }`
- `.tab-pane blockquote { ... }`
- `.tab-pane blockquote p { ... }`

These are contiguous in the file (the `/* Results panel */` and following sections).

- [ ] **Step 2: Delete every rule listed above**

Remove all of them. Do NOT delete:
- The `.welcome { ... }` rule
- `.welcome h2 { ... }`
- `.welcome p, .welcome li { ... }`
- `.welcome ul { ... }`

These are reused by the moved welcome element.

- [ ] **Step 3: Update `#chat-panel`**

Find:

```css
#chat-panel {
  width: 50%;
  border-right: 1px solid var(--border);
  display: flex; flex-direction: column;
  background: var(--bg);
}
```

Replace with:

```css
#chat-panel {
  width: 100%;
  display: flex; flex-direction: column;
  background: var(--bg);
}
```

- [ ] **Step 4: Add the new `#welcome` rule**

Add immediately after the updated `#chat-panel` rule (above `#messages`):

```css
#welcome {
  padding: 24px 20px 8px;
  border-bottom: 1px solid var(--border);
}
```

- [ ] **Step 5: Commit**

```bash
git add ui/static/style.css
git commit -m "style(ui): drop right-panel rules, widen chat to full width"
```

---

## Task 3: Delete tab-related JS and add welcome show/hide hooks

**Files:** Modify: `ui/static/app.js`

This task has the most surface area. Be careful: keep `enableSortableTable` and `renderMarkdown` — both still serve the left bubble.

- [ ] **Step 1: Delete module-level state**

Remove the lines:

```js
const TABS_KEY = 'iam_chat_tabs';
const MAX_TABS = 10;

let tabCount = 0;
```

Keep `HISTORY_KEY`. The header comment may be edited or left; if you tighten it, replace the original two-line comment block at the top of the file with:

```js
// Conversation history is persisted in sessionStorage so a refresh inside
// the same browser tab keeps the prior conversation visible.
```

- [ ] **Step 2: Delete `loadTabsState` and `saveTabsState`**

Remove both function definitions in their entirety.

- [ ] **Step 3: Delete the `#tab-bar` click handler**

Remove the entire block starting with `// Delegated tab-bar click handler` and ending at the closing `});` of `document.getElementById('tab-bar').addEventListener('click', …)`.

- [ ] **Step 4: Delete `openResultsTab`, `activateTab`, `deriveTabLabel`**

Remove all three function definitions.

- [ ] **Step 5: Delete `restoreTabs`**

Remove the entire `function restoreTabs() { … }` definition.

- [ ] **Step 6: Remove all `resultPane` mentions and tab-side calls inside `sendMessage`**

In `sendMessage`, find:

```js
  let buffer = '';
  let resultPane = null;
```

Replace with:

```js
  let buffer = '';
```

Inside the `[DONE]` branch, find:

```js
        if (payload === '[DONE]') {
          // Finalize
          aiEl.querySelector('.cursor')?.remove();
          history.push({ role: 'assistant', content: buffer });
          saveHistory(history);

          if (resultPane) renderMarkdown(resultPane, buffer);
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
          streamDone = true;
          break;
        }
```

Inside the chunk loop, find:

```js
        // Open a results tab on first chunk
        if (resultPane === null) {
          resultPane = openResultsTab('…');
        }
```

Delete those four lines entirely.

After the read loop, find:

```js
    // Update tab label once we have the full response
    if (resultPane) {
      const label = deriveTabLabel(buffer);
      const activeTab = document.querySelector('.tab.active');
      if (activeTab && activeTab.id !== 'tab-welcome') {
        activeTab.textContent = label;
      }
      renderMarkdown(resultPane, buffer);
      saveTabsState();
    }

    // Re-render the left chat bubble with markdown now that streaming is done.
    // During streaming we appended plain text to avoid mid-parse layout flicker.
    renderMarkdown(aiEl, buffer);
```

Replace with:

```js
    // Re-render the left chat bubble with markdown now that streaming is done.
    // During streaming we appended plain text to avoid mid-parse layout flicker.
    renderMarkdown(aiEl, buffer);
```

- [ ] **Step 7: Add the welcome-removal hook at the top of `sendMessage`**

In `sendMessage`, find:

```js
async function sendMessage() {
  const input = document.getElementById('input');
  const text = input.value.trim();
  if (!text) return;
```

Replace with:

```js
async function sendMessage() {
  const input = document.getElementById('input');
  const text = input.value.trim();
  if (!text) return;

  document.getElementById('welcome')?.remove();
```

- [ ] **Step 8: Hide welcome on startup if history exists, and clean up old TABS_KEY**

At the bottom of the file, find:

```js
restoreChatMessages();
restoreTabs();
```

Replace with:

```js
// Drop the orphaned tab-state key from older versions; harmless if absent.
sessionStorage.removeItem('iam_chat_tabs');

if (loadHistory().length > 0) {
  document.getElementById('welcome')?.remove();
}

restoreChatMessages();
```

- [ ] **Step 9: Commit**

```bash
git add ui/static/app.js
git commit -m "feat(ui): drop tab JS, gate welcome on empty history"
```

---

## Task 4: Manual browser verification

**Files:** none modified.

Run through the spec's verification checklist. The reviewer (you) will start the server when ready.

- [ ] **Step 1: Start the app**

```bash
set -a && source .sapcli.env && set +a
conda run -n sapcli-env --no-capture-output uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

Open `http://localhost:8080`.

- [ ] **Step 2: Cold load**

Clear the browser's sessionStorage for the site (DevTools → Application → Storage → Clear). Reload.

Expected:
- Welcome block visible at the top of the chat panel with the three example queries.
- No right panel, no tab bar, no border between panels.
- Chat panel spans the full viewport.

- [ ] **Step 3: Send any query**

Send a message. Expected:
- Welcome block disappears immediately.
- Streaming replies into the left bubble; markdown renders after `[DONE]`.

- [ ] **Step 4: Refresh after one query**

Refresh the browser tab.

Expected:
- Conversation replays in the chat.
- Welcome stays gone (history is non-empty).

- [ ] **Step 5: DevTools Console + Storage**

Open DevTools.

Expected:
- Console clean — no `Cannot read properties of null` errors, no references to missing `#tab-bar` / `#results-panel`.
- Application → sessionStorage: `iam_chat_history` key present, `iam_chat_tabs` key absent.

- [ ] **Step 6: Sortable left-bubble table**

Send a query that returns a markdown table. Click a header. Expected: rows sort in the bubble.

- [ ] **Step 7: If anything fails**

Note the failure, jump to the offending Task, fix, re-commit, return here.

- [ ] **Step 8: Done**

No commit needed — this task is verification only.
