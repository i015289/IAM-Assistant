# Left Chat Readability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render markdown in the left-hand chat bubble (currently plain text) and apply matching styles, so AI responses become readable for typical IAM answers (lists, tables, code blocks, inline tokens).

**Architecture:** Reuse the existing `renderMarkdown(pane, raw)` helper (`ui/static/app.js:155`) for the left chat bubble at two call sites — stream-completion and history-replay. Add markdown child-element styles scoped under `.msg-ai` in `ui/static/style.css`. Widen the chat panel from 42% to 50% and the AI bubble max-width from 90% to 95%.

**Tech Stack:** Vanilla JS, `marked` + `DOMPurify` (already loaded), plain CSS.

**Reference spec:** `docs/superpowers/specs/2026-06-03-left-chat-readability-design.md`

**Testing approach:** No JS unit tests exist for the UI layer in this repo. Verification is manual visual inspection in a browser per §Verification of the spec — this is documented in the final task.

---

## File Structure

- **Modify** `ui/static/style.css` — replace the `.msg-ai` rule, add `.msg-ai` child-element styles, widen `#chat-panel` and `.msg-ai-wrap`.
- **Modify** `ui/static/app.js` — add `renderMarkdown(aiEl, buffer)` after the existing right-pane render call; replace `bubble.textContent = msg.content` in history replay with `renderMarkdown(bubble, msg.content)`.

No new files. No test files. Two files touched, ~70 LOC of CSS added/replaced, 2 LOC of JS changed.

---

## Task 1: Render markdown in the left chat bubble after stream completion

**Files:**
- Modify: `ui/static/app.js:262`

This is the smallest possible JS change — one new line. We do it first so that even before the CSS is in place, you can confirm the markdown HTML is being produced (it will look ugly without styles, but headings/lists/tables will at least appear as semantic HTML).

- [ ] **Step 1: Read context around the call site**

Open `ui/static/app.js` and read lines 250-265 to confirm the surrounding code matches the plan. The existing block ends with `renderMarkdown(resultPane, buffer);` followed by `saveTabsState();`.

- [ ] **Step 2: Add the left-bubble render call**

In `ui/static/app.js`, after line 262 (`renderMarkdown(resultPane, buffer);`), add a call to render markdown into the left chat bubble too.

Find:
```js
      renderMarkdown(resultPane, buffer);
      saveTabsState();
    }
```

Replace with:
```js
      renderMarkdown(resultPane, buffer);
      saveTabsState();
    }

    // Re-render the left chat bubble with markdown now that streaming is done.
    // During streaming we appended plain text to avoid mid-parse layout flicker.
    renderMarkdown(aiEl, buffer);
```

The `renderMarkdown` call replaces the bubble's `innerHTML`, which removes the streaming cursor (`<span class="cursor">`) automatically — no extra cleanup needed.

Note: `renderMarkdown` also calls `enableSortableTable` on every rendered `<table>`, so left-bubble tables become sortable for free.

- [ ] **Step 3: Manual smoke test**

1. Run the app (`./install.sh` or however the project starts; check README if unsure).
2. Send a query that produces markdown (e.g. ask about a Treasury BRT).
3. Confirm the left bubble after streaming shows real headings, lists, tables — not raw `#` and `|` characters.

Expected: Markdown elements render but are unstyled (no spacing, no colours) — that's fine, Task 3 fixes styling.

- [ ] **Step 4: Commit**

```bash
git add ui/static/app.js
git commit -m "feat(ui): render markdown in left chat bubble after stream completion"
```

---

## Task 2: Render markdown when replaying chat history

**Files:**
- Modify: `ui/static/app.js:300`

History replay (`restoreChatMessages`) currently writes `textContent`, so a page refresh wipes formatting. Same fix as Task 1, different call site.

- [ ] **Step 1: Locate the history-replay block**

In `ui/static/app.js`, find the loop in `restoreChatMessages` around lines 285-305. The relevant assistant branch ends with:

```js
      const bubble = document.createElement('div');
      bubble.className = 'msg-ai';
      bubble.textContent = msg.content;
      wrap.appendChild(avatar);
      wrap.appendChild(bubble);
      messagesEl.appendChild(wrap);
```

- [ ] **Step 2: Replace `textContent` with `renderMarkdown`**

Find:
```js
      const bubble = document.createElement('div');
      bubble.className = 'msg-ai';
      bubble.textContent = msg.content;
```

Replace with:
```js
      const bubble = document.createElement('div');
      bubble.className = 'msg-ai';
      renderMarkdown(bubble, msg.content);
```

`renderMarkdown` works on any element — it sets `innerHTML` from sanitised markdown and binds sortable tables.

- [ ] **Step 3: Manual smoke test**

1. Reload the running app (or restart, if needed) so a prior conversation is in localStorage.
2. Refresh the page.
3. Confirm replayed AI messages render markdown the same way live messages do.

Expected: refreshed history shows formatted markdown, not plain text.

- [ ] **Step 4: Commit**

```bash
git add ui/static/app.js
git commit -m "feat(ui): render markdown when replaying chat history"
```

---

## Task 3: Replace `.msg-ai` rule and add scoped markdown styles

**Files:**
- Modify: `ui/static/style.css:65-69`

Now the markdown is rendering, give it visual structure. All new selectors are scoped under `.msg-ai` so the right-hand `#tab-pane` styles are untouched.

- [ ] **Step 1: Locate the existing `.msg-ai` rule**

In `ui/static/style.css`, find lines 65-69:

```css
.msg-ai {
  background: var(--surface);
  border-radius: 2px 12px 12px 12px;
  padding: 10px 14px; line-height: 1.5;
}
```

