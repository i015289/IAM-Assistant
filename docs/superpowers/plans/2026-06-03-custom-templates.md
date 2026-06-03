# Custom Prompt Templates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users save, edit, and delete their own prompt templates from the welcome card grid (localStorage; `Custom` category; built-in templates remain read-only).

**Architecture:** Add a `UserTemplates` module to `app.js` that owns localStorage I/O. Extend `populateWelcomeTemplates` to render a final `Custom` group with user templates + an `Add template` card. Add a `renderWelcomeForm` function that swaps the welcome cards for an inline form (Title, Prompt, Save/Cancel). Card hover surfaces edit/delete buttons; built-in cards never get them.

**Tech Stack:** Vanilla JS, plain CSS, no HTML changes.

**Reference spec:** `docs/superpowers/specs/2026-06-03-custom-templates-design.md`

**Testing:** No JS unit tests in this repo. Manual browser verification consolidated in Task 4.

---

## File Structure

- **Modify** `ui/static/app.js` — add `UserTemplates` module; extend `populateWelcomeTemplates`; add `renderWelcomeForm`. ~120 LOC of new code.
- **Modify** `ui/static/style.css` — add `.welcome-card.custom` hover-button styles, `.welcome-card.add-card` dashed style, `.welcome-form` form styles. ~60 LOC.
- No HTML changes. No new files.

---

## Task 1: Add the `UserTemplates` storage module

**Files:** Modify `ui/static/app.js`

This task adds the storage abstraction in isolation. No UI rendering yet.

- [ ] **Step 1: Insert the module right after the `Sessions` module**

In `ui/static/app.js`, find the closing `};` of the `Sessions` module (around line 80, after the `setActive(id)` method). Insert the following block immediately after it:

```js
// User-created prompt templates, persisted to localStorage.
// Built-in templates live in window.PROMPT_TEMPLATES; user ones are appended
// at render time as a "Custom" category.
const USER_TEMPLATES_KEY = 'iam_user_templates';

const UserTemplates = {
  list() {
    try { return JSON.parse(localStorage.getItem(USER_TEMPLATES_KEY) || '[]'); }
    catch { return []; }
  },

  _write(list) {
    localStorage.setItem(USER_TEMPLATES_KEY, JSON.stringify(list));
  },

  create(title, prompt, { now = Date.now() } = {}) {
    const t = (title || '').trim();
    const p = (prompt || '').trim();
    if (!t) throw new Error('Title is required.');
    if (!p) throw new Error('Prompt is required.');
    if (t.length > 60) throw new Error('Title must be 60 chars or fewer.');
    if (p.length > 2000) throw new Error('Prompt must be 2000 chars or fewer.');
    const id = crypto.randomUUID().slice(0, 8);
    const list = UserTemplates.list();
    list.push({ id, title: t, prompt: p, createdAt: now });
    UserTemplates._write(list);
    return id;
  },

  update(id, title, prompt) {
    const t = (title || '').trim();
    const p = (prompt || '').trim();
    if (!t) throw new Error('Title is required.');
    if (!p) throw new Error('Prompt is required.');
    if (t.length > 60) throw new Error('Title must be 60 chars or fewer.');
    if (p.length > 2000) throw new Error('Prompt must be 2000 chars or fewer.');
    const list = UserTemplates.list();
    const idx = list.findIndex(x => x.id === id);
    if (idx < 0) return;
    list[idx] = { ...list[idx], title: t, prompt: p };
    UserTemplates._write(list);
  },

  delete(id) {
    const list = UserTemplates.list().filter(x => x.id !== id);
    UserTemplates._write(list);
  },
};
```

- [ ] **Step 2: Confirm syntax**

Run: `node --check ui/static/app.js`
Expected: clean exit.

- [ ] **Step 3: Commit**

```bash
git add ui/static/app.js
git commit -m "feat(ui): add UserTemplates localStorage module"
```

---

## Task 2: CSS for custom cards, add card, and form

**Files:** Modify `ui/static/style.css`

- [ ] **Step 1: Add the rules**

Append this block to the very end of `ui/static/style.css`:

```css
/* Custom welcome cards — edit/delete buttons revealed on hover. */
.welcome-card { position: relative; }
.welcome-card .card-actions {
  position: absolute; top: 6px; right: 6px;
  display: flex; gap: 2px;
  visibility: hidden;
}
.welcome-card.custom:hover .card-actions { visibility: visible; }
.welcome-card .card-action-btn {
  width: 22px; height: 22px;
  background: transparent; border: none; border-radius: 4px;
  color: var(--muted); cursor: pointer; font-size: 13px; line-height: 1;
  font-family: inherit;
}
.welcome-card .card-action-btn:hover { background: var(--bg); color: var(--text); }
.welcome-card .card-action-btn.delete:hover { color: var(--red); }

/* "+ Add template" card */
.welcome-card.add-card {
  border-style: dashed; color: var(--muted);
  align-items: center; justify-content: center;
  text-align: center; min-height: 64px;
}
.welcome-card.add-card:hover { color: var(--accent); border-color: var(--accent); }

/* Inline add/edit form (replaces the cards in #welcome-templates) */
.welcome-form { display: flex; flex-direction: column; gap: 12px; }
.welcome-form h3 {
  font-size: 13px; color: var(--text);
  text-transform: uppercase; letter-spacing: 0.08em;
  margin: 0;
}
.welcome-form label {
  font-size: 11px; color: var(--muted);
  text-transform: uppercase; letter-spacing: 0.06em;
  display: block; margin-bottom: 4px;
}
.welcome-form input[type="text"],
.welcome-form textarea {
  width: 100%; background: var(--surface); color: var(--text);
  border: 1px solid var(--border); border-radius: 6px;
  padding: 8px 10px; font-size: 13px; font-family: inherit;
  outline: none;
}
.welcome-form input[type="text"]:focus,
.welcome-form textarea:focus { border-color: var(--accent); }
.welcome-form textarea { min-height: 120px; resize: vertical; line-height: 1.5; }
.welcome-form-error {
  color: var(--red); font-size: 12px; min-height: 1em;
}
.welcome-form-actions {
  display: flex; justify-content: flex-end; gap: 8px;
}
.welcome-form-actions button {
  padding: 6px 14px; border-radius: 6px; border: 1px solid var(--border);
  font-size: 13px; font-family: inherit; cursor: pointer;
}
.welcome-form-actions .btn-secondary {
  background: transparent; color: var(--muted);
}
.welcome-form-actions .btn-secondary:hover { color: var(--text); }
.welcome-form-actions .btn-primary {
  background: var(--accent); color: var(--bg); border-color: var(--accent);
  font-weight: 600;
}
.welcome-form-actions .btn-primary:disabled {
  opacity: 0.4; cursor: default;
}
```

- [ ] **Step 2: Commit**

```bash
git add ui/static/style.css
git commit -m "style(ui): custom-card hover actions, add-card, inline form"
```

---

## Task 3: Render custom cards + add card + the form

**Files:** Modify `ui/static/app.js`

This task replaces the current `populateWelcomeTemplates` function with an extended version, then adds `renderWelcomeForm`.

- [ ] **Step 1: Replace `populateWelcomeTemplates`**

Find the current `populateWelcomeTemplates` function:

```js
function populateWelcomeTemplates(container) {
  if (!container || !Array.isArray(window.PROMPT_TEMPLATES)) return;
  const seenCategories = new Map(); // category -> .welcome-cards element
  for (const t of window.PROMPT_TEMPLATES) {
    let cards = seenCategories.get(t.category);
    if (!cards) {
      const heading = document.createElement('div');
      heading.className = 'welcome-category-heading';
      heading.textContent = t.category;
      container.appendChild(heading);
      cards = document.createElement('div');
      cards.className = 'welcome-cards';
      container.appendChild(cards);
      seenCategories.set(t.category, cards);
    }
    const card = document.createElement('button');
    card.type = 'button';
    card.className = 'welcome-card';
    const title = document.createElement('div');
    title.className = 'card-title';
    title.textContent = t.title;
    const sub = document.createElement('div');
    sub.className = 'card-subtitle';
    sub.textContent = t.prompt;
    card.appendChild(title);
    card.appendChild(sub);
    card.addEventListener('click', () => fillInputFromTemplate(t.prompt));
    cards.appendChild(card);
  }
}
```

Replace with:

```js
function populateWelcomeTemplates(container) {
  if (!container) return;
  container.innerHTML = '';

  // Built-in templates first.
  const seenCategories = new Map(); // category -> .welcome-cards element
  if (Array.isArray(window.PROMPT_TEMPLATES)) {
    for (const t of window.PROMPT_TEMPLATES) {
      const cards = ensureCategory(container, seenCategories, t.category);
      cards.appendChild(makeBuiltInCard(t));
    }
  }

  // Custom group — always shown so the "+ Add template" card is discoverable.
  const customCards = ensureCategory(container, seenCategories, 'Custom');
  for (const t of UserTemplates.list()) {
    customCards.appendChild(makeCustomCard(t, container));
  }
  customCards.appendChild(makeAddCard(container));
}

function ensureCategory(container, seenCategories, category) {
  let cards = seenCategories.get(category);
  if (cards) return cards;
  const heading = document.createElement('div');
  heading.className = 'welcome-category-heading';
  heading.textContent = category;
  container.appendChild(heading);
  cards = document.createElement('div');
  cards.className = 'welcome-cards';
  container.appendChild(cards);
  seenCategories.set(category, cards);
  return cards;
}

function makeBuiltInCard(t) {
  const card = document.createElement('button');
  card.type = 'button';
  card.className = 'welcome-card';
  const title = document.createElement('div');
  title.className = 'card-title';
  title.textContent = t.title;
  const sub = document.createElement('div');
  sub.className = 'card-subtitle';
  sub.textContent = t.prompt;
  card.appendChild(title);
  card.appendChild(sub);
  card.addEventListener('click', () => fillInputFromTemplate(t.prompt));
  return card;
}

function makeCustomCard(t, container) {
  const card = document.createElement('button');
  card.type = 'button';
  card.className = 'welcome-card custom';
  const title = document.createElement('div');
  title.className = 'card-title';
  title.textContent = t.title;
  const sub = document.createElement('div');
  sub.className = 'card-subtitle';
  sub.textContent = t.prompt;
  card.appendChild(title);
  card.appendChild(sub);

  const actions = document.createElement('div');
  actions.className = 'card-actions';
  const editBtn = document.createElement('button');
  editBtn.type = 'button';
  editBtn.className = 'card-action-btn edit';
  editBtn.title = 'Edit template';
  editBtn.textContent = '✎';
  editBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    renderWelcomeForm(container, t);
  });
  const delBtn = document.createElement('button');
  delBtn.type = 'button';
  delBtn.className = 'card-action-btn delete';
  delBtn.title = 'Delete template';
  delBtn.textContent = '×';
  delBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    if (!confirm(`Delete template "${t.title}"?`)) return;
    UserTemplates.delete(t.id);
    populateWelcomeTemplates(container);
  });
  actions.appendChild(editBtn);
  actions.appendChild(delBtn);
  card.appendChild(actions);

  card.addEventListener('click', () => fillInputFromTemplate(t.prompt));
  return card;
}

function makeAddCard(container) {
  const card = document.createElement('button');
  card.type = 'button';
  card.className = 'welcome-card add-card';
  card.textContent = '+ Add template';
  card.addEventListener('click', () => renderWelcomeForm(container, null));
  return card;
}

function renderWelcomeForm(container, existing) {
  container.innerHTML = '';
  const form = document.createElement('div');
  form.className = 'welcome-form';

  const heading = document.createElement('h3');
  heading.textContent = existing ? 'Edit template' : 'Add template';
  form.appendChild(heading);

  const titleLabel = document.createElement('label');
  titleLabel.textContent = 'Title';
  const titleInput = document.createElement('input');
  titleInput.type = 'text';
  titleInput.maxLength = 60;
  titleInput.value = existing ? existing.title : '';
  titleLabel.appendChild(titleInput);
  form.appendChild(titleLabel);

  const promptLabel = document.createElement('label');
  promptLabel.textContent = 'Prompt';
  const promptArea = document.createElement('textarea');
  promptArea.maxLength = 2000;
  promptArea.value = existing ? existing.prompt : '';
  promptLabel.appendChild(promptArea);
  form.appendChild(promptLabel);

  const errorEl = document.createElement('div');
  errorEl.className = 'welcome-form-error';
  form.appendChild(errorEl);

  const actions = document.createElement('div');
  actions.className = 'welcome-form-actions';
  const cancelBtn = document.createElement('button');
  cancelBtn.type = 'button';
  cancelBtn.className = 'btn-secondary';
  cancelBtn.textContent = 'Cancel';
  cancelBtn.addEventListener('click', () => populateWelcomeTemplates(container));
  const saveBtn = document.createElement('button');
  saveBtn.type = 'button';
  saveBtn.className = 'btn-primary';
  saveBtn.textContent = existing ? 'Save changes' : 'Save template';

  const updateSaveEnabled = () => {
    saveBtn.disabled = !titleInput.value.trim() || !promptArea.value.trim();
  };
  titleInput.addEventListener('input', updateSaveEnabled);
  promptArea.addEventListener('input', updateSaveEnabled);
  updateSaveEnabled();

  saveBtn.addEventListener('click', () => {
    try {
      if (existing) {
        UserTemplates.update(existing.id, titleInput.value, promptArea.value);
      } else {
        UserTemplates.create(titleInput.value, promptArea.value);
      }
      populateWelcomeTemplates(container);
    } catch (err) {
      errorEl.textContent = err.message;
    }
  });
  actions.appendChild(cancelBtn);
  actions.appendChild(saveBtn);
  form.appendChild(actions);

  container.appendChild(form);
  titleInput.focus();
}
```

