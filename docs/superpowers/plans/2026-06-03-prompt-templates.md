# Prompt Templates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the static example list in the welcome block with a category-grouped grid of clickable prompt template cards. Click → fill input, no auto-send.

**Architecture:** New static `ui/static/prompt-templates.js` defines `window.PROMPT_TEMPLATES`. `index.html` loads it before `app.js`. `showWelcome` populates the template grid by grouping the global array by category. Card click sets `#input.value` and triggers the autosize input event.

**Tech Stack:** Vanilla JS, plain CSS, Jinja HTML.

**Reference spec:** `docs/superpowers/specs/2026-06-03-prompt-templates-design.md`

**Testing:** No JS unit tests in this repo; verification is manual (Task 5).

---

## File Structure

- **Create** `ui/static/prompt-templates.js` — the `PROMPT_TEMPLATES` array.
- **Modify** `ui/templates/index.html` — replace welcome template body; add `<script>` for prompt-templates.js before app.js.
- **Modify** `ui/static/style.css` — add `.welcome-category-heading`, `.welcome-cards`, `.welcome-card`, `.card-title`, `.card-subtitle`; widen `.welcome`.
- **Modify** `ui/static/app.js` — extend `showWelcome` (or call a new `populateWelcomeTemplates` from inside it) to inject the category grid and wire click handlers.

---

## Task 1: Create prompt-templates.js

**Files:** Create `ui/static/prompt-templates.js`

- [ ] **Step 1: Write the file**

Create `ui/static/prompt-templates.js` with this content:

```js
// Prompt template library for the welcome block.
// Each entry: { category, title, prompt }
// Categories appear in the order they first occur in this array.
// Loaded as a plain <script> before app.js — exposes window.PROMPT_TEMPLATES.

window.PROMPT_TEMPLATES = [
  // Getting Started — onboarding questions, no placeholders. Click → send-ready.
  { category: 'Getting Started', title: 'What can I ask?',
    prompt: 'What kinds of IAM questions can you help me with? Give me a short overview of your capabilities and the data you can query.' },
  { category: 'Getting Started', title: 'Glossary: BRT, BC, App',
    prompt: 'Explain the IAM concepts I will encounter most often: Business Role Template (BRT), Business Catalog, IAM App, Restriction Type. Use plain language.' },
  { category: 'Getting Started', title: 'What is SoD?',
    prompt: 'Explain Segregation of Duties (SoD) in this IAM system: what it means, why it matters, and how it shows up in catalogs and authorization objects.' },
  { category: 'Getting Started', title: 'How do roles work?',
    prompt: 'Walk me through how a Business Role Template gets composed from Business Catalogs and apps, and how those map to PFCG roles in SAP.' },

  // Treasury IAM
  { category: 'Treasury IAM', title: 'FOE/BOE SoD validation',
    prompt: 'For app <APP_ID>, validate whether it is compliant with FOE or BOE SoD rules.' },
  { category: 'Treasury IAM', title: 'Catalog split analysis',
    prompt: 'Analyze SAP_TC_FIN_TRM_COMMON and propose the FOE/BOE split — which apps go where?' },
  { category: 'Treasury IAM', title: 'Hedge request SoD',
    prompt: 'For app <APP_ID>, validate T_TOE_HR values against MOE and Accountant forbidden combinations.' },
  { category: 'Treasury IAM', title: 'BRT footprint',
    prompt: 'For Business Role Template <BRT_ID>, show the full catalog and app footprint.' },

  // Cash Management
  { category: 'Cash Management', title: 'Activity set completeness',
    prompt: 'For IAM App ID <IAM_APP_ID>, verify whether the authorization activity set is complete and aligned with the intended business process.' },
  { category: 'Cash Management', title: 'Submit/Approve SoD',
    prompt: 'For IAM App ID <IAM_APP_ID>, analyze whether submit and approve capabilities are properly segregated across applications and roles.' },
  { category: 'Cash Management', title: 'Four-eyes catalog check',
    prompt: 'For Business Catalog <BC_ID>, identify whether any access combination violates the four-eyes principle or introduces SoD risks.' },
  { category: 'Cash Management', title: 'IAM health check',
    prompt: 'For IAM App ID <IAM_APP_ID>, run a full IAM health check including authorization objects, activity sets, catalog assignments, and BRT coverage.' },

  // General
  { category: 'General', title: 'App → Catalog mapping',
    prompt: 'List all catalogs that include app <APP_ID>.' },
  { category: 'General', title: 'Restriction type coverage',
    prompt: 'Check restriction type coverage for SAP_FIN_BC_TRM_TMPL_PC.' },
  { category: 'General', title: 'BRT catalog tree',
    prompt: 'Show the full catalog tree for Business Role Template <BRT_ID>.' },
  { category: 'General', title: 'Auth object usage',
    prompt: 'Find all apps that use authorization object <AUTH_OBJECT>.' },
];
```

