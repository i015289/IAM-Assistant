# UI Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 8 independent UX improvements to the IAM Assistant chat UI: stop button, placeholder auto-select, code copy button, regenerate button, sidebar message count, time auto-refresh, welcome centering, and AI avatar icon.

**Architecture:** All changes are pure frontend. `ui/static/app.js` receives most logic changes; `ui/static/style.css` receives CSS additions for copy button hover and regenerate button hover. No backend, no HTML template, no new files.

**Tech Stack:** Vanilla JS (ES2020), CSS custom properties, `navigator.clipboard` API, `ReadableStreamDefaultReader.cancel()`

---

## File Map

| File | What changes |
|------|-------------|
| `ui/static/app.js` | `sendMessage()` refactor + stop, `fillInputFromTemplate()` placeholder select, `enableCopyButtons()` new helper, `attachRegenButton()` new helper, `removeRegenButtons()` new helper, `renderSidebar()` message count, startup `setInterval`, `appendAIMessageEl()` + `restoreChatMessages()` avatar |
| `ui/static/style.css` | `.copy-btn` styles, `.msg-ai pre` position relative, `.msg-actions` + `.regen-btn` styles |

---

### Task 1: Cosmetic quick wins — avatar, welcome centering, time auto-refresh

Small, zero-risk changes. Do these first to get a clean commit before touching complex logic.

**Files:**
- Modify: `ui/static/app.js` (lines ~420–427 `appendAIMessageEl`, ~743–757 `restoreChatMessages`, ~809 startup block)
- Modify: `ui/static/style.css` (line ~99 `#welcome > .welcome`)

- [ ] **Step 1: Change AI avatar text to ⚡ in `appendAIMessageEl()`**

In `app.js`, find:
```js
wrap.innerHTML = '<div class="ai-avatar">AI</div><div class="msg-ai"><span class="cursor">▍</span></div>';
```
Change to:
```js
wrap.innerHTML = '<div class="ai-avatar">⚡</div><div class="msg-ai"><span class="cursor">▍</span></div>';
```

- [ ] **Step 2: Change AI avatar text to ⚡ in `restoreChatMessages()`**

In `app.js`, find:
```js
avatar.textContent = 'AI';
```
Change to:
```js
avatar.textContent = '⚡';
```

- [ ] **Step 3: Fix welcome page centering in `style.css`**

Find the existing rule:
```css
#welcome > .welcome {
  padding: 24px 20px 8px;
  margin: 0 auto;
}
```
Change to:
```css
#welcome > .welcome {
  padding: 24px 20px 8px;
  margin: 0 auto;
  max-width: 860px;
}
```

- [ ] **Step 4: Add sidebar time auto-refresh at startup**

At the very bottom of `app.js`, after the existing startup block:
```js
renderSidebar();
restoreChatMessages();
```
Add:
```js
setInterval(() => renderSidebar(), 60_000);
```

- [ ] **Step 5: Verify in browser**

Start the app and open the UI. Check:
- AI avatar shows ⚡ instead of "AI"
- Welcome screen cards are centred on a wide window (not edge-to-edge)
- No console errors

- [ ] **Step 6: Commit**

```bash
git add ui/static/app.js ui/static/style.css
git commit -m "feat(ui): avatar icon, welcome centering, sidebar time auto-refresh"
```

---

### Task 2: Sidebar message count

**Files:**
- Modify: `ui/static/app.js` (`renderSidebar()` function, around line ~636)

- [ ] **Step 1: Update `renderSidebar()` to show message count**

In `renderSidebar()`, find the block that builds `time`:
```js
const time = document.createElement('span');
time.className = 'session-time';
time.textContent = relativeTime(s.updatedAt);
```
Replace with:
```js
const time = document.createElement('span');
time.className = 'session-time';
const msgCount = Sessions.getMessages(s.id).length;
const rel = relativeTime(s.updatedAt);
time.textContent = msgCount > 0 ? `${msgCount} · ${rel}` : rel;
```

