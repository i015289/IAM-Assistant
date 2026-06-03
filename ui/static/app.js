// Sessions are stored in localStorage so they survive browser restart.
//   iam_sessions       → JSON array of {id, title, createdAt, updatedAt}
//   iam_session:<id>   → JSON array of {role, content}
// The active session id lives in sessionStorage (per-tab).
const SESSIONS_KEY = 'iam_sessions';
const ACTIVE_SESSION_KEY = 'iam_active_session';
const sessionDataKey = (id) => `iam_session:${id}`;

const Sessions = {
  list() {
    try {
      const raw = JSON.parse(localStorage.getItem(SESSIONS_KEY) || '[]');
      // Newest first by updatedAt (then createdAt as tiebreaker).
      return raw.slice().sort((a, b) =>
        (b.updatedAt || b.createdAt || 0) - (a.updatedAt || a.createdAt || 0));
    } catch { return []; }
  },

  _writeList(list) {
    localStorage.setItem(SESSIONS_KEY, JSON.stringify(list));
  },

  getMessages(id) {
    try { return JSON.parse(localStorage.getItem(sessionDataKey(id)) || '[]'); }
    catch { return []; }
  },

  saveMessages(id, messages, { now = Date.now() } = {}) {
    const list = Sessions.list();
    const idx = list.findIndex(s => s.id === id);
    if (idx < 0) {
      // Session was deleted in another tab; do not write an orphaned data blob.
      return;
    }
    localStorage.setItem(sessionDataKey(id), JSON.stringify(messages));
    list[idx] = { ...list[idx], updatedAt: now };
    Sessions._writeList(list);
  },

  create({ title = 'New session', now = Date.now() } = {}) {
    const id = crypto.randomUUID().slice(0, 8);
    const list = Sessions.list();
    list.push({ id, title, createdAt: now, updatedAt: now });
    Sessions._writeList(list);
    return id;
  },

  setTitle(id, title) {
    const list = Sessions.list();
    const idx = list.findIndex(s => s.id === id);
    if (idx < 0) return;
    list[idx] = { ...list[idx], title };
    Sessions._writeList(list);
  },

  delete(id) {
    const list = Sessions.list().filter(s => s.id !== id);
    Sessions._writeList(list);
    localStorage.removeItem(sessionDataKey(id));
    return list[0]?.id ?? null;
  },

  getActive() {
    let id = sessionStorage.getItem(ACTIVE_SESSION_KEY);
    const list = Sessions.list();
    if (id && list.some(s => s.id === id)) return id;
    if (list.length > 0) {
      sessionStorage.setItem(ACTIVE_SESSION_KEY, list[0].id);
      return list[0].id;
    }
    // No sessions exist yet — create one.
    id = Sessions.create();
    sessionStorage.setItem(ACTIVE_SESSION_KEY, id);
    return id;
  },

  setActive(id) {
    sessionStorage.setItem(ACTIVE_SESSION_KEY, id);
  },
};

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

// loadHistory / saveHistory operate on the active session.
function loadHistory() {
  return Sessions.getMessages(Sessions.getActive());
}

function saveHistory(messages) {
  Sessions.saveMessages(Sessions.getActive(), messages);
}

// Welcome block lives in a <template> so we can restore it on "New session"
// without keeping a hidden DOM node around between fresh starts.
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

function hideWelcome() {
  document.getElementById('welcome')?.remove();
}

// Auto-grow textarea up to 4 lines
document.getElementById('input').addEventListener('input', function () {
  this.style.height = 'auto';
  this.style.height = Math.min(this.scrollHeight, 96) + 'px';
});

