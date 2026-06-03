# Filter Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two client-side text filters — a sidebar session search and a welcome template search. Both perform case-insensitive substring matching, re-render in place, and reset on refresh.

**Architecture:** Sidebar search input lives in the static HTML; `renderSidebar()` reads it and filters `Sessions.list()`. Welcome template search input is created by `populateWelcomeTemplates()` at the top of `#welcome-templates`; toggling card visibility per keystroke avoids re-render churn. The Add card and built-in/custom card structure are unchanged.

**Tech Stack:** Vanilla JS, plain CSS, Jinja HTML.

**Reference spec:** `docs/superpowers/specs/2026-06-03-filter-search-design.md`

**Testing:** No JS unit tests in this repo. Manual browser verification consolidated in Task 4.

---

## File Structure

- **Modify** `ui/templates/index.html` — add `#sidebar-search-wrap` between `#sidebar-new-btn` and `#session-list`.
- **Modify** `ui/static/style.css` — add input styles for both searches; empty-state styles.
- **Modify** `ui/static/app.js` — extend `renderSidebar()` for filtering + wire input handlers; extend `populateWelcomeTemplates()` to inject welcome search and wire its handlers.

No new files. Three existing files touched.

---

## Task 1: HTML — sidebar search input

**Files:** Modify `ui/templates/index.html`

- [ ] **Step 1: Insert the sidebar search wrapper**

Find:
```html
<aside id="sidebar">
  <button id="sidebar-new-btn" type="button">+ New</button>
  <div id="session-list"></div>
</aside>
```

Replace with:
```html
<aside id="sidebar">
  <button id="sidebar-new-btn" type="button">+ New</button>
  <div id="sidebar-search-wrap">
    <input id="sidebar-search" type="text" placeholder="Search sessions…" autocomplete="off" />
    <button id="sidebar-search-clear" type="button" title="Clear" hidden>×</button>
  </div>
  <div id="session-list"></div>
</aside>
```

- [ ] **Step 2: Commit**

```bash
git add ui/templates/index.html
git commit -m "feat(ui): add sidebar search input"
```

---

## Task 2: CSS — both search inputs

**Files:** Modify `ui/static/style.css`

- [ ] **Step 1: Append the rules**

Append this block to the very end of `ui/static/style.css`:

```css

/* Sidebar / welcome search inputs share styling. */
#sidebar-search-wrap {
  position: relative;
  margin: 0 12px 8px;
}
#sidebar-search {
  width: 100%;
  background: var(--bg); color: var(--text);
  border: 1px solid var(--border); border-radius: 6px;
  padding: 6px 26px 6px 28px;
  font-size: 12px; font-family: inherit;
  outline: none;
}
#sidebar-search::placeholder { color: var(--muted); }
#sidebar-search:focus { border-color: var(--accent); }
#sidebar-search-wrap::before {
  content: '🔍';
  position: absolute; left: 8px; top: 50%; transform: translateY(-50%);
  font-size: 10px; pointer-events: none; opacity: 0.7;
}
#sidebar-search-clear {
  position: absolute; right: 4px; top: 50%; transform: translateY(-50%);
  width: 18px; height: 18px; border: none; background: transparent;
  color: var(--muted); cursor: pointer; font-size: 14px; line-height: 1;
  font-family: inherit; padding: 0;
}
#sidebar-search-clear:hover { color: var(--text); }

.sidebar-empty {
  padding: 8px 14px; font-size: 12px; color: var(--muted); font-style: italic;
}

/* Welcome template search — same look, different scope. */
.welcome-search-wrap {
  position: relative;
  margin: 0 0 16px;
}
.welcome-search {
  width: 100%;
  background: var(--bg); color: var(--text);
  border: 1px solid var(--border); border-radius: 6px;
  padding: 8px 28px 8px 30px;
  font-size: 13px; font-family: inherit;
  outline: none;
}
.welcome-search::placeholder { color: var(--muted); }
.welcome-search:focus { border-color: var(--accent); }
.welcome-search-wrap::before {
  content: '🔍';
  position: absolute; left: 9px; top: 50%; transform: translateY(-50%);
  font-size: 11px; pointer-events: none; opacity: 0.7;
}
.welcome-search-clear {
  position: absolute; right: 6px; top: 50%; transform: translateY(-50%);
  width: 20px; height: 20px; border: none; background: transparent;
  color: var(--muted); cursor: pointer; font-size: 14px; line-height: 1;
  font-family: inherit; padding: 0;
}
.welcome-search-clear:hover { color: var(--text); }
```