- [ ] **Step 2: Verify in browser**

Open the sidebar. Sessions that have messages should show e.g. `"6 · 3m"`. A brand-new empty session shows only `"just now"`.

- [ ] **Step 3: Commit**

```bash
git add ui/static/app.js
git commit -m "feat(ui): show message count in sidebar session list"
```

---

### Task 3: Placeholder auto-select in templates

**Files:**
- Modify: `ui/static/app.js` (`fillInputFromTemplate()`, around line ~384)

- [ ] **Step 1: Update `fillInputFromTemplate()` to select first placeholder**

Find the existing function:
```js
function fillInputFromTemplate(prompt) {
  const input = document.getElementById('input');
  input.value = prompt;
  input.dispatchEvent(new Event('input'));
  input.focus();
  input.setSelectionRange(prompt.length, prompt.length);
}
```
Replace with:
```js
function fillInputFromTemplate(prompt) {
  const input = document.getElementById('input');
  input.value = prompt;
  input.dispatchEvent(new Event('input'));
  input.focus();
  const match = prompt.match(/<[A-Z][A-Z0-9_]*>/);
  if (match) {
    input.setSelectionRange(match.index, match.index + match[0].length);
  } else {
    input.setSelectionRange(prompt.length, prompt.length);
  }
}
```

- [ ] **Step 2: Verify in browser**

Click a template card that contains a placeholder like `<APP_ID>`. The text `<APP_ID>` should be highlighted/selected in the input box so typing immediately replaces it. Click a "Getting Started" card (no placeholder) — cursor should land at the end.

- [ ] **Step 3: Commit**

```bash
git add ui/static/app.js
git commit -m "feat(ui): auto-select first placeholder when filling template"
```

---

### Task 4: Code block copy button

**Files:**
- Modify: `ui/static/style.css` (add copy button styles)
- Modify: `ui/static/app.js` (new `enableCopyButtons()` helper, call it from `renderMarkdown()`)

- [ ] **Step 1: Add CSS for copy button**

Append to the end of `style.css`:
```css
/* Code block copy button */
.msg-ai pre { position: relative; }
.copy-btn {
  position: absolute; top: 6px; right: 6px;
  background: var(--border); color: var(--muted);
  border: 1px solid var(--muted); border-radius: 4px;
  padding: 2px 8px; font-size: 11px; font-family: inherit;
  cursor: pointer; opacity: 0; transition: opacity 0.15s;
  line-height: 1.6;
}
.msg-ai pre:hover .copy-btn { opacity: 1; }
.copy-btn:hover { color: var(--text); border-color: var(--text); }
```

- [ ] **Step 2: Add `enableCopyButtons()` helper to `app.js`**

After the existing `enableSortableTable()` function (around line ~434), add:
```js
function enableCopyButtons(pane) {
  pane.querySelectorAll('pre').forEach(pre => {
    if (pre.querySelector('.copy-btn')) return; // already injected
    const btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.textContent = 'Copy';
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const text = pre.querySelector('code')?.innerText ?? pre.innerText;
      try {
        await navigator.clipboard.writeText(text);
        btn.textContent = 'Copied ✓';
        setTimeout(() => { btn.textContent = 'Copy'; }, 1500);
      } catch { /* clipboard unavailable — silent no-op */ }
    });
    pre.appendChild(btn);
  });
}
```

- [ ] **Step 3: Call `enableCopyButtons()` from `renderMarkdown()`**

Find `renderMarkdown()`:
```js
function renderMarkdown(pane, raw) {
  pane.innerHTML = DOMPurify.sanitize(marked.parse(raw));
  pane.querySelectorAll('table').forEach(enableSortableTable);
}
```
Change to:
```js
function renderMarkdown(pane, raw) {
  pane.innerHTML = DOMPurify.sanitize(marked.parse(raw));
  pane.querySelectorAll('table').forEach(enableSortableTable);
  enableCopyButtons(pane);
}
```

