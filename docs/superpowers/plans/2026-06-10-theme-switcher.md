# Theme Switcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Dark / Light theme toggle to the IAM Assistant web UI. Default Dark, persisted in localStorage, instant switch with no flash.

**Architecture:** A `data-theme` attribute on `<html>` selects the palette. The default `:root { ... }` keeps the current Catppuccin Mocha (Dark) values; a new `:root[data-theme="light"] { ... }` block overrides them with Catppuccin Latte (Light). An inline `<head>` script reads `localStorage` and sets the attribute *before* the stylesheet is processed, so first paint uses the correct palette (no FOUC). A toggle button in the header flips the attribute and writes localStorage.

**Tech Stack:** Vanilla HTML / CSS / JS. No new dependencies. No backend changes.

**Spec:** `docs/superpowers/specs/2026-06-10-theme-switcher-design.md`

---

## File Structure

| File | Change |
| ---- | ------ |
| `ui/templates/index.html` | Add inline `<head>` FOUC script before stylesheet `<link>`; add `<button id="theme-toggle">` in `.header-right` before `Sign out`. |
| `ui/static/style.css` | Add 3 new CSS variables to `:root` (`--code-bg`, `--border-soft`, `--strong`); replace 3 hard-coded color literals at lines 122, 139, 146 with `var(--...)`; add `:root[data-theme="light"] { ... }` override block; add `#theme-toggle` button styles. |
| `ui/static/app.js` | Add `applyTheme()` and `toggleTheme()` near top; wire button click handler at the bottom alongside the other top-level init calls (this codebase uses top-level init, **not** `DOMContentLoaded`). |

No test framework exists in this UI codebase (the project has Python tests under `tests/` but no JS tests). Verification is **manual**, performed at the end. The plan still uses tight commits per task.

---

## Task 1: Add CSS variables and aliases for hard-coded colors

This is a pure refactor — no behavior change. Just makes the three literal color values live as variables so the Light theme can override them.

**Files:**
- Modify: `ui/static/style.css:3-14` (add 3 variables to `:root`)
- Modify: `ui/static/style.css:122` (replace `#2a2b3d`)
- Modify: `ui/static/style.css:139` (replace `#f5e0dc`)
- Modify: `ui/static/style.css:146` (replace `#11111b` and `#2a2b3d`)

- [ ] **Step 1: Add three new variables to the `:root` block**

In `ui/static/style.css`, change the `:root` block (currently lines 3-14) by appending three new variables. The block should become:

```css
:root {
  --bg: #1e1e2e;
  --surface: #181825;
  --border: #313244;
  --text: #cdd6f4;
  --muted: #6c7086;
  --accent: #89b4fa;
  --green: #a6e3a1;
  --red: #f38ba8;
  --amber: #f9e2af;
  --code-bg: #11111b;
  --border-soft: #2a2b3d;
  --strong: #f5e0dc;
  --header-h: 48px;
}
```

- [ ] **Step 2: Replace `#2a2b3d` on line 122 (`.msg-ai` border)**

Find this line in `ui/static/style.css` (around line 122 inside `.msg-ai`):

```css
  border: 1px solid #2a2b3d;
```

Replace with:

```css
  border: 1px solid var(--border-soft);
```

- [ ] **Step 3: Replace `#f5e0dc` on line 139 (`.msg-ai strong`)**

Find:

```css
.msg-ai strong { color: #f5e0dc; }
```

Replace with:

```css
.msg-ai strong { color: var(--strong); }
```

- [ ] **Step 4: Replace both literals on line 146 (`.msg-ai pre`)**

Find:

```css
  background: #11111b; border: 1px solid #2a2b3d;
```

Replace with:

```css
  background: var(--code-bg); border: 1px solid var(--border-soft);
```

- [ ] **Step 5: Verify no other hard-coded hex colors remain in the file**

Run:

```bash
grep -nE '#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}\b' ui/static/style.css
```

Expected: only the lines inside the `:root` block (lines 4-15 area) should match. No matches outside `:root`. If any other hex literal shows up, it must also be replaced with a variable, otherwise it will not switch when the theme changes.

- [ ] **Step 6: Manual visual smoke test**

Reload the app in the browser. The page should look **identical** to before (still Dark, exact same colors). This task is a pure refactor.

- [ ] **Step 7: Commit**

```bash
git add ui/static/style.css
git commit -m "refactor(ui): alias hard-coded colors as CSS variables for theming"
```

---

## Task 2: Add Light theme palette (Catppuccin Latte)

