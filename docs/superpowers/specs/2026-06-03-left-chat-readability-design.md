# Left Chat Readability — Design

**Date:** 2026-06-03
**Scope:** UI only — `ui/static/style.css`, `ui/static/app.js`
**Goal:** Make the left-hand AI chat bubble readable for typical IAM answers (lists, tables, code blocks, inline tokens).

## Problem

The left chat panel renders AI responses as plain text. `app.js:244` appends each streaming chunk as a `textNode`; on stream completion only the right-hand results tab is run through `renderMarkdown` (`app.js:262`). Replay of history (`restoreChatMessages`, `app.js:300`) also writes `textContent`. Result: lists, headings, tables, fenced code, and inline `code` all appear as one undifferentiated paragraph.

`.msg-ai` (`style.css:65-69`) sets only background, radius, padding, and `line-height: 1.5`. Even if we did render markdown, no child-element styles exist to format it.

The right-hand `#tab-pane` already has a complete markdown stylesheet (`style.css:113-136`) — we mirror that style with small differences scoped to `.msg-ai`.

## Design

### 1. Render strategy

Keep streaming behaviour as-is (plain-text `textNode` insertion) — rendering half-formed markdown mid-stream causes layout flicker. On stream completion, replace bubble contents once with rendered markdown, reusing the existing `renderMarkdown(pane, raw)` helper (`app.js:155-157`).

Two call sites change:

- `app.js:262` — after rendering the results tab, also call `renderMarkdown(aiEl, buffer)`.
- `app.js:300` (`restoreChatMessages`) — replace `bubble.textContent = msg.content` with `renderMarkdown(bubble, msg.content)`.

The streaming cursor (`<span class="cursor">▍</span>`) is removed naturally when `renderMarkdown` overwrites `innerHTML`. Error spans (`msg-error`) continue to use `textContent` — no change.

### 2. CSS — markdown styles scoped to `.msg-ai`

Replace the current `.msg-ai` rule and add child-element rules. All selectors are scoped under `.msg-ai` so the right-hand tab styles are untouched.

```css
.msg-ai {
  background: var(--surface);
  border: 1px solid #2a2b3d;
  border-radius: 2px 14px 14px 14px;
  padding: 14px 16px;
  font-size: 14.5px;
  line-height: 1.7;
}
.msg-ai > :first-child { margin-top: 0; }
.msg-ai > :last-child  { margin-bottom: 0; }

.msg-ai h1, .msg-ai h2, .msg-ai h3 {
  color: var(--accent); font-size: 13px; font-weight: 700;
  margin: 14px 0 6px; letter-spacing: 0.02em;
}
.msg-ai p  { margin: 0 0 10px; }
.msg-ai ul, .msg-ai ol { padding-left: 20px; margin: 0 0 10px; }
.msg-ai li { margin: 3px 0; }
.msg-ai strong { color: #f5e0dc; }

.msg-ai code {
  background: var(--border); padding: 1px 5px; border-radius: 3px;
  font-size: 12.5px; font-family: ui-monospace, monospace; color: var(--amber);
}
.msg-ai pre {
  background: #11111b; border: 1px solid #2a2b3d;
  padding: 10px 12px; border-radius: 6px; overflow-x: auto;
  margin: 8px 0 12px;
}
.msg-ai pre code { background: none; padding: 0; color: var(--text); font-size: 12px; }

.msg-ai table { width: 100%; border-collapse: collapse; font-size: 12.5px; margin: 6px 0 10px; }
.msg-ai th { text-align: left; padding: 6px 8px; color: var(--accent);
             font-weight: 600; border-bottom: 1px solid var(--border); }
.msg-ai td { padding: 6px 8px; border-bottom: 1px solid var(--bg); }
```

`#2a2b3d` sits between `--surface` (#181825) and `--border` (#313244). Used twice (bubble border + pre border); not promoted to a CSS variable to avoid noise.

### 3. Width

`#chat-panel` (`style.css:44`): `width: 42%` → `width: 50%`. Long IAM answers (catalogs, role tables) get a usable column instead of a narrow strip; the right results panel still owns the tabs and full-fidelity rendering.

`.msg-ai-wrap` (`style.css:59`): `max-width: 90%` → `max-width: 95%`. Tables and code blocks need horizontal room; the avatar still anchors the bubble to the left.

`.msg-user` (`max-width: 85%`) stays — the right-aligned offset is more valuable than width for short user prompts.

### 4. Cursor & error handling

- Streaming cursor removal: implicit, via `innerHTML` replacement in `renderMarkdown`.
- Errors (`.msg-error`): unchanged, still rendered as `textContent`.

## Out of Scope

- Right results panel styles (`#tab-pane`) — already styled.
- Light/dark theming or palette tokens — current Catppuccin-style palette retained.
- Markdown library swaps — continue using `marked` + `DOMPurify`.
- User-message styling.
- Streaming-time markdown rendering (rejected: flicker).

## Verification

After implementation, visually confirm in `localhost`:

1. Send an IAM query that produces headings, a list, a table, fenced SQL, and inline `code`. All should render in the left bubble.
2. Refresh the page mid-conversation; replayed history must render the same way (not as plain text).
3. Trigger an error (e.g. disconnect MCP); error span continues to render plainly.
4. Confirm chat panel now occupies 50% width and bubbles can host wide tables without horizontal scroll on a typical 1440px display.