- [ ] **Step 2: Confirm syntax**

Run: `node --check ui/static/prompt-templates.js`
Expected: clean exit.

- [ ] **Step 3: Commit**

```bash
git add ui/static/prompt-templates.js
git commit -m "feat(ui): add PROMPT_TEMPLATES library"
```

---

## Task 2: HTML — load script, restructure welcome template

**Files:** Modify `ui/templates/index.html`

- [ ] **Step 1: Add prompt-templates.js script tag**

Find:

```html
<script src="/static/app.js"></script>
```

Replace with:

```html
<script src="/static/prompt-templates.js"></script>
<script src="/static/app.js"></script>
```

(Order matters: `prompt-templates.js` first defines `window.PROMPT_TEMPLATES`, then `app.js` uses it.)

- [ ] **Step 2: Replace the welcome template body**

Find:

```html
<!-- Welcome content (cloned at startup-when-empty and on New session). -->
<template id="welcome-template">
  <div id="welcome" class="welcome">
    <h2>IAM Assistant</h2>
    <p>Ask a question to get started. Examples:</p>
    <ul>
      <li>Show BRT coverage for SAP_BR_TREASURY_SPECIALIST_FOE</li>
      <li>Run a SoD scan on the Treasury FOE catalogs</li>
      <li>Check restriction type coverage for SAP_FIN_BC_TRM_TMPL_PC</li>
    </ul>
  </div>
</template>
```

Replace with:

```html
<!-- Welcome content (cloned at startup-when-empty and on New session).
     #welcome-templates is filled at clone time by populateWelcomeTemplates(). -->
<template id="welcome-template">
  <div id="welcome" class="welcome">
    <h2>IAM Assistant</h2>
    <p>Pick a template to start, or type your own question.</p>
    <div id="welcome-templates"></div>
  </div>
</template>
```

- [ ] **Step 3: Commit**

```bash
git add ui/templates/index.html
git commit -m "feat(ui): swap static welcome examples for templates grid placeholder"
```

---

## Task 3: CSS — widen welcome, style cards

**Files:** Modify `ui/static/style.css`

- [ ] **Step 1: Widen `.welcome`**

Find:

```css
.welcome { max-width: 480px; }
```

Replace with:

```css
.welcome { max-width: 720px; }
```

- [ ] **Step 2: Add card grid styles**

Add this block immediately after the existing `.welcome` rules (the four `.welcome*` lines at the bottom of the file):

```css
.welcome-category-heading {
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--muted); font-weight: 600;
  margin: 16px 0 8px;
}
.welcome-category-heading:first-child { margin-top: 8px; }
.welcome-cards {
  display: grid; gap: 8px;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
}
.welcome-card {
  background: var(--surface); color: var(--text);
  border: 1px solid var(--border); border-radius: 8px;
  padding: 10px 12px; text-align: left;
  cursor: pointer; font-family: inherit;
  display: flex; flex-direction: column; gap: 4px;
}
.welcome-card:hover { border-color: var(--accent); }
.welcome-card .card-title {
  font-size: 13px; font-weight: 600; color: var(--text);
}
.welcome-card .card-subtitle {
  font-size: 11.5px; color: var(--muted); line-height: 1.4;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden;
}
```

- [ ] **Step 3: Commit**

```bash
git add ui/static/style.css
git commit -m "style(ui): welcome card grid + wider container"
```