Adds the override block that maps every variable to its Latte equivalent. Adding this block alone does nothing visible — `data-theme="light"` is not yet set anywhere — but the CSS is ready to switch.

**Files:**
- Modify: `ui/static/style.css` (append new block at end of file)

- [ ] **Step 1: Append the Light override block to the end of `ui/static/style.css`**

Append (after the last existing rule, line 404):

```css

/* Light theme — Catppuccin Latte. Activated by data-theme="light" on <html>. */
:root[data-theme="light"] {
  --bg: #eff1f5;
  --surface: #e6e9ef;
  --border: #ccd0da;
  --text: #4c4f69;
  --muted: #8c8fa1;
  --accent: #1e66f5;
  --green: #40a02b;
  --red: #d20f39;
  --amber: #df8e1d;
  --code-bg: #dce0e8;
  --border-soft: #bcc0cc;
  --strong: #dc8a78;
}
```

- [ ] **Step 2: Manual sanity check — the app should still look Dark**

Reload in browser. Page must look identical to before — no Light theme is active yet because no `data-theme` attribute has been set. If colors changed, the override block has incorrect specificity.

- [ ] **Step 3: Temporary visual test of the Light palette**

Open browser DevTools console and run:

```js
document.documentElement.setAttribute("data-theme", "light")
```

The page should flip to Light immediately. Visually scan: header bar, sidebar, welcome cards, input bar, AI message bubbles, code blocks, tables, dialog backdrops. All should be readable with no obvious unstyled patches.

Then run:

```js
document.documentElement.removeAttribute("data-theme")
```

The page should return to Dark.

- [ ] **Step 4: Commit**

```bash
git add ui/static/style.css
git commit -m "feat(ui): add Catppuccin Latte light theme palette"
```

---

## Task 3: Add inline FOUC-prevention script in `<head>`

The script must run *before* `<link rel="stylesheet">` so the attribute is set before the browser resolves CSS variables for first paint.

**Files:**
- Modify: `ui/templates/index.html:9` (insert script before existing stylesheet `<link>`)

- [ ] **Step 1: Insert the inline script before the stylesheet `<link>`**

In `ui/templates/index.html`, find line 9:

```html
  <link rel="stylesheet" href="/static/style.css">
```

Insert this immediately *before* it (between line 8 and line 9):

```html
  <script>
    // Set theme before stylesheet loads — prevents flash of wrong theme.
    (function () {
      var t = null;
      try { t = localStorage.getItem("theme"); } catch (e) {}
      document.documentElement.setAttribute("data-theme", t === "light" ? "light" : "dark");
    })();
  </script>
```

The `try/catch` covers private-browsing modes where localStorage access throws. The strict `t === "light"` check means any unexpected value (corrupted storage, future themes, null) safely falls back to Dark.

- [ ] **Step 2: Reload the app and confirm Dark default**

Open the app fresh (or run `localStorage.removeItem("theme")` and reload). Page should still load Dark — no visible change.

Inspect the `<html>` element in DevTools: it should now have `data-theme="dark"` attribute.

- [ ] **Step 3: Manual FOUC test with Light theme set**

In DevTools console:

```js
localStorage.setItem("theme", "light")
```

Then reload. The page should appear in Light from the very first paint — **no dark flash**, even on a slow throttled connection. To verify under throttling: in DevTools → Network → set throttling to "Slow 3G", reload again. Still no flash.

Then reset:

```js
localStorage.removeItem("theme")
```

Reload — Dark again.

- [ ] **Step 4: Commit**

```bash
git add ui/templates/index.html
git commit -m "feat(ui): add inline head script to set theme before stylesheet loads"
```

---

## Task 4: Add the toggle button to the header

The button has no behavior yet — clicking it does nothing until Task 5. This task just gets it into the DOM and styled.

**Files:**
- Modify: `ui/templates/index.html` (add button inside `.header-right`)
- Modify: `ui/static/style.css` (add `#theme-toggle` styles near header rules)

- [ ] **Step 1: Insert the toggle button in the header**

In `ui/templates/index.html`, find the `.header-right` block (lines 15-22):

```html
  <div class="header-right">
    <span id="mcp-indicator" class="indicator {{ 'connected' if mcp_status == 'connected' else 'disconnected' }}">
      ● ER6 {{ mcp_status }}
    </span>
    <span class="indicator">Model: {{ llm_model }}</span>
    <span class="username">{{ username }}</span>
    <a href="/auth/logout" class="signout">Sign out</a>
  </div>
```