// Enter sends, Shift+Enter newline
document.getElementById('input').addEventListener('keydown', function (e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

function appendUserMessage(text) {
  const el = document.createElement('div');
  el.className = 'msg-user';
  el.textContent = text;
  document.getElementById('messages').appendChild(el);
  scrollToBottom();
}

function appendAIMessageEl() {
  const wrap = document.createElement('div');
  wrap.className = 'msg-ai-wrap';
  wrap.innerHTML = '<div class="ai-avatar">AI</div><div class="msg-ai"><span class="cursor">▍</span></div>';
  document.getElementById('messages').appendChild(wrap);
  scrollToBottom();
  return wrap.querySelector('.msg-ai');
}

function scrollToBottom() {
  const el = document.getElementById('messages');
  el.scrollTop = el.scrollHeight;
}

function enableSortableTable(table) {
  table.querySelectorAll('th').forEach((th, colIdx) => {
    let asc = true;
    th.addEventListener('click', () => {
      const tbody = table.querySelector('tbody');
      if (!tbody) return;
      const rows = Array.from(tbody.querySelectorAll('tr'));
      rows.sort((a, b) => {
        const aText = a.cells[colIdx]?.textContent.trim() ?? '';
        const bText = b.cells[colIdx]?.textContent.trim() ?? '';
        return asc ? aText.localeCompare(bText) : bText.localeCompare(aText);
      });
      asc = !asc;
      rows.forEach(r => tbody.appendChild(r));
    });
  });
}

function renderMarkdown(pane, raw) {
  pane.innerHTML = DOMPurify.sanitize(marked.parse(raw));
  pane.querySelectorAll('table').forEach(enableSortableTable);
}

async function sendMessage() {
  const input = document.getElementById('input');
  const text = input.value.trim();
  if (!text) return;

  hideWelcome();

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

  // Auto-title from the first user message — but only if the user has not
  // renamed the session yet (default title still in place).
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

  try {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: history }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let partial = '';
    let streamDone = false;
    let streamErrored = false;

    while (!streamDone) {
      const { done, value } = await reader.read();
      if (done) {
        // Server closed the stream without [DONE] — likely a network/proxy
        // timeout. Persist whatever partial reply we have, mark as errored,
        // and append a small notice to the bubble.
        aiEl.querySelector('.cursor')?.remove();
        if (buffer.length > 0) {
          renderMarkdown(aiEl, buffer);
          history.push({ role: 'assistant', content: buffer });
          saveHistory(history);
          renderSidebar();
        }
        const errEl = document.createElement('span');
        errEl.className = 'msg-error';
        errEl.textContent = '(connection ended without completion)';
        aiEl.appendChild(errEl);
        streamErrored = true;
        break;
      }

      partial += decoder.decode(value, { stream: true });
      const lines = partial.split('\n');
      partial = lines.pop() ?? ''; // keep incomplete line

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const payload = line.slice(6);

        if (payload === '[DONE]') {
          // Finalize
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

        // Normal text chunk (JSON-encoded string)
        let chunk;
        try { chunk = JSON.parse(payload); } catch { chunk = payload; }
        buffer += chunk;

        // Update chat bubble (plain text, no markdown during streaming)
        const cursor = aiEl.querySelector('.cursor');
        const textNode = document.createTextNode(chunk);
        aiEl.insertBefore(textNode, cursor);
        scrollToBottom();
      }
    }

    // Re-render the left chat bubble with markdown now that streaming is done.
    // During streaming we appended plain text to avoid mid-parse layout flicker.
    // Skip when the stream ended in an error — that path already wrote a
    // .msg-error span to the bubble that we must not clobber.
    if (!streamErrored) {
      renderMarkdown(aiEl, buffer);
    }

  } catch (err) {
    aiEl.querySelector('.cursor')?.remove();
    const errEl = document.createElement('span');
    errEl.className = 'msg-error';
    errEl.textContent = `Error: ${err.message}`;
    aiEl.appendChild(errEl);
  } finally {
    sendBtn.disabled = false;
    input.disabled = false;
    input.focus();
  }
}

// --- Sidebar rendering & session switching -------------------------------

function relativeTime(ts) {
  if (!ts) return '';
  const diff = Date.now() - ts;
  if (diff < 60_000) return 'just now';
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h`;
  return `${Math.floor(diff / 86_400_000)}d`;
}

function renderSidebar() {
  const list = document.getElementById('session-list');
  const activeId = Sessions.getActive();
  const sessions = Sessions.list();
  list.innerHTML = '';
  for (const s of sessions) {
    const row = document.createElement('div');
    row.className = 'session-row' + (s.id === activeId ? ' active' : '');
    row.dataset.id = s.id;

    const title = document.createElement('div');
    title.className = 'session-title';
    title.textContent = s.title;
    title.title = s.title;

    const time = document.createElement('span');
    time.className = 'session-time';
    time.textContent = relativeTime(s.updatedAt);

    const del = document.createElement('button');
    del.className = 'session-delete';
    del.type = 'button';
    del.title = 'Delete session';
    del.textContent = '×';

    row.appendChild(title);
    row.appendChild(time);
    row.appendChild(del);

    // Click row → switch (but ignore clicks that originated on the delete
    // button or while editing the title).
    row.addEventListener('click', (e) => {
      if (e.target === del) return;
      if (title.classList.contains('editing')) return;
      if (s.id !== Sessions.getActive()) switchSession(s.id);
    });

    // Double-click title → inline rename.
    title.addEventListener('dblclick', (e) => {
      e.stopPropagation();
      beginRename(title, s.id, s.title);
    });

    // Click × → confirm and delete.
    del.addEventListener('click', (e) => {
      e.stopPropagation();
      if (!confirm(`Delete session "${s.title}"?`)) return;
      const wasActive = (s.id === Sessions.getActive());
      const nextActive = Sessions.delete(s.id);
      if (wasActive) {
        if (nextActive) {
          switchSession(nextActive);
        } else {
          // List empty — getActive will auto-create a fresh one.
          const fresh = Sessions.getActive();
          switchSession(fresh);
        }
      } else {
        renderSidebar();
      }
    });

    list.appendChild(row);
  }
}

function beginRename(titleEl, id, originalTitle) {
  titleEl.classList.add('editing');
  titleEl.contentEditable = 'plaintext-only';
  titleEl.textContent = originalTitle;
  titleEl.focus();
  // Select all text inside the editable element.
  const range = document.createRange();
  range.selectNodeContents(titleEl);
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);

  let finished = false;
  const finish = (commit) => {
    if (finished) return;
    finished = true;
    titleEl.contentEditable = 'false';
    titleEl.classList.remove('editing');
    const newTitle = titleEl.textContent.trim().slice(0, 80);
    if (commit && newTitle && newTitle !== originalTitle) {
      Sessions.setTitle(id, newTitle);
    }
    renderSidebar();
  };

  titleEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); finish(true); }
    else if (e.key === 'Escape') { e.preventDefault(); finish(false); }
  });
  titleEl.addEventListener('blur', () => finish(true), { once: true });
}

function switchSession(id) {
  Sessions.setActive(id);
  document.getElementById('messages').innerHTML = '';
  const input = document.getElementById('input');
  input.value = '';
  input.style.height = 'auto';
  hideWelcome();
  restoreChatMessages();
  if (loadHistory().length === 0) showWelcome();
  renderSidebar();
  input.focus();
}

// --- Startup: replay prior session into the DOM --------------------------

function restoreChatMessages() {
  // Re-render every prior turn into #messages so a refresh keeps the
  // conversation visible. Mirrors appendUserMessage / appendAIMessageEl
  // without the streaming cursor.
  const messagesEl = document.getElementById('messages');
  for (const msg of loadHistory()) {
    if (msg.role === 'user') {
      const el = document.createElement('div');
      el.className = 'msg-user';
      el.textContent = msg.content;
      messagesEl.appendChild(el);
    } else if (msg.role === 'assistant') {
      const wrap = document.createElement('div');
      wrap.className = 'msg-ai-wrap';
      const avatar = document.createElement('div');
      avatar.className = 'ai-avatar';
      avatar.textContent = 'AI';
      const bubble = document.createElement('div');
      bubble.className = 'msg-ai';
      renderMarkdown(bubble, msg.content);
      wrap.appendChild(avatar);
      wrap.appendChild(bubble);
      messagesEl.appendChild(wrap);
    }
  }
  scrollToBottom();
}

// Drop orphaned keys from older versions; harmless if absent.
sessionStorage.removeItem('iam_chat_tabs');

// One-shot migration: hoist any pre-feature in-flight conversation
// (sessionStorage-only) into a real session, then clear the legacy key.
function migrateLegacyHistory() {
  if (localStorage.getItem(SESSIONS_KEY)) return; // already migrated or fresh install
  let legacy;
  try { legacy = JSON.parse(sessionStorage.getItem('iam_chat_history') || '[]'); }
  catch { legacy = []; }
  if (legacy.length === 0) return;
  const firstUser = legacy.find(m => m.role === 'user');
  const title = firstUser
    ? firstUser.content.trim().slice(0, 40) || 'Imported session'
    : 'Imported session';
  const id = Sessions.create({ title });
  Sessions.saveMessages(id, legacy);
  Sessions.setActive(id);
}

migrateLegacyHistory();
sessionStorage.removeItem('iam_chat_history');

// Sidebar `+ New` button: create a fresh session and switch to it.
document.getElementById('sidebar-new-btn').addEventListener('click', () => {
  const id = Sessions.create();
  switchSession(id);
});

if (loadHistory().length === 0) {
  showWelcome();
}

renderSidebar();
restoreChatMessages();
