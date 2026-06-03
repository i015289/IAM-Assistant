// Conversation history is persisted in sessionStorage so a refresh inside
// the same browser tab keeps the prior conversation visible.
const HISTORY_KEY = 'iam_chat_history';

function loadHistory() {
  try { return JSON.parse(sessionStorage.getItem(HISTORY_KEY) || '[]'); }
  catch { return []; }
}

function saveHistory(messages) {
  sessionStorage.setItem(HISTORY_KEY, JSON.stringify(messages));
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

  document.getElementById('welcome')?.remove();

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

if (loadHistory().length > 0) {
  document.getElementById('welcome')?.remove();
}

restoreChatMessages();