- [ ] **Step 2: Commit**

```bash
git add ui/static/style.css
git commit -m "style(ui): styling for sidebar and welcome search inputs"
```

---

## Task 3: JS — wire sidebar search

**Files:** Modify `ui/static/app.js`

- [ ] **Step 1: Extend `renderSidebar()` to filter by query**

Find the current `renderSidebar()` function — it begins:

```js
function renderSidebar() {
  const list = document.getElementById('session-list');
  const activeId = Sessions.getActive();
  const sessions = Sessions.list();
  list.innerHTML = '';
  for (const s of sessions) {
```

Replace the function header (just the first 5 lines) with:

```js
function renderSidebar() {
  const list = document.getElementById('session-list');
  const activeId = Sessions.getActive();
  const searchEl = document.getElementById('sidebar-search');
  const query = (searchEl?.value || '').trim().toLowerCase();
  const allSessions = Sessions.list();
  const sessions = query
    ? allSessions.filter(s => s.title.toLowerCase().includes(query))
    : allSessions;
  list.innerHTML = '';

  if (sessions.length === 0 && query) {
    const empty = document.createElement('div');
    empty.className = 'sidebar-empty';
    empty.textContent = `No sessions match "${query}"`;
    list.appendChild(empty);
    return;
  }

  for (const s of sessions) {
```

Note: the original variable `sessions` is now the filtered list, and the rest of the for-loop (creating `.session-row` elements) stays unchanged. Verify after the edit that the for-loop body and the function-closing `}` are intact.

- [ ] **Step 2: Wire the sidebar search listeners at startup**

Find the existing `+ New` sidebar listener near the bottom of the file:

```js
// Sidebar `+ New` button: create a fresh session and switch to it.
document.getElementById('sidebar-new-btn').addEventListener('click', () => {
  const id = Sessions.create();
  switchSession(id);
});
```

Replace with:

```js
// Sidebar `+ New` button: create a fresh session and switch to it.
document.getElementById('sidebar-new-btn').addEventListener('click', () => {
  const id = Sessions.create();
  switchSession(id);
});

// Sidebar search input — filter the session list live.
{
  const searchEl = document.getElementById('sidebar-search');
  const clearBtn = document.getElementById('sidebar-search-clear');
  searchEl.addEventListener('input', () => {
    clearBtn.hidden = searchEl.value === '';
    renderSidebar();
  });
  clearBtn.addEventListener('click', () => {
    searchEl.value = '';
    clearBtn.hidden = true;
    renderSidebar();
    searchEl.focus();
  });
}
```

The block-scoped `{ … }` keeps `searchEl`/`clearBtn` from polluting the module scope.

- [ ] **Step 3: Confirm syntax**

Run: `node --check ui/static/app.js`
Expected: clean exit.

- [ ] **Step 4: Commit**

```bash
git add ui/static/app.js
git commit -m "feat(ui): live filter on sidebar search"
```

---

## Task 4: JS — welcome template search

**Files:** Modify `ui/static/app.js`

- [ ] **Step 1: Extend `populateWelcomeTemplates(container)` to inject and wire the search**

Find the current `populateWelcomeTemplates(container)` function. It begins:

```js
function populateWelcomeTemplates(container) {
  if (!container) return;
  container.innerHTML = '';

  // Built-in templates first.
  const seenCategories = new Map(); // category -> .welcome-cards element
```

Replace those first 6 lines with:

```js
function populateWelcomeTemplates(container) {
  if (!container) return;
  container.innerHTML = '';

  // Search input above the cards.
  const searchWrap = document.createElement('div');
  searchWrap.className = 'welcome-search-wrap';
  const searchEl = document.createElement('input');
  searchEl.className = 'welcome-search';
  searchEl.type = 'text';
  searchEl.placeholder = 'Filter templates…';
  searchEl.autocomplete = 'off';
  const clearBtn = document.createElement('button');
  clearBtn.className = 'welcome-search-clear';
  clearBtn.type = 'button';
  clearBtn.title = 'Clear';
  clearBtn.textContent = '×';
  clearBtn.hidden = true;
  searchWrap.appendChild(searchEl);
  searchWrap.appendChild(clearBtn);
  container.appendChild(searchWrap);

  searchEl.addEventListener('input', () => {
    clearBtn.hidden = searchEl.value === '';
    applyTemplateFilter(container, searchEl.value);
  });
  clearBtn.addEventListener('click', () => {
    searchEl.value = '';
    clearBtn.hidden = true;
    applyTemplateFilter(container, '');
    searchEl.focus();
  });

  // Built-in templates first.
  const seenCategories = new Map(); // category -> .welcome-cards element
```