- [ ] **Step 4: Verify in browser**

Ask a question that produces a code block. Hover over the code block — "Copy" button should appear top-right. Click it — button changes to "Copied ✓" then back to "Copy". Paste elsewhere to confirm correct content copied.

- [ ] **Step 5: Commit**

```bash
git add ui/static/app.js ui/static/style.css
git commit -m "feat(ui): copy button on code blocks"
```

---

### Task 5: Stop button + UI state reset refactor

This is the most complex change. **Must be done after Task 6** because `sendMessage()` calls `removeRegenButtons()` and `attachRegenButton()`, which are defined in Task 6. Complete Task 6 first, then come back here.

**Files:**
- Modify: `ui/static/app.js` (`sendMessage()`, around lines ~457–592)

- [ ] **Step 1: Extract `resetInputUI()` helper**

Before `sendMessage()`, add this new helper:
```js
function resetInputUI() {
  const sendBtn = document.getElementById('send-btn');
  const input = document.getElementById('input');
  sendBtn.textContent = 'Send';
  sendBtn.style.background = '';
  sendBtn.style.color = '';
  sendBtn.disabled = false;
  input.disabled = false;
  input.placeholder = 'Ask about roles, catalogs, SoD…';
  input.style.opacity = '';
  input.focus();
}
```

- [ ] **Step 2: Add `setGeneratingUI()` helper**

Right after `resetInputUI()`, add:
```js
function setGeneratingUI(onStop) {
  const sendBtn = document.getElementById('send-btn');
  const input = document.getElementById('input');
  sendBtn.textContent = '■ Stop';
  sendBtn.style.background = 'var(--red)';
  sendBtn.style.color = 'var(--bg)';
  sendBtn.disabled = false;
  sendBtn.onclick = onStop;
  input.disabled = true;
  input.placeholder = 'Generating…';
  input.style.opacity = '0.5';
}
```

- [ ] **Step 3: Refactor `sendMessage()` to use helpers and support Stop**

Replace the entire `sendMessage()` function with:
```js
async function sendMessage() {
  const input = document.getElementById('input');
  const text = input.value.trim();
  if (!text) return;

  hideWelcome();
  removeRegenButtons();

  const sendBtn = document.getElementById('send-btn');
  input.value = '';
  input.style.height = 'auto';
  sendBtn.disabled = true;
  input.disabled = true;

  appendUserMessage(text);

  const history = loadHistory();
  const isFirstUserMessage = history.every(m => m.role !== 'user');
  history.push({ role: 'user', content: text });
  saveHistory(history);

  if (isFirstUserMessage) {
    const activeId = Sessions.getActive();
    const meta = Sessions.list().find(s => s.id === activeId);
    if (meta && meta.title === 'New session') {
      const t = text.trim();
      const newTitle = t.length > 40 ? t.slice(0, 40) + '…' : t;
      Sessions.setTitle(activeId, newTitle || 'New session');
      renderSidebar();
    }
  }

  const aiEl = appendAIMessageEl();
  let buffer = '';
  let reader = null;
  let stopped = false;

  const stopHandler = () => {
    stopped = true;
    reader?.cancel();
  };

  setGeneratingUI(stopHandler);

  try {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: history }),
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    reader = response.body.getReader();
    const decoder = new TextDecoder();
    let partial = '';
    let streamDone = false;
    let streamErrored = false;

    while (!streamDone) {
      const { done, value } = await reader.read();
      if (done || stopped) {
        aiEl.querySelector('.cursor')?.remove();
        if (buffer.length > 0) {
          renderMarkdown(aiEl, buffer);
          history.push({ role: 'assistant', content: buffer });
          saveHistory(history);
          renderSidebar();
        }
        if (stopped) {
          const errEl = document.createElement('span');
          errEl.className = 'msg-error';
          errEl.textContent = '(stopped)';
          aiEl.appendChild(errEl);
        } else if (done) {
          const errEl = document.createElement('span');
          errEl.className = 'msg-error';
          errEl.textContent = '(connection ended without completion)';
          aiEl.appendChild(errEl);
          streamErrored = true;
        }
        streamDone = true;
        break;
      }

      partial += decoder.decode(value, { stream: true });
      const lines = partial.split('\n');
      partial = lines.pop() ?? '';

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const payload = line.slice(6);

        if (payload === '[DONE]') {
          aiEl.querySelector('.cursor')?.remove();
          history.push({ role: 'assistant', content: buffer });
          saveHistory(history);
          renderSidebar();
          streamDone = true;
          break;
        }

        if (payload.startsWith('[ERROR]')) {
          aiEl.querySelector('.cursor')?.remove();
          const errEl = document.createElement('span');
          errEl.className = 'msg-error';
          errEl.textContent = payload.replace('[ERROR] ', '');
          aiEl.appendChild(errEl);
          streamErrored = true;
          streamDone = true;
          break;
        }

        let chunk;
        try { chunk = JSON.parse(payload); } catch { chunk = payload; }
        buffer += chunk;

        const cursor = aiEl.querySelector('.cursor');
        const textNode = document.createTextNode(chunk);
        aiEl.insertBefore(textNode, cursor);
        scrollToBottom();
      }
    }

    if (!streamErrored && !stopped) {
      renderMarkdown(aiEl, buffer);
    }
    if (!streamErrored) {
      attachRegenButton(aiEl.closest('.msg-ai-wrap'));
    }

  } catch (err) {
    if (!stopped) {
      aiEl.querySelector('.cursor')?.remove();
      const errEl = document.createElement('span');
      errEl.className = 'msg-error';
      errEl.textContent = `Error: ${err.message}`;
      aiEl.appendChild(errEl);
    }
  } finally {
    sendBtn.onclick = sendMessage;
    resetInputUI();
  }
}
```