- [ ] **Step 2: Confirm syntax**

Run: `node --check ui/static/app.js`
Expected: clean exit.

- [ ] **Step 3: Commit**

```bash
git add ui/static/app.js
git commit -m "feat(ui): render Custom group, add/edit/delete user templates"
```

---

## Task 4: Manual browser verification

**Files:** none modified.

- [ ] **Step 1: Restart the dev server**

```bash
set -a && source .sapcli.env && set +a
conda run -n sapcli-env --no-capture-output uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

Hard-refresh the browser. (`auto_reload=False` on the Jinja env means a full process restart is needed for HTML edits — but this plan touches no HTML, so a refresh alone may be enough; do a hard-refresh to be safe.)

- [ ] **Step 2: Cold load (no custom templates yet)**

DevTools → Application → Storage → Clear site data → reload.

Expected:
- Welcome shows 4 built-in headings + a 5th `Custom` heading.
- Under `Custom`, only the dashed `+ Add template` card.

- [ ] **Step 3: Add a template**

Click `+ Add template`. Expected: form replaces the cards. Save button is disabled.

Type "Quarterly audit" in Title and "List apps with both ACTVT 01 and 03 across all FOE catalogs." in Prompt. Save button enables. Click Save.

Expected: form closes, the new card appears under `Custom` before the `+ Add template` card.

- [ ] **Step 4: Click the new card**

Expected: input fills with the prompt text; no message sent.

- [ ] **Step 5: Hover the new card**

Expected: pencil and × buttons appear at top-right.

- [ ] **Step 6: Edit**

Click the pencil. Expected: form opens prefilled, heading reads `Edit template`.

Change the title to "Q4 SoD audit" and click Save changes. Expected: card title updates.

- [ ] **Step 7: Delete**

Hover the card → click ×. Confirm dialog → OK. Expected: card disappears; only `+ Add template` left under `Custom`.

Click Cancel on the confirm next time → card remains.

- [ ] **Step 8: Built-in cards have no edit/delete**

Hover a Treasury card. Expected: NO pencil or × buttons appear.

- [ ] **Step 9: Persistence**

Add 2 templates, refresh the browser. Expected: both still listed under `Custom`.

- [ ] **Step 10: Validation**

Click `+ Add template`, leave both fields empty. Save button is disabled.

Type a 70-char title (Title input enforces `maxLength="60"` so the keystrokes beyond 60 are simply not accepted — verify this).

Type a single space in Title. Save button stays disabled (we trim).

- [ ] **Step 11: Cancel restores cards without prompt**

Open the form, type something, click Cancel. Expected: cards re-render; nothing saved; no confirm dialog.

- [ ] **Step 12: DevTools storage**

`localStorage.getItem('iam_user_templates')` returns a JSON array; length matches the cards visible.

- [ ] **Step 13: Console clean**

After all the above, DevTools console must be clean — no errors.

- [ ] **Step 14: Done**

No commit needed.
