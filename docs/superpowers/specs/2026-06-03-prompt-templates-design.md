# Prompt Templates — Design

**Date:** 2026-06-03
**Scope:** UI only — `ui/templates/index.html`, `ui/static/style.css`, `ui/static/app.js`, new `ui/static/prompt-templates.js`
**Goal:** Replace the static three-line example list in the welcome block with a category-grouped grid of clickable prompt templates. A click drops the template text into the input box (no auto-send) so the user can edit before sending.

## Rationale

The current welcome block lists three example queries as plain text. New users (especially non-developers asked to operate the IAM tool) don't know what valid queries look like — there's no obvious way to copy or insert these examples. We already maintain richer prompt libraries inside `.claude/skills/treasury-iam.md` and `cash-iam.md`; surface them in the UI so a click of a card becomes a starting point.

Templates often contain placeholders like `<APP_ID>` or `<BRT_ID>`. The user can edit before sending — we do NOT auto-send.

## UI

The welcome block becomes:

```
┌────────────────────────────────────────┐
│  IAM Assistant                          │
│  Pick a template to start, or type     │
│  your own question.                     │
│                                         │
│  Treasury IAM                           │
│  ┌─────────────┐ ┌─────────────┐        │
│  │ Validate    │ │ Catalog     │ …      │
│  │ FOE/BOE SoD │ │ split       │        │
│  └─────────────┘ └─────────────┘        │
│                                         │
│  Cash Management                        │
│  ┌─────────────┐ ┌─────────────┐        │
│  │ Auth set    │ │ Submit /    │ …      │
│  │ completeness│ │ Approve SoD │        │
│  └─────────────┘ └─────────────┘        │
│                                         │
│  General                                │
│  ┌─────────────┐ ┌─────────────┐        │
│  │ App-to-     │ │ Restriction │        │
│  │ catalog map │ │ type cover  │        │
│  └─────────────┘ └─────────────┘        │
└────────────────────────────────────────┘
```