- [ ] **Step 2: Replace the rule with the expanded block**

Replace those exact 5 lines with:

```css
.msg-ai {
  background: var(--surface);
  border: 1px solid #2a2b3d;
  border-radius: 2px 14px 14px 14px;
  padding: 14px 16px;
  font-size: 14.5px;
  line-height: 1.7;
}
.msg-ai > :first-child { margin-top: 0; }
.msg-ai > :last-child  { margin-bottom: 0; }

.msg-ai h1, .msg-ai h2, .msg-ai h3 {
  color: var(--accent); font-size: 13px; font-weight: 700;
  margin: 14px 0 6px; letter-spacing: 0.02em;
}
.msg-ai p  { margin: 0 0 10px; }
.msg-ai ul, .msg-ai ol { padding-left: 20px; margin: 0 0 10px; }
.msg-ai li { margin: 3px 0; }
.msg-ai strong { color: #f5e0dc; }

.msg-ai code {
  background: var(--border); padding: 1px 5px; border-radius: 3px;
  font-size: 12.5px; font-family: ui-monospace, monospace; color: var(--amber);
}
.msg-ai pre {
  background: #11111b; border: 1px solid #2a2b3d;
  padding: 10px 12px; border-radius: 6px; overflow-x: auto;
  margin: 8px 0 12px;
}
.msg-ai pre code { background: none; padding: 0; color: var(--text); font-size: 12px; }

.msg-ai table { width: 100%; border-collapse: collapse; font-size: 12.5px; margin: 6px 0 10px; }
.msg-ai th { text-align: left; padding: 6px 8px; color: var(--accent);
             font-weight: 600; border-bottom: 1px solid var(--border); }
.msg-ai td { padding: 6px 8px; border-bottom: 1px solid var(--bg); }
```

Note: `#2a2b3d` is a one-off colour between `--surface` (#181825) and `--border` (#313244). It's used twice (bubble border + `pre` border); keep it inline rather than promoting to a CSS variable to avoid `:root` noise.

- [ ] **Step 3: Manual smoke test**

1. Hard-reload the running app (cache may hold the old CSS).
2. Send a query that produces headings, list, table, and inline `code`.
3. Confirm:
   - Bubble has a thin border, slightly softer corners, more padding.
   - Headings are accent-blue and tighter.
   - Inline `code` is amber on dark background.
   - Code block has its own darker background and border.
   - Table has accent-coloured header cells.

- [ ] **Step 4: Commit**

```bash
git add ui/static/style.css
git commit -m "style(ui): scope markdown styles to left chat bubble"
```

---

## Task 4: Widen the chat panel and AI-bubble max-width

**Files:**
- Modify: `ui/static/style.css:44`
- Modify: `ui/static/style.css:59`

Two single-value changes so long answers, tables, and code blocks have room to breathe.

- [ ] **Step 1: Widen `#chat-panel`**

In `ui/static/style.css`, find:

```css
#chat-panel {
  width: 42%;
```

Replace `width: 42%;` with `width: 50%;`. The full block becomes:

```css
#chat-panel {
  width: 50%;
  border-right: 1px solid var(--border);
  display: flex; flex-direction: column;
  background: var(--bg);
}
```

- [ ] **Step 2: Widen `.msg-ai-wrap` max-width**

In `ui/static/style.css`, find:

```css
.msg-ai-wrap { align-self: flex-start; display: flex; gap: 8px; max-width: 90%; }
```

Replace `max-width: 90%` with `max-width: 95%`:

```css
.msg-ai-wrap { align-self: flex-start; display: flex; gap: 8px; max-width: 95%; }
```

`.msg-user` (max-width 85%) is intentionally left alone — short user prompts benefit from the right-aligned offset more than from extra width.

- [ ] **Step 3: Manual smoke test**

1. Hard-reload the running app.
2. On a typical 1440px display, confirm:
   - The left chat panel and right results panel each take roughly half the viewport.
   - A query that produces a wide markdown table renders without horizontal scroll inside the bubble.

- [ ] **Step 4: Commit**

```bash
git add ui/static/style.css
git commit -m "style(ui): widen chat panel to 50% and AI bubble to 95%"
```

---

## Task 5: Final verification against the spec

**Files:** none modified.

Run through the spec's verification checklist (`docs/superpowers/specs/2026-06-03-left-chat-readability-design.md` §Verification) end-to-end on a clean reload.

- [ ] **Step 1: IAM query producing all markdown elements**

Send an IAM question that yields all of: heading, bullet list, numbered list, table, fenced SQL block, inline `code`, and `**strong**` text. (Example: "Summarise SAP_BR_TREASURY_SPECIALIST_FOE — list catalogs as bullets, auth objects as a table, and include a sample SQL query.")

Expected: every markdown element renders styled in the left bubble.

- [ ] **Step 2: History replay**

Refresh the page. Expected: replayed AI messages render the same way live ones did, not as plain text.

- [ ] **Step 3: Error path unaffected**

Trigger an error (e.g. send a message while the MCP server is down). Expected: the `.msg-error` span renders as plain red text — no markdown rendering, no crash.

- [ ] **Step 4: Layout**

On a typical desktop window, confirm the chat panel occupies ~50% of viewport width and that wide tables render inside the bubble without horizontal scroll.

- [ ] **Step 5: Sortable left-bubble tables (bonus check)**

Click a table header in a left-bubble table. Expected: rows sort (this comes for free from `enableSortableTable` inside `renderMarkdown`).

- [ ] **Step 6: If anything fails**

Note the failure, jump back to the relevant Task, fix, recommit. Then return here.

- [ ] **Step 7: Done**

No commit needed — this task is verification only.