- [ ] **Step 4: Fix the Send button's original `onclick`**

In `index.html` the send button has `onclick="sendMessage()"` — that stays. But inside `setGeneratingUI` we temporarily override `sendBtn.onclick`. The `finally` block restores it with `sendBtn.onclick = sendMessage`. This is correct — no HTML change needed.

- [ ] **Step 5: Verify in browser**

Send a message. While generating: button says "■ Stop" in red, input is dimmed. Click Stop — generation halts, partial reply persists, "(stopped)" appears, input re-enables. Send another message — everything works normally.

- [ ] **Step 6: Commit**

```bash
git add ui/static/app.js
git commit -m "feat(ui): stop button — interrupt streaming mid-response"
```

---

### Task 6: Regenerate button

**Do this BEFORE Task 5** — `sendMessage()` in Task 5 calls `removeRegenButtons()` and `attachRegenButton()`. These helpers must exist before `sendMessage()` is rewritten.

**Files:**
- Modify: `ui/static/style.css` (add `.msg-actions` and `.regen-btn` styles)
- Modify: `ui/static/app.js` (new `attachRegenButton()`, `removeRegenButtons()` helpers)

- [ ] **Step 1: Add CSS for regenerate button**

Append to the end of `style.css`:
```css
/* Regenerate button */
.msg-actions {
  display: flex; gap: 6px; margin-top: 4px; margin-left: 34px;
  visibility: hidden;
}
.msg-ai-wrap:hover + .msg-actions,
.msg-actions:hover { visibility: visible; }
.regen-btn {
  background: transparent; color: var(--muted);
  border: 1px solid var(--border); border-radius: 4px;
  padding: 3px 10px; font-size: 11px; font-family: inherit;
  cursor: pointer;
}
.regen-btn:hover { color: var(--text); border-color: var(--text); }
```

- [ ] **Step 2: Add `removeRegenButtons()` helper**

Before `sendMessage()` in `app.js`, add:
```js
function removeRegenButtons() {
  document.querySelectorAll('.msg-actions').forEach(el => el.remove());
}
```

- [ ] **Step 3: Add `attachRegenButton()` helper**