Insert the button immediately *before* the `Sign out` `<a>`:

```html
  <div class="header-right">
    <span id="mcp-indicator" class="indicator {{ 'connected' if mcp_status == 'connected' else 'disconnected' }}">
      ● ER6 {{ mcp_status }}
    </span>
    <span class="indicator">Model: {{ llm_model }}</span>
    <span class="username">{{ username }}</span>
    <button id="theme-toggle" type="button" title="Toggle theme" aria-label="Toggle theme">🌙</button>
    <a href="/auth/logout" class="signout">Sign out</a>
  </div>
```

The default text content is `🌙` — this is correct for the default Dark theme. Task 5's JS will sync the icon to the actual current theme on init.

- [ ] **Step 2: Add button styles to `ui/static/style.css`**

Find the existing `.signout:hover` rule (around line 33):

```css
.signout:hover { color: var(--text); }
```

Append these rules immediately after it (before the `/* Layout */` comment):

```css
#theme-toggle {
  background: transparent; border: none;
  color: var(--muted); cursor: pointer;
  font-size: 14px; padding: 4px 6px; line-height: 1;
  border-radius: 4px;
  font-family: inherit;
}
#theme-toggle:hover { color: var(--text); background: var(--border); }
```

- [ ] **Step 3: Reload and visually verify the button**

Reload the app. The 🌙 button should appear in the header, between the username and `Sign out`. Hover should show the lighter background.

Clicking it does nothing yet — that's fine. We're verifying placement and styling only.

- [ ] **Step 4: Commit**

```bash
git add ui/templates/index.html ui/static/style.css
git commit -m "feat(ui): add theme toggle button to header"
```

---

## Task 5: Wire up the toggle behavior in `app.js`

This codebase runs init code at the top level of `app.js` (the `<script>` tag is at the bottom of `<body>`, so the DOM is already parsed). Follow that pattern — do **not** introduce a `DOMContentLoaded` handler.

**Files:**
- Modify: `ui/static/app.js` (add functions near top, init call at bottom)

- [ ] **Step 1: Add `applyTheme` and `toggleTheme` functions near the top**

In `ui/static/app.js`, find line 7 (the end of the existing storage-key declarations):

```js
const sessionDataKey = (id) => `iam_session:${id}`;
```

Insert *after* line 7 (a new section before the `Sessions` object on line 9):

```js

// ── Theme ──────────────────────────────────────────────────────────────
// The current theme lives on <html data-theme="..."> and is mirrored to
// localStorage. The inline <head> script set the attribute before the
// stylesheet loaded; these helpers only handle subsequent toggles.
function applyTheme(theme) {
  const next = theme === "light" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  try { localStorage.setItem("theme", next); } catch (e) {}
  const btn = document.getElementById("theme-toggle");
  if (btn) btn.textContent = next === "dark" ? "🌙" : "☀";
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "dark";
  applyTheme(current === "dark" ? "light" : "dark");
}
```

- [ ] **Step 2: Wire the click handler at the bottom of `app.js`**

The bottom of `app.js` (around line 939-945) currently has:

```js
if (loadHistory().length === 0) {
  showWelcome();
}

renderSidebar();
restoreChatMessages();
setInterval(() => renderSidebar(), 60_000);
```

Append at the end of the file (after the `setInterval` line):

```js

// Sync the theme button icon to the attribute set by the inline <head>
// script, then wire the click handler.
applyTheme(document.documentElement.getAttribute("data-theme") || "dark");
document.getElementById("theme-toggle").addEventListener("click", toggleTheme);
```

The first line here is important: the inline `<head>` script set the attribute, but the button's text content was hard-coded to `🌙` in HTML. Calling `applyTheme(...)` re-syncs the icon — for example, if the user previously chose Light, the button icon must show `☀` after page load, not `🌙`.

- [ ] **Step 3: Reload and test full flow**

Reload the app fresh (`localStorage.removeItem("theme")` first if needed):

1. Page loads Dark, button shows `🌙`.
2. Click `🌙` → page flips to Light instantly, button updates to `☀`.
3. Reload → page loads Light (no Dark flash), button shows `☀`.
4. Click `☀` → page flips to Dark, button updates to `🌙`.
5. Reload → page loads Dark, button shows `🌙`.

If any step fails, debug before committing.

- [ ] **Step 4: Commit**

```bash
git add ui/static/app.js
git commit -m "feat(ui): wire theme toggle button"
```

---