- Cards laid out as a CSS grid, `repeat(auto-fill, minmax(220px, 1fr))`, gap 8px.
- Each card has a short title (4-6 words) and a one-line subtitle (the prompt's intent).
- Click a card → the prompt template is inserted into `#input`, the textarea autoscrolls into view, the input gains focus, the textarea height is recomputed (auto-grow). **No auto-send.**

The previous static `<ul>` of examples is removed. The welcome block remains per-session: shown when history is empty, hidden once a message is sent.

## Data shape

A new file `ui/static/prompt-templates.js` exports a global `PROMPT_TEMPLATES` constant — a flat array of `{ category, title, prompt }` objects. Keeping it flat (not nested) simplifies iteration; we group by `category` at render time.

```js
window.PROMPT_TEMPLATES = [
  { category: 'Treasury IAM', title: 'FOE/BOE SoD validation',
    prompt: 'For app <APP_ID>, validate whether it is compliant with FOE or BOE SoD rules.' },
  { category: 'Treasury IAM', title: 'Catalog split analysis',
    prompt: 'Analyze SAP_TC_FIN_TRM_COMMON and propose the FOE/BOE split — which apps go where?' },
  { category: 'Treasury IAM', title: 'Hedge request SoD',
    prompt: 'For app <APP_ID>, validate T_TOE_HR values against MOE and Accountant forbidden combinations.' },
  { category: 'Treasury IAM', title: 'BRT footprint',
    prompt: 'For Business Role Template <BRT_ID>, show the full catalog and app footprint.' },
  { category: 'Cash Management', title: 'Activity set completeness',
    prompt: 'For IAM App ID <IAM_APP_ID>, verify whether the authorization activity set is complete and aligned with the intended business process.' },
  { category: 'Cash Management', title: 'Submit/Approve SoD',
    prompt: 'For IAM App ID <IAM_APP_ID>, analyze whether submit and approve capabilities are properly segregated across applications and roles.' },
  { category: 'Cash Management', title: 'Four-eyes catalog check',
    prompt: 'For Business Catalog <BC_ID>, identify whether any access combination violates the four-eyes principle or introduces SoD risks.' },
  { category: 'Cash Management', title: 'IAM health check',
    prompt: 'For IAM App ID <IAM_APP_ID>, run a full IAM health check including authorization objects, activity sets, catalog assignments, and BRT coverage.' },
  { category: 'General', title: 'App → Catalog mapping',
    prompt: 'List all catalogs that include app <APP_ID>.' },
  { category: 'General', title: 'Restriction type coverage',
    prompt: 'Check restriction type coverage for SAP_FIN_BC_TRM_TMPL_PC.' },
  { category: 'General', title: 'BRT catalog tree',
    prompt: 'Show the full catalog tree for Business Role Template <BRT_ID>.' },
  { category: 'General', title: 'Authorization object usage',
    prompt: 'Find all apps that use authorization object <AUTH_OBJECT>.' },
];
```

Categories render in the order they first appear in the array — so the array order IS the display order. No alphabetic sort. This keeps Treasury (the most common use case for this team) at the top.

`<APP_ID>`-style placeholders are kept as plain literal text. The user replaces them by hand. We don't introduce a fancy "tab through placeholders" interaction — that's overkill for a 12-template library.

## Loading

`prompt-templates.js` is loaded **before** `app.js` via a new `<script>` tag in `index.html`. We don't lazy-load — the file is small (~2 KB) and the welcome block needs it on first paint when the session is empty.

## File-level changes

### `ui/templates/index.html`

Replace the contents of `<template id="welcome-template">`:

```html
<template id="welcome-template">
  <div id="welcome" class="welcome">
    <h2>IAM Assistant</h2>
    <p>Pick a template to start, or type your own question.</p>
    <div id="welcome-templates"></div>
  </div>
</template>
```

Add a `<script>` tag for `prompt-templates.js` BEFORE `app.js`:

```html
<script src="/static/prompt-templates.js"></script>
<script src="/static/app.js"></script>
```

### `ui/static/prompt-templates.js`

New file, ~50 lines. Defines `window.PROMPT_TEMPLATES` array.

### `ui/static/style.css`

Add `.welcome-category-heading`, `.welcome-cards` (grid), `.welcome-card` rules. Adjust `.welcome` to expand wider — current `max-width: 480px` is too tight for a card grid. Bump to `max-width: 720px`.

### `ui/static/app.js`

In `showWelcome` (or via a new helper called from `showWelcome`), after the template is cloned:

1. Find `#welcome-templates` inside the cloned welcome.
2. Group `window.PROMPT_TEMPLATES` by `category`, preserving first-appearance order.
3. For each group, append a heading (`.welcome-category-heading`) and a `.welcome-cards` div containing one `.welcome-card` button per template.
4. Each button has a `<div class="card-title">` and `<div class="card-subtitle">` (the prompt itself, truncated by CSS to 2 lines via `-webkit-line-clamp`).
5. On click: insert `prompt` into `#input.value`, dispatch the `input` event so the autosize handler fires, focus `#input`. **Do NOT send.**

The card click handler must NOT call `sendMessage` — only set the value.

## Out of Scope

- Editing templates from the UI (no template-management screen).
- Loading templates from the server / personalization per user.
- Placeholder navigation (no "tab through `<APP_ID>` slots" UX).
- Search/filter templates.
- "Recently used templates" tracking.

## Verification

1. Cold load (cleared storage): welcome block shows category headings (Treasury IAM, Cash Management, General) in that order, with multiple cards each.
2. Click a Treasury card with `<APP_ID>` in the prompt: the input fills with the prompt text including the literal `<APP_ID>`, textarea height grows to fit, input is focused. No message sent.
3. Edit `<APP_ID>` to a real id, press Send → query runs as before.
4. After first send, welcome disappears; remains hidden across that session.
5. Switch to a session with prior history → welcome stays hidden.
6. Switch to a fresh session via `+ New` → welcome with templates re-renders.
7. DevTools: `window.PROMPT_TEMPLATES.length === 12`. Console clean — no `PROMPT_TEMPLATES is not defined`.
8. CSS responsive: at narrow viewport widths, cards stack into fewer columns.
