# Custom Prompt Templates — Design

**Date:** 2026-06-03
**Scope:** UI only — `ui/static/app.js`, `ui/static/style.css`. No HTML or new files.
**Goal:** Let the user save their own prompt templates to the welcome card grid. Templates are local to the browser (localStorage), live alongside the 16 built-in templates under a fixed `Custom` category, and are individually editable and deletable. Built-in templates are read-only.

## Rationale

The 16 built-ins cover common IAM scenarios but miss niche cases each user develops over time (specific catalogs they re-investigate, particular SoD audits they run quarterly). Asking the user to retype the same 200-character prompt every time is friction. Letting them save their own takes 30 seconds and pays back forever.

Cross-user sharing was explicitly rejected — that's a backend feature for another day. Local-only is enough to be useful.

## UI

### Welcome layout

After the four built-in categories (`Getting Started`, `Treasury IAM`, `Cash Management`, `General`), one more group appears IF the user has any custom templates:

```
… Built-in cards above …

CUSTOM
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ My audit    │ │ Quarterly   │ │  + Add      │
│ template    │ │ SoD scan    │ │  template   │
└─────────────┘ └─────────────┘ └─────────────┘
```

If no custom templates exist yet, the `Custom` heading still shows with just the `+ Add template` card so the entry point is always visible:

```
CUSTOM
┌─────────────┐
│  + Add      │
│  template   │
└─────────────┘
```

### Custom card visuals

A custom card looks like a built-in card, with two extras visible only on `:hover`:

- A small pencil **edit** button (top-right, before the delete)
- A small × **delete** button (top-right corner)

Hidden by default; revealed on `:hover` of the card. Both buttons stop propagation so the click doesn't also fill the input.

### Add card

The last card in the `Custom` group is a dashed-border placeholder with `+ Add template` content. Click it → a form replaces the welcome content (or expands inline above the cards). Same for clicking pencil — opens the form prefilled.

### The form

Inline, inside `#welcome-templates`, replacing the cards while editing:

```
┌────────────────────────────────────────┐
│ Add template                           │
│                                        │
│ Title                                  │
│ [_________________________________]    │
│                                        │
│ Prompt                                 │
│ ┌────────────────────────────────┐     │
│ │                                │     │
│ │                                │     │
│ │                                │     │
│ └────────────────────────────────┘     │
│                                        │
│ [Cancel]              [Save template]  │
└────────────────────────────────────────┘
```

- **Title**: required, 1–60 chars (trimmed). Empty → Save disabled.
- **Prompt**: required, 1–2000 chars. Empty → Save disabled.
- **Cancel**: closes the form, restores the cards.
- **Save**: writes the template to localStorage, closes the form, re-renders the cards.

No category picker — every user template is `Custom`. (Decision: keep edges clean, prevent accidental pollution of the built-in categories.)

When **editing** an existing template, the form is the same but the heading reads `Edit template` and `Save` updates in place rather than appending.

## Data

New localStorage key `iam_user_templates` → JSON array:

```json
[
  { "id": "a1b2c3d4", "title": "Quarterly SoD scan", "prompt": "Run a SoD scan on…", "createdAt": 1717400000000 }
]
```

`id` = `crypto.randomUUID().slice(0, 8)`. No `updatedAt` — we don't sort by it; user templates display in insertion order.

A new module-style namespace `UserTemplates` in `app.js` provides:

- `UserTemplates.list()` → `Array<{id, title, prompt, createdAt}>`, in insertion order.
- `UserTemplates.create(title, prompt)` → returns the new id.
- `UserTemplates.update(id, title, prompt)` → mutates in place.
- `UserTemplates.delete(id)` → removes.

Both create and update perform input validation (trim, length cap). On invalid input, throw a small `Error('reason')`; the form layer catches and surfaces inline.

## Render integration

`populateWelcomeTemplates(container)` (the existing function) is extended:

1. Render built-ins as today (group → cards).
2. Render the `Custom` group with:
   - All `UserTemplates.list()` entries as cards (with edit/delete buttons).
   - The `+ Add template` card as the final card in the group.
3. Card click → fill input (no auto-send) — same behavior as built-ins.
4. Card edit-button click → `renderWelcomeForm(existing)` replacing the welcome contents.
5. Card delete-button click → `confirm("Delete template <title>?")` → `UserTemplates.delete(id)` → `populateWelcomeTemplates(container)` (just re-render).
6. Add card click → `renderWelcomeForm(null)`.

`renderWelcomeForm(existing | null)` builds the form into the same `#welcome-templates` container (replacing the cards). On Save / Cancel, restore the cards via `populateWelcomeTemplates`.

## CSS additions

- `.welcome-card.custom` — a subtle marker (no visual difference; just a hook for the edit/delete buttons).
- `.welcome-card .card-actions` — a small absolute-positioned cluster of pencil + × buttons in the top-right; `visibility: hidden` by default; `:hover` reveals.
- `.welcome-card.custom .card-action-btn` — small icon button; muted by default; accent on hover.
- `.welcome-card.add-card` — dashed border (`border: 1px dashed var(--border)`), centered text, no subtitle, slightly lower opacity until hover.
- `.welcome-form` — a column flex layout with labelled fields, similar to the welcome's existing typography.
- `.welcome-form input`, `.welcome-form textarea` — match `#input` styling for consistency. Textarea: `min-height: 120px; resize: vertical`.
- `.welcome-form-actions` — flex row, justify-content: flex-end, gap.
- `.welcome-form-actions .btn-primary` — blue/accent button (Save).
- `.welcome-form-actions .btn-secondary` — neutral button (Cancel).

All new selectors are scoped under `.welcome` or `.welcome-card.*`.

## Behavior decisions

- The form is rendered inside `#welcome-templates` (replacing the cards), NOT as a modal overlay. This keeps the user in the same visual context and avoids a backdrop layer.
- Cancel always restores the cards without prompting (no "discard changes?" dialog). The form is cheap to redo if cancelled by accident.
- Built-in templates have no edit/delete buttons. They are purely fixed.
- The `Custom` heading and `+ Add template` card render even when zero custom templates exist — the entry point must be discoverable.
- A user-created template that exactly matches a built-in is allowed (we don't dedupe). Filtering would be over-engineering.
- The pencil and × buttons use Unicode glyphs `✎` and `×` (no SVG, no icon font).

## Out of Scope

- Cross-user sharing (rejected).
- Importing/exporting templates as a JSON blob.
- Sorting or searching the Custom list.
- Reordering custom templates beyond insertion order.
- Editing built-in templates.
- Moving custom templates between categories.
- Per-template variables / "tab through `<APP_ID>` slots" UX.
- Confirmation prompt on Cancel when the form has unsaved changes.

## Verification

1. Cold load with empty `iam_user_templates`: welcome shows 4 built-in groups, then `Custom` with just the `+ Add template` card.
2. Click `+ Add template`: form renders, Save disabled until both fields non-empty.
3. Type "My audit" / "List all apps in <BC_ID>", click Save: form closes, a new card appears in `Custom` before the `+ Add template` card.
4. Click the new card: input fills with the prompt; no message sent.
5. Hover the new card: pencil and × buttons appear top-right.
6. Click pencil: form opens prefilled with the existing values, heading reads `Edit template`.
7. Edit the prompt, Save: card title/subtitle update in place.
8. Click ×: confirm dialog → Yes → card disappears from the grid.
9. Refresh the browser: custom templates persist.
10. Click a built-in card: it has no edit/delete buttons (verify by inspecting the rendered DOM).
11. DevTools: `localStorage.getItem('iam_user_templates')` is a JSON array; `JSON.parse(...).length` matches what's on screen.
12. Console clean — no errors after add/edit/delete cycles.
13. Validation: try Save with empty title or empty prompt → button is disabled (or click does nothing if already disabled).