After `removeRegenButtons()`, add:
```js
function attachRegenButton(wrapEl) {
  removeRegenButtons();
  if (!wrapEl) return;
  const actions = document.createElement('div');
  actions.className = 'msg-actions';
  const btn = document.createElement('button');
  btn.className = 'regen-btn';
  btn.textContent = '↺ Regenerate';
  btn.addEventListener('click', async () => {
    const history = loadHistory();
    const lastUserIdx = [...history].map((m, i) => m.role === 'user' ? i : -1)
                                    .filter(i => i >= 0).at(-1);
    if (lastUserIdx === undefined) return;
    const lastUserContent = history[lastUserIdx].content;
    // Trim everything after (and including) the last assistant turn that follows
    const trimmed = history.slice(0, lastUserIdx + 1);
    // Remove last user message too — sendMessage re-adds it
    const withoutLast = trimmed.slice(0, lastUserIdx);
    Sessions.saveMessages(Sessions.getActive(), withoutLast);
    removeRegenButtons();
    // Remove the last user bubble and AI bubble from DOM
    const messages = document.getElementById('messages');
    // Remove last two children (user msg + ai wrap)
    if (messages.lastElementChild) messages.lastElementChild.remove();
    if (messages.lastElementChild) messages.lastElementChild.remove();
    const input = document.getElementById('input');
    input.value = lastUserContent;
    input.dispatchEvent(new Event('input'));
    await sendMessage();
  });
  actions.appendChild(btn);
  wrapEl.insertAdjacentElement('afterend', actions);
}
```

- [ ] **Step 4: Verify in browser**

After an AI reply finishes, hover over the bubble — "↺ Regenerate" appears below it. Click it — the last exchange is cleared from DOM and history, the question is re-submitted, a new reply streams in. After that new reply, Regenerate appears again on the new bubble.

- [ ] **Step 5: Verify Regenerate is removed on new message**

Type and send a new message while a Regenerate button is visible — it should disappear before the new exchange appears. (`removeRegenButtons()` is called at the top of `sendMessage()`.)

- [ ] **Step 6: Commit**

```bash
git add ui/static/app.js ui/static/style.css
git commit -m "feat(ui): regenerate button on last AI reply"
```

---

### Task 7: Smoke-test all 8 features end-to-end

No code changes. Verification only.

- [ ] **Step 1: Avatar** — Open app, start a chat. AI bubble shows ⚡, not "AI". Reload page — still ⚡ on restored messages.

- [ ] **Step 2: Welcome centering** — Open on a wide window (>1400px). Template cards should stop expanding and stay centred.

- [ ] **Step 3: Time auto-refresh** — Leave the page open for 1 minute. Sidebar relative times increment without a page refresh. (Tip: create a session, wait, watch "just now" become "1m".)

- [ ] **Step 4: Message count** — Open app with existing sessions. Sessions with messages show `"N · Xm"` format. A fresh empty session shows only `"just now"`.

- [ ] **Step 5: Placeholder select** — Click "App → Catalog mapping" template. `<APP_ID>` should be selected/highlighted. Type `F1443A_TRAN` — it replaces the placeholder. Click a "Getting Started" template — cursor lands at end.

- [ ] **Step 6: Copy button** — Ask a question that returns SQL or code. Hover the code block — "Copy" button appears. Click — changes to "Copied ✓". Paste in a text editor — correct code is pasted.

- [ ] **Step 7: Stop button** — Send a long query. While generating, button shows "■ Stop" in red, input dims to "Generating…". Click Stop — partial reply persists with "(stopped)" note, input re-enables, next question works normally.

- [ ] **Step 8: Regenerate** — Complete a query. Hover AI bubble — "↺ Regenerate" appears. Click — same question re-runs, new reply appears. Send a new message — Regenerate button from previous exchange is gone.

- [ ] **Step 9: Commit final verification note**

```bash
git commit --allow-empty -m "chore: all 8 UI improvements verified end-to-end"
```
