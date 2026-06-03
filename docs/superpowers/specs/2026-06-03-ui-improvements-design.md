# UI Improvements Design

**Date:** 2026-06-03
**Scope:** Frontend only (`ui/static/app.js`, `ui/static/style.css`)
**Status:** Approved

## Overview

Eight independent UX improvements to the IAM Assistant chat interface. All changes are pure frontend — no backend modifications required. Each item is self-contained and can be implemented and tested in isolation.

---

## 1. Stop Button (interrupt streaming)

**Behaviour during generation:**
- Send button label changes to "■ Stop", background colour switches to `--red` (`#f38ba8`), text colour to `--bg`.
- Input textarea gains `disabled`, opacity drops to ~0.5, placeholder changes to "Generating…".

**On Stop click:**
- Call `reader.cancel()` to abort the SSE stream.
- Remove the blinking cursor span.
- Render whatever partial content is in `buffer` as markdown.
- Push `{ role: 'assistant', content: buffer }` to history and save (same as normal completion).
- Append a `<span class="msg-error">(stopped)</span>` note inside the bubble.
- Restore Send button and re-enable input.

**Implementation notes:**
- The `AbortController` / `reader.cancel()` pattern lives entirely inside `sendMessage()`.
- No new state variables needed beyond storing the `reader` reference in a variable scoped to the current send invocation.
- On normal completion or error, the same restore-UI code path runs — refactor into a `resetInputUI()` helper to avoid duplication.

---

## 2. Placeholder Auto-Select in Templates

**Behaviour:**
- After `fillInputFromTemplate()` sets `input.value`, search for the first `<PLACEHOLDER>` token using regex `/<[A-Z][A-Z0-9_]*>/`.
- If found, call `input.setSelectionRange(start, end)` to select it instead of moving the cursor to the end.
- If no placeholder found, keep existing behaviour (cursor at end).

**Pattern matched:** Uppercase identifiers in angle brackets, e.g. `<APP_ID>`, `<BRT_ID>`, `<BC_ID>`, `<AUTH_OBJECT>`, `<IAM_APP_ID>`.

---

## 3. Code Block Copy Button

**Behaviour:**
- After `renderMarkdown()` renders HTML into a `.msg-ai` bubble, call `enableCopyButtons(pane)` which iterates all `pre` elements inside `pane`.
- For each `pre`, inject a `<button class="copy-btn">Copy</button>` as an absolutely-positioned child.
- Button is hidden by default (`opacity: 0`); revealed on `pre:hover` via CSS (`pre:hover .copy-btn { opacity: 1 }`).
- Click handler: copies `pre.querySelector('code')?.innerText ?? pre.innerText` to clipboard via `navigator.clipboard.writeText()`. On success, label changes to "Copied ✓"; reverts after 1500 ms. On failure (clipboard API unavailable), silently no-ops.

**CSS additions to `style.css`:**
```
.msg-ai pre { position: relative; }
.copy-btn { position: absolute; top: 6px; right: 6px; ... opacity: 0; transition: opacity 0.15s; }
.msg-ai pre:hover .copy-btn { opacity: 1; }
```

**No HTML changes** — button is injected via JS after markdown render.

---

## 4. Regenerate Button

**Behaviour:**
- After each completed AI response (normal or stopped), append an actions row below the `.msg-ai-wrap`:
  ```html
  <div class="msg-actions"><button class="regen-btn">↺ Regenerate</button></div>
  ```
- The `.msg-actions` div is hidden by default; revealed on `.msg-ai-wrap:hover` via CSS.
- Only the **last** AI response gets this treatment. When a new user message is sent (or a new session loaded), remove any existing `.msg-actions` divs before appending new content.
- Click handler: reads the last `user` message from `loadHistory()`, trims the last `assistant` entry from history, saves, and calls `sendMessage()` with that text pre-filled (or directly re-invokes the fetch logic).

**Regenerate logic detail:**
```
const history = loadHistory();
const lastUserMsg = [...history].reverse().find(m => m.role === 'user');
if (!lastUserMsg) return;
// Remove last assistant turn from storage
const trimmed = history.slice(0, history.lastIndexOf(/* last assistant entry */));
Sessions.saveMessages(activeId, trimmed);
// Re-run
input.value = lastUserMsg.content;
sendMessage();
```

---

## 5. Message Count in Sidebar

**Behaviour:**
- `session-time` span currently shows only relative time. Change it to `"N · 5m"` format (message count · relative time) where N is the number of messages in the session.
- Count is read from `Sessions.getMessages(id).length` — already available, no new storage.
- If count is 0, show only relative time (no "0 ·" prefix).

**CSS:** No change needed; existing `.session-time` styling accommodates the extra text.

---

## 6. Relative Time Auto-Refresh

**Behaviour:**
- On page load, after `renderSidebar()` runs, start `setInterval(() => renderSidebar(), 60_000)`.
- `renderSidebar()` is already idempotent — this requires no other changes.
- Interval is never cleared (page lifetime; acceptable for a single-tab app).

---

## 7. Welcome Page Max-Width Centering

**Change:** In `style.css`, add `margin: 0 auto` to `#welcome > .welcome`.

```css
/* before */
#welcome > .welcome { padding: 24px 20px 8px; margin: 0 auto; }

/* after */
#welcome > .welcome { padding: 24px 20px 8px; margin: 0 auto; max-width: 860px; }
```

The existing `.welcome { max-width: 720px }` rule applies to the inner content block. The `#welcome > .welcome` selector targets the padded container — adding `margin: 0 auto` there centres it on wide screens. Raise `max-width` to `860px` to give the card grid a little more breathing room while keeping it contained.

---

## 8. AI Avatar Icon

**Change:** In `appendAIMessageEl()` and `restoreChatMessages()`, replace the hardcoded text `"AI"` with `"⚡"` — matching the header logo character.

Two locations in `app.js`:
- `appendAIMessageEl()`: `avatar.textContent = 'AI'` → `avatar.textContent = '⚡'`
- `restoreChatMessages()`: same replacement

No CSS change needed — the avatar div already handles emoji rendering at the correct size.

---

## File Impact Summary

| File | Changes |
|------|---------|
| `ui/static/app.js` | Items 1, 2, 3 (JS), 4, 5, 6, 8 |
| `ui/static/style.css` | Items 3 (CSS), 7 |
| `ui/templates/index.html` | None |

All backend files (`app/`, `mcp-server/`) are untouched.