---

## Task 4: JS — populate the grid and wire clicks

**Files:** Modify `ui/static/app.js`

- [ ] **Step 1: Add `populateWelcomeTemplates` helper**

In `ui/static/app.js`, find the `showWelcome` function:

```js
function showWelcome() {
  if (document.getElementById('welcome')) return; // already shown
  const tpl = document.getElementById('welcome-template');
  const node = tpl.content.firstElementChild.cloneNode(true);
  const chatPanel = document.getElementById('chat-panel');
  chatPanel.insertBefore(node, document.getElementById('messages'));
}
```

Replace with:

```js
function showWelcome() {
  if (document.getElementById('welcome')) return; // already shown
  const tpl = document.getElementById('welcome-template');
  const node = tpl.content.firstElementChild.cloneNode(true);
  const chatPanel = document.getElementById('chat-panel');
  chatPanel.insertBefore(node, document.getElementById('messages'));
  populateWelcomeTemplates(node.querySelector('#welcome-templates'));
}

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

function fillInputFromTemplate(prompt) {
  const input = document.getElementById('input');
  input.value = prompt;
  // Trigger the existing autosize handler (registered with addEventListener('input', ...)).
  input.dispatchEvent(new Event('input'));
  input.focus();
  // Move caret to the end so the user can edit immediately.
  input.setSelectionRange(prompt.length, prompt.length);
}
```

Notes:
- All user-supplied data goes via `textContent`. No `innerHTML` involvement.
- The autosize handler currently lives at module scope as `input.addEventListener('input', ...)`. Dispatching a synthetic `input` event triggers that handler so the textarea grows to fit.
- We do NOT call `sendMessage` — the spec is explicit that templates fill but don't send.

- [ ] **Step 2: Confirm syntax**

Run: `node --check ui/static/app.js`
Expected: clean exit.

- [ ] **Step 3: Commit**

```bash
git add ui/static/app.js
git commit -m "feat(ui): populate welcome template grid; click fills input"
```

---

## Task 5: Manual browser verification

**Files:** none modified.

- [ ] **Step 1: Restart the dev server**

```bash
set -a && source .sapcli.env && set +a
conda run -n sapcli-env --no-capture-output uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

Hard-refresh the browser (Cmd+Shift+R / Ctrl+Shift+R).

- [ ] **Step 2: Cold load with empty session**

Clear site storage, reload. Expected:
- Welcome block visible.
- Four category headings: `Getting Started`, `Treasury IAM`, `Cash Management`, `General` in that order.
- Multiple card buttons under each heading; cards have a bold title and a 2-line muted subtitle.
- Cards form a responsive grid (auto-fill, minmax 220px).

- [ ] **Step 3: Click a Getting Started card**

Click "What can I ask?" (or any Getting Started card). Expected:
- The input textarea fills with the full question — no `<...>` placeholders.
- Textarea height grows; input focused; caret at end.
- No auto-send. The user can press Send to actually run the question.

- [ ] **Step 4: Click a Treasury card**

Click "FOE/BOE SoD validation" (or any Treasury card). Expected:
- The input textarea fills with the template text including the literal `<APP_ID>` placeholder.
- Textarea height grows to fit the prompt (autosize triggered).
- Input is focused; caret at end.
- No message sent.

- [ ] **Step 5: Edit and send**

Replace `<APP_ID>` with a real id (e.g. `F1443A_TRAN`), press Send. Expected: query runs normally, welcome disappears.

- [ ] **Step 6: New session**

Click `+ New` in the sidebar. Expected:
- Welcome reappears with the template grid.
- All categories render.

- [ ] **Step 7: Switch to a session with history**

Click an older session row. Expected: welcome hidden, prior conversation rendered.

- [ ] **Step 8: DevTools checks**

Open DevTools console.

Expected:
- `window.PROMPT_TEMPLATES.length` returns 16.
- No `ReferenceError`.
- No CSS warning about unknown properties.

- [ ] **Step 9: Responsive check**

Narrow the browser window. Expected: cards reflow to fewer columns; nothing overflows the welcome container.

- [ ] **Step 10: Done**

No commit needed — verification only.
