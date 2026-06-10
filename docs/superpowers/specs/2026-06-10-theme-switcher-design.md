# UI Theme Switcher — Design

**Date:** 2026-06-10
**Scope:** Add a Dark / Light theme switch to the IAM Assistant web UI.

## Goal

Today the UI is dark only. Add a one-click toggle so users can choose Dark or
Light. The choice persists across reloads. New users get Dark by default —
matching today's appearance, so existing users see no visual change.

## Non-Goals

- No automatic following of `prefers-color-scheme`.
- No backend persistence or cross-device sync — it's a pure UI preference.
- No theme-picker menu / dropdown / modal — single toggle button only.
- No custom user-defined palettes, no third theme.
- No transition animation when switching — instant flip is fine and avoids feeling sluggish.

## Architecture

Three small components, each with one job:

| Component       | File                          | Responsibility                                                                  |
| --------------- | ----------------------------- | ------------------------------------------------------------------------------- |
| Theme state     | `<html data-theme="...">`     | Single source of truth for the current theme.                                   |
| Style layer     | `ui/static/style.css`         | Default Catppuccin Mocha (Dark) in `:root`, plus a Latte (Light) override block. |
| Control layer   | `ui/static/app.js` + inline `<head>` script | Read/write `localStorage`, flip the attribute, drive the button.    |

### Data flow

```
User clicks ☀/🌙  →  JS toggles data-theme on <html>
                  →  CSS variables re-resolve, page re-paints
                  →  localStorage.setItem("theme", "...")

Page load        →  Inline <head> script reads localStorage
                  →  Sets data-theme BEFORE stylesheet is applied
                  →  No flash of wrong theme (FOUC)
```

The inline script runs before the `<link rel="stylesheet">` tag is processed.
That ordering is what makes the no-flash guarantee work.

## Color Mapping (Catppuccin Latte for Light)

The existing Dark palette is Catppuccin Mocha. The Light palette is Catppuccin
Latte — its official sister palette — so the design language (the "feel" of
blue/green/red/amber) stays consistent across modes.

Add a single new block to the end of `ui/static/style.css`:

```css
:root[data-theme="light"] {
  --bg: #eff1f5;          /* base */
  --surface: #e6e9ef;     /* mantle */
  --border: #ccd0da;      /* surface0 */
  --text: #4c4f69;        /* text */
  --muted: #8c8fa1;       /* overlay1 */
  --accent: #1e66f5;      /* blue */
  --green: #40a02b;
  --red: #d20f39;
  --amber: #df8e1d;
  --code-bg: #dce0e8;     /* crust */
  --border-soft: #bcc0cc; /* surface1 */
  --strong: #dc8a78;      /* rosewater */
}
```

### Hard-coded colors that need to become variables

The current CSS has three colors written as literals instead of `var(--...)`.
Each one needs to be aliased so the Light override can change it. This is a
small, scoped cleanup — done because it's necessary for theme support, not
unrelated refactoring.

| Literal       | Used at                              | New variable     | Dark value | Light value |
| ------------- | ------------------------------------ | ---------------- | ---------- | ----------- |
| `#11111b`     | `.msg-ai pre` background             | `--code-bg`      | `#11111b`  | `#dce0e8`   |
| `#2a2b3d`     | `.msg-ai` border, `.msg-ai pre` border | `--border-soft` | `#2a2b3d`  | `#bcc0cc`   |
| `#f5e0dc`     | `.msg-ai strong` color               | `--strong`       | `#f5e0dc`  | `#dc8a78`   |

The Dark values for these three new variables are added to the existing
`:root { ... }` block. The three call sites are updated to use `var(--...)`.
**No other CSS rules change** — every other rule already uses variables.

## HTML Changes (`ui/templates/index.html`)

### (a) Inline FOUC-prevention script

Inserted in `<head>` **before** the existing `<link rel="stylesheet">` tag:

```html
<script>
  // Set theme before stylesheet loads — prevents flash of wrong theme.
  (function () {
    var t = localStorage.getItem("theme") || "dark";
    document.documentElement.setAttribute("data-theme", t);
  })();
</script>
```

