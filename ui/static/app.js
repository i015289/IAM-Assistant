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
    localStorage.setItem(sessionDataKey(id), JSON.stringify(messages));
    const list = Sessions.list();
    const idx = list.findIndex(s => s.id === id);
    if (idx >= 0) {
      list[idx] = { ...list[idx], updatedAt: now };
      Sessions._writeList(list);
    }
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

// loadHistory / saveHistory remain shims over the active session for now.
// They're rewired to Sessions in Task 4.
function loadHistory() {
  try { return JSON.parse(sessionStorage.getItem('iam_chat_history') || '[]'); }
  catch { return []; }
}

function saveHistory(messages) {
  sessionStorage.setItem('iam_chat_history', JSON.stringify(messages));
}

// Welcome block lives in a <template> so we can restore it on "New session"
// without keeping a hidden DOM node around between fresh starts.
function showWelcome() {
  if (document.getElementById('welcome')) return; // already shown
  const tpl = document.getElementById('welcome-template');
  const node = tpl.content.firstElementChild.cloneNode(true);
  const chatPanel = document.getElementById('chat-panel');
  chatPanel.insertBefore(node, document.getElementById('messages'));
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
  history.push({ role: 'user', content: text });
  saveHistory(history);

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
      if (done) break;

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

// Drop the orphaned tab-state key from older versions; harmless if absent.
sessionStorage.removeItem('iam_chat_tabs');

// "New session" button: clear history and DOM, restore welcome.
document.getElementById('new-session-btn').addEventListener('click', () => {
  sessionStorage.removeItem(HISTORY_KEY);
  document.getElementById('messages').innerHTML = '';
  const input = document.getElementById('input');
  input.value = '';
  input.style.height = 'auto';
  showWelcome();
  input.focus();
});

if (loadHistory().length === 0) {
  showWelcome();
}

restoreChatMessages();