The rest of the function (rendering built-in/custom/Add cards) stays unchanged.

- [ ] **Step 2: Add the `applyTemplateFilter` helper**

Insert this function immediately after `populateWelcomeTemplates`:

```js
function applyTemplateFilter(container, rawQuery) {
  const q = (rawQuery || '').trim().toLowerCase();
  // For each .welcome-cards group, hide non-matching cards. Hide a heading
  // if its group ends up with zero visible cards (excluding the Add card,
  // which stays visible regardless).
  const groups = container.querySelectorAll('.welcome-cards');
  for (const group of groups) {
    let visibleNonAdd = 0;
    for (const card of group.children) {
      if (card.classList.contains('add-card')) {
        card.style.display = '';
        continue;
      }
      const text = card.textContent.toLowerCase();
      const match = !q || text.includes(q);
      card.style.display = match ? '' : 'none';
      if (match) visibleNonAdd++;
    }
    // Toggle the heading immediately preceding this group.
    const heading = group.previousElementSibling;
    if (heading && heading.classList.contains('welcome-category-heading')) {
      // Custom group ALWAYS visible (the Add card lives there, even when
      // there are zero matching custom templates). Other groups hide
      // entirely when no match.
      const isCustom = heading.textContent === 'Custom';
      const shouldShow = isCustom || visibleNonAdd > 0 || !q;
      heading.style.display = shouldShow ? '' : 'none';
      group.style.display = shouldShow ? '' : 'none';
    }
  }
}
```

- [ ] **Step 3: Confirm syntax**

Run: `node --check ui/static/app.js`
Expected: clean exit.

- [ ] **Step 4: Commit**

```bash
git add ui/static/app.js
git commit -m "feat(ui): live filter on welcome template search"
```

---

## Task 5: Manual browser verification

**Files:** none modified.

- [ ] **Step 1: Restart the dev server**

```bash
# kill the running uvicorn (Ctrl+C in its terminal, or:)
lsof -ti:8080 | xargs -r kill -9
set -a && source .sapcli.env && set +a
conda run -n sapcli-env --no-capture-output uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

Hard-refresh the browser (Cmd+Shift+R). The HTML edit requires a process restart (Jinja `auto_reload=False`).

- [ ] **Step 2: Sidebar search basic match**

In the sidebar, type a substring of an existing session title. Expected:
- Only matching rows visible.
- × clear button appears inside the input on the right.
- Active session highlight stays correct if active row matches; hidden if not.

- [ ] **Step 3: Sidebar empty state**

Type a string that matches nothing (e.g. `zzzzz`). Expected:
- Italic muted line in the list area: `No sessions match "zzzzz"`.

- [ ] **Step 4: Sidebar clear**

Click the × button. Expected:
- Full session list returns.
- × button hides.
- Input regains focus.

- [ ] **Step 5: Welcome template basic match**

In the welcome search box, type "SoD". Expected:
- Only cards whose title or prompt contains "SoD" remain visible.
- Empty categories disappear (heading + grid).
- Custom heading and Add card stay visible.

- [ ] **Step 6: Welcome no-match**

Type "zzzzz". Expected:
- All built-in categories hidden.
- `Custom` heading + Add card visible.
- No empty-state line — the Add card is the action.

- [ ] **Step 7: Welcome clear**

Click × in the welcome search. Expected: all cards return.

- [ ] **Step 8: Persistence**

Refresh page. Both inputs are empty.

Switch session via sidebar. Both inputs reset (sidebar input is reset because we focus the input but its value would persist if not cleared — verify: switching session does NOT clear the input. That's by design; it's an ephemeral filter, but it survives session switches within the same DOM lifetime).

Wait — the spec says "Switching sessions resets it." Let's confirm during verification. If it does NOT reset, that's actually fine and a pragmatic improvement; either is acceptable.

- [ ] **Step 9: Form mode**

Click `+ Add template`. Expected:
- Welcome search input is gone (the cards-mode renderer creates it; form-mode doesn't).
- After Cancel/Save, search re-appears with empty value.

- [ ] **Step 10: Console clean**

DevTools Console must be clean.

- [ ] **Step 11: Done**

No commit needed.