## Task 6: Final manual verification

Run through the full verification checklist from the spec to catch regressions and contrast issues.

**Files:** None modified — verification only.

- [ ] **Step 1: Reset state and verify Dark default**

In DevTools console:

```js
localStorage.removeItem("theme")
```

Reload. Confirm: page loads in Dark, button shows `🌙`.

- [ ] **Step 2: Switch to Light and visually scan all major UI elements**

Click the toggle button. Inspect each element type for sensible Light-mode appearance — text readable, borders visible, accents distinct:

- Header bar (logo, indicators, username, theme button, sign out link)
- Sidebar (`+ New` button, search input, session rows including hover and active states)
- Welcome screen (heading, prompt cards, category headings, search input, `+ Add template` dashed card)
- Input bar (textarea placeholder, Send button enabled/disabled state)
- Send a test message and check AI response rendering: paragraphs, headings, **bold** text, `inline code`, code block (```` ``` ````), tables, lists, links
- Hover an AI message → regenerate button appears, readable
- Hover a code block → copy button appears, readable
- Trigger a confirm dialog (e.g., delete a session) → backdrop and dialog box readable

- [ ] **Step 3: FOUC test under network throttling**

DevTools → Network tab → set throttling to "Slow 3G". With Light still active, reload the page. Watch the very first frames: there should be **no dark flash** before the page renders Light. If there's a flash, the inline `<head>` script is misplaced or running too late.

Reset throttling to "No throttling" when done.

- [ ] **Step 4: Switch back to Dark and verify**

Click the toggle button. Page returns to Dark. Reload — still Dark, button shows `🌙`. No flash.

- [ ] **Step 5: localStorage-disabled fallback**

In DevTools console, simulate localStorage failure:

```js
const orig = Storage.prototype.setItem;
Storage.prototype.setItem = function() { throw new Error("disabled"); };
```

Now click the toggle button. Theme should still flip on the page (the attribute swap and CSS still work) — only the persistence is lost. No JS errors should appear in the console.

Restore:

```js
Storage.prototype.setItem = orig;
```

Reload — back to normal.

- [ ] **Step 6: Cross-browser quick check (if practical)**

If multiple browsers are available locally, repeat steps 1-2 in at least one other browser (Safari/Firefox/Edge depending on what's installed). All emoji icons and CSS variables work in every modern browser, so this is just a sanity check.

- [ ] **Step 7: Commit verification notes (if anything was tweaked)**

If steps 1-6 caught any small issue (e.g., a contrast tweak, a missed hard-coded color), fix it inline and commit:

```bash
git add ui/static/style.css   # or whichever file was tweaked
git commit -m "fix(ui): <describe tweak>"
```

If nothing needed changing, no commit is needed for this task.

---

## Self-Review Notes

**Spec coverage check:**

- ✅ `data-theme` attribute strategy → Task 1 (variables) + Task 2 (Light block)
- ✅ Inline `<head>` FOUC script → Task 3
- ✅ Toggle button in header (before Sign out) → Task 4
- ✅ Catppuccin Latte palette → Task 2
- ✅ localStorage persistence with fallback → Task 5 (try/catch in `applyTheme`) + Task 3 (try/catch in inline script)
- ✅ Default Dark for new users → Task 3 (`t === "light" ? "light" : "dark"`)
- ✅ 3 hard-coded color literals aliased → Task 1 (lines 122, 139, 146)
- ✅ Button styling → Task 4
- ✅ Verification checklist (FOUC test, palette scan, fallback) → Task 6

**Departures from the spec, with reasoning:**

- Spec section "JavaScript" showed a `DOMContentLoaded` handler. The actual `app.js` does not use one — the script tag is at end-of-body and init runs at the top level. Task 5 follows the existing pattern. Behavior is identical.
- Spec recommended deciding the localStorage try/catch "during plan." Decision: include it in both the inline `<head>` script and `applyTheme`. Cost is negligible (4 lines), benefit is graceful private-browsing handling.

**Type/identifier consistency:** `applyTheme` and `toggleTheme` names are used identically across Tasks 5 step 1, step 2, and step 3. Button id `theme-toggle` is consistent across HTML (Task 4) and JS (Task 5). Variable names `--code-bg`, `--border-soft`, `--strong` consistent across Task 1 (declaration), Task 1 (use sites), and Task 2 (Light overrides).

**Placeholder scan:** No TBD/TODO/"appropriate"/"similar to" patterns. Every step has either exact code, exact commands, or exact verification checks.
