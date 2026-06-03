# Remove Right Results Panel — Design

**Date:** 2026-06-03
**Scope:** UI only — `ui/templates/index.html`, `ui/static/style.css`, `ui/static/app.js`
**Goal:** Delete the right-hand results/tab panel now that the left chat bubble fully renders markdown (sortable tables, code blocks, headings). Chat takes the full viewport. Welcome guidance moves into the chat area as a one-time greeting.

## Rationale

The 2026-06-03 left-chat-readability change made the left bubble a complete rendering surface — same `marked.parse` + `DOMPurify.sanitize`, same `enableSortableTable` binding. The right panel duplicates that output one-to-one with the only added value being a tabbed history of past queries. The user assessed the duplicated panel as not useful enough to keep; we remove it.

## Design

### What disappears

**HTML (`ui/templates/index.html`):** The entire `<div id="results-panel">` block (lines 39-58 of the current file), including `#tab-bar`, `#tab-content`, the welcome `.tab-pane`, and the welcome `<h2>`/`<p>`/`<ul>` content.

**CSS (`ui/static/style.css`):** All rules whose selector starts with `#results-panel`, `#tab-bar`, `.tab `, `.tab.`, `#tab-content`, `.tab-pane`. The `.welcome` block stays — we still use it to style the moved welcome content. The line `#chat-panel { width: 50% }` becomes `width: 100%`, and the `border-right` declaration is removed.

**JS (`ui/static/app.js`):** Delete the following symbols and their callers:

- module-level state: `TABS_KEY`, `MAX_TABS`, `tabCount`
- functions: `loadTabsState`, `saveTabsState`, `openResultsTab`, `activateTab`, `deriveTabLabel`, `restoreTabs`
- the `#tab-bar` delegated click handler
- the `restoreTabs()` invocation at the bottom of the file
- inside `sendMessage`: the `let resultPane = null;` declaration, `if (resultPane === null) { resultPane = openResultsTab('…'); }`, the `if (resultPane) renderMarkdown(resultPane, buffer);` inside the `[DONE]` branch, and the entire `if (resultPane) { ... renderMarkdown(resultPane, buffer); saveTabsState(); }` block after the read loop

What stays in `app.js`:
- `HISTORY_KEY`, `loadHistory`, `saveHistory`
- `appendUserMessage`, `appendAIMessageEl`, `scrollToBottom`
- `enableSortableTable`, `renderMarkdown` (still used by left bubble)
- `restoreChatMessages` and its bottom-of-file invocation
- the existing left-bubble `renderMarkdown(aiEl, buffer)` call after the read loop
- input keydown / textarea autosize handlers

### What appears (welcome content)

The example queries currently shown inside the right-panel `.welcome` block are useful first-run guidance. Move them inside `#chat-panel` above `#messages`:

```html
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
  <div id="input-bar">…</div>
</div>
```

The `#welcome` element should:
- be visible only when chat history is empty (no prior turns)
- hide itself the moment the first user message is sent

JS hook: at the top of `sendMessage()` (before any other side-effect), call `document.getElementById('welcome')?.remove()`. On startup, if `loadHistory().length > 0`, also remove the welcome element. Removal (vs. `display: none`) is simpler and there's no scenario where it should reappear in the same session.

### CSS for the new layout

```css
#chat-panel {
  width: 100%;
  display: flex; flex-direction: column;
  background: var(--bg);
}
#welcome {
  padding: 24px 20px 8px;
  border-bottom: 1px solid var(--border);
}
```

Existing `.welcome` rules (`max-width`, `h2`, `p,li`, `ul`) keep working. We narrow the `.welcome` width via the existing `max-width: 480px`; with the chat panel now 100% wide, that just centers/limits the text — fine.

### localStorage / sessionStorage cleanup

The old `iam_chat_tabs` key (the `TABS_KEY`) becomes orphaned in users' sessionStorage. On startup, do `sessionStorage.removeItem('iam_chat_tabs')` once to free the slot. Not load-blocking — purely tidy.

### Dependencies

`marked` and `DOMPurify` are still required (left bubble uses them). The `<script src=...marked...>` and `<script src=...purify...>` tags in `index.html` stay.

## Out of Scope

- Adding a "history sidebar" or alternative way to revisit past queries — the chat scrollback is now the single source.
- Restyling the welcome text beyond placing it.
- Changing the streaming behaviour or markdown rules from the prior change.
- Removing `enableSortableTable` (still useful inside left-bubble tables).

## Verification

After implementation, manually in a browser:

1. Cold load: `#welcome` shows the greeting and three example queries above the message area.
2. Send any query: welcome disappears immediately and never returns this session.
3. Reload after one query: history replays in the chat; welcome stays gone.
4. The chat panel spans the full viewport width — no right panel, no border-right, no tab bar visible.
5. Markdown rendering, sortable tables, and history replay still work in the left bubble.
6. DevTools Console is clean — no errors about missing `#tab-bar` / `#results-panel` / undefined references.
7. DevTools sessionStorage: no `iam_chat_tabs` key after first load.