It reads localStorage synchronously, defaults to `"dark"`, sets the attribute
on `<html>`. This must run before the stylesheet is parsed, because that's
when the variable values are resolved for first paint.

### (b) Toggle button in header

Inside `.header-right`, immediately **before** the `Sign out` link:

```html
<button id="theme-toggle" type="button" title="Toggle theme" aria-label="Toggle theme">🌙</button>
```

Icon convention:

- Current = Dark → button shows 🌙 (it's night; click → go to day)
- Current = Light → button shows ☀

## JavaScript (`ui/static/app.js`)

About 15 lines, added near the existing initialization code:

```js
function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("theme", theme);
  const btn = document.getElementById("theme-toggle");
  if (btn) btn.textContent = theme === "dark" ? "🌙" : "☀";
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "dark";
  applyTheme(current === "dark" ? "light" : "dark");
}

// On DOMContentLoaded — sync button icon and wire click handler.
document.addEventListener("DOMContentLoaded", () => {
  applyTheme(document.documentElement.getAttribute("data-theme") || "dark");
  document.getElementById("theme-toggle")?.addEventListener("click", toggleTheme);
});
```

`applyTheme` is the single mutation function — every change goes through it.
The DOMContentLoaded handler doesn't pick a theme; it just re-applies whatever
the inline `<head>` script already set, so the button icon matches the state.

## Button Style (`ui/static/style.css`)

Added near the existing `.header-right` rules:

```css
#theme-toggle {
  background: transparent; border: none;
  color: var(--muted); cursor: pointer;
  font-size: 14px; padding: 4px 6px; line-height: 1;
  border-radius: 4px;
}
#theme-toggle:hover { color: var(--text); background: var(--border); }
```

Matches the visual weight of the other header indicators.

## Verification (manual — no front-end test framework in this project)

1. Fresh browser (or `localStorage.clear()`) → app loads in **Dark** by default.
2. Click 🌙 → page flips to **Light** instantly, no flicker. Visually scan:
   header, sidebar, session list, welcome cards, input bar, AI message
   bubbles, code blocks, tables, error text, confirm dialog backdrop.
3. **Reload the page** → still Light, **no flash of Dark** during load. (This
   is the FOUC test — if the inline `<head>` script is missing or in the
   wrong place, you'll see a dark flash here.)
4. Click ☀ → back to Dark. Reload → still Dark.
5. `localStorage.removeItem("theme")` and reload → defaults back to Dark.
6. In Light mode, check WCAG-AA-ish contrast on muted text, the search input
   placeholder, and the disabled Send button.
7. AI message rendering in Light: bold (`--strong`), inline `code` (amber on
   `--border`), `<pre>` blocks (`--code-bg`), tables, links, headings — all
   readable.

## Files Touched

| File                            | Change                                                                  |
| ------------------------------- | ----------------------------------------------------------------------- |
| `ui/templates/index.html`       | Inline FOUC script in `<head>`; `#theme-toggle` button in `.header-right`. |
| `ui/static/style.css`           | 3 new variables in `:root`; replace 3 hard-coded colors with `var(--...)`; new `:root[data-theme="light"]` block; `#theme-toggle` button styles. |
| `ui/static/app.js`              | `applyTheme`, `toggleTheme`, DOMContentLoaded wire-up.                   |

No backend, server, or Python changes.

## Risks & Mitigations

- **FOUC on slow loads** — mitigated by inline `<head>` script setting the
  attribute before the stylesheet resolves variables.
- **localStorage disabled / unavailable** (private browsing in some browsers)
  — `localStorage.getItem` returns null safely; default `"dark"` kicks in.
  `setItem` would throw — wrap in try/catch in implementation if needed
  (decide during plan, but it's a one-line concern).
- **New hard-coded colors creeping in later** — design notes that all colors
  must use `var(--...)`; if a future change adds a literal, it'll only work
  in one mode. Caught at code review.

## Out of Scope (explicit)

- No system-preference auto-detection.
- No third theme.
- No theme menu UI.
- No backend persistence.
- No transition animation.
