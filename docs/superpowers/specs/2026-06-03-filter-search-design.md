# Filter Search — Design

**Date:** 2026-06-03
**Scope:** UI only — `ui/templates/index.html`, `ui/static/style.css`, `ui/static/app.js`
**Goal:** Add two client-side text filters: a search box at the top of the sidebar that filters the session list, and a search box above the welcome cards that filters prompt templates. Both perform a case-insensitive substring match and re-render in place; no backend involvement.

## Rationale

As session and template counts grow, scrolling becomes the dominant cost of "find the thing I want". A 30-line input + a re-render on each keystroke removes that cost. We do not yet need fuzzy matching, regex, or scoping operators — substring is enough.

Chat-message search is intentionally NOT in scope: the browser's built-in Cmd+F covers most of that need, and adding our own would entangle with the existing markdown render pipeline.

## UI

### Sidebar search

A new input row sits between `+ New` and `#session-list`:

```
┌───────────────┐
│ + New         │
├───────────────┤
│ 🔍 Search…    │  ← new input, persists no state
├───────────────┤
│ Treasury app …│  ← session-list, filtered live
│ SoD scan …    │
└───────────────┘
```

- Input element id: `#sidebar-search`.
- Placeholder: `Search sessions…`.
- Typing fires the `input` event; we re-render the session list with rows whose `title` contains the lowercased search term (case-insensitive).
- Clearing the input restores the full list.
- The input is **not** persisted to storage — refresh resets it. Within a single page lifetime the input keeps its value across session switches (the search box stays put in the DOM). Acceptable trade-off; resetting on switch would require an explicit clear that the user almost certainly does not want.
- An `×` clear button appears inside the input (right side) when the input has text. Clicking it clears the value and re-renders.

When the filter eliminates all rows, an empty-state row reads `No sessions match "<query>"`.

### Welcome (templates) search

A new input row sits above the category cards, inside `#welcome-templates` but always visible at the top — the cards themselves are filtered:

```
┌─────────────────────────────────────┐
│ Pick a template to start, or type   │
│ your own question.                  │
│                                     │
│ 🔍 Filter templates…                │
│                                     │
│ GETTING STARTED                     │
│ [card] [card] …                     │
│ GENERAL                             │
│ ...                                 │
└─────────────────────────────────────┘
```

- Input element id: `#templates-search`.
- Placeholder: `Filter templates…`.
- Match against the lowercased concatenation of `title` and `prompt`. Both built-in and custom templates participate.
- Categories with zero matching templates are hidden entirely (heading + grid). The `+ Add template` card stays visible regardless of the filter — it's an action, not a template.
- An `×` clear button mirrors the sidebar search.
- Welcome search is also not persisted.
- The welcome **add/edit form** (when shown instead of cards) does NOT show the search input — search only appears in the cards-mode view.

### Visual

Both inputs use the same compact dark styling: `--surface` background, `--border` border, `--text` foreground, font-size 12px, slight padding, rounded 6px. The 🔍 prefix is a `padding-left` + a CSS `::before` pseudo-element with a Unicode glyph (no SVG, no icon font).

## Implementation

### Sidebar

`renderSidebar()` becomes:

1. Read input value (if input exists in DOM yet) and lowercase + trim.
2. Filter `Sessions.list()` by `title.toLowerCase().includes(query)`.
3. Render rows from the filtered list as today.
4. If filtered list is empty AND the query is non-empty, append an empty-state element.

We rebuild the entire `#session-list` on every keystroke. This is O(N) per keystroke for N sessions; for any realistic N this is invisible.

The search input lives in the DOM permanently (in `index.html`, not re-created), so its current value survives every `renderSidebar()` call. We re-attach the listener once at startup.

### Welcome

`populateWelcomeTemplates(container)` extension:

1. Append the search input as the first child of `container` (after clearing).
2. Wire its `input` listener once: each keystroke calls a local `applyFilter()` that walks the cards already in DOM and toggles `display: none` per card and per `.welcome-cards` container with no visible cards (and the heading above).
3. Cards visibility logic: a card matches if `(title + ' ' + prompt).toLowerCase().includes(query)`. The Add card always stays visible.

Since the cards are static (only re-render on add/edit/delete), filtering by toggling display avoids rebuilding DOM on each keystroke.

### Storage / cross-session behavior

Neither query is persisted. Switching sessions, refreshing, opening a new tab — all reset filters to empty. This keeps state minimal and matches user expectation that a search box is ephemeral.

## File-level changes

### `ui/templates/index.html`

Add a sidebar input row inside `<aside id="sidebar">` between the `+ New` button and `#session-list`:

```html
<aside id="sidebar">
  <button id="sidebar-new-btn" type="button">+ New</button>
  <div id="sidebar-search-wrap">
    <input id="sidebar-search" type="text" placeholder="Search sessions…" />
    <button id="sidebar-search-clear" type="button" title="Clear" hidden>×</button>
  </div>
  <div id="session-list"></div>
</aside>
```

The welcome search input is created in JS (inside `populateWelcomeTemplates`) since the `<template>` block is cloned each time; baking it into the `<template>` would also work but JS-side keeps the single source of truth for what `populateWelcomeTemplates` controls.

### `ui/static/style.css`

Add `#sidebar-search-wrap`, `#sidebar-search`, `#sidebar-search-clear`, `.sidebar-empty`, `.welcome-search-wrap`, `.welcome-search`, `.welcome-search-clear` rules. The two search inputs share most styling.

### `ui/static/app.js`

- Extend `renderSidebar()` to read the search query and filter rows.
- Wire `#sidebar-search` and `#sidebar-search-clear` once at startup, near the `#sidebar-new-btn` listener block.
- Extend `populateWelcomeTemplates(container)` to inject the search input and wire its listener; add internal `applyTemplateFilter()` that toggles `display`.

## Out of Scope

- Chat content search (deferred per discussion).
- Fuzzy matching / typo tolerance.
- Regex or operator syntax (`category:`, `tag:`, etc.).
- Highlighting matched substrings within rows/cards.
- Search history, recent queries, or autocomplete.
- Persisting the query across reloads / sessions / tabs.
- Keyboard shortcuts (Cmd+K to focus search, etc.).

## Verification

1. **Cold load**: sidebar shows the search input above the session list; placeholder reads `Search sessions…`. Welcome cards-view shows `Filter templates…` between the intro line and the first category heading.
2. **Type in sidebar search**: only sessions whose title contains the query (case-insensitive) remain visible. Active row stays correctly highlighted IF its title still matches; if not, the active row is hidden but `Sessions.getActive()` is unchanged.
3. **Type a non-matching query in sidebar**: an empty-state line `No sessions match "xyz"` appears.
4. **Clear sidebar input via × button**: full list returns; clear button hides itself.
5. **Type in templates search**: matching cards stay visible; non-matching cards hide; categories with zero visible cards (heading + grid) hide. The Add card stays visible at all times.
6. **Type a non-matching template query**: only the Add card remains visible (no empty-state needed — the Add card is always the action).
7. **Persistence**: refresh the page → both search inputs are empty. Switch sessions → both reset. Open a new tab → both empty.
8. **Add card behavior under filter**: typing a query with the form mode showing has no effect (form mode doesn't render the search).
9. **DevTools console clean** — no errors.
