// Conversation history stored in sessionStorage
const HISTORY_KEY = 'iam_chat_history';
const MAX_TABS = 10;

let tabCount = 0;

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

function openResultsTab(label) {
  tabCount++;
  const tabId = `tab-${tabCount}`;
  const paneId = `pane-${tabCount}`;

  // Deactivate current tab
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

  // Add new tab
  const tab = document.createElement('div');
  tab.className = 'tab active';
  tab.id = tabId;
  tab.dataset.tab = String(tabCount);
  tab.textContent = label;
  tab.onclick = () => activateTab(tabCount);
  document.getElementById('tab-bar').appendChild(tab);

  // Add new pane
  const pane = document.createElement('div');
  pane.className = 'tab-pane active';
  pane.id = paneId;
  document.getElementById('tab-content').appendChild(pane);

  // Enforce max tabs
  const tabs = document.querySelectorAll('.tab');
  if (tabs.length > MAX_TABS) {
    const oldest = tabs[1]; // tabs[0] is welcome tab
    const oldestNum = oldest.dataset.tab;
    oldest.remove();
    document.getElementById(`pane-${oldestNum}`)?.remove();
  }

  return pane;
}

function activateTab(num) {
  document.querySelectorAll('.tab').forEach(t => {
    t.classList.toggle('active', t.dataset.tab === String(num));
  });
  document.querySelectorAll('.tab-pane').forEach(p => {
    p.classList.toggle('active', p.id === `pane-${num}`);
  });
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
  pane.innerHTML = marked.parse(raw);
  pane.querySelectorAll('table').forEach(enableSortableTable);
}

function deriveTabLabel(text) {
  // Use first heading found, or first 40 chars of text
  const match = text.match(/^#+\s+(.+)/m);
  if (match) return match[1].slice(0, 40);
  return text.trim().slice(0, 40) || 'Result';
}

async function sendMessage() {
  const input = document.getElementById('input');
  const text = input.value.trim();
  if (!text) return;

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
  let resultPane = null;

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

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      partial += decoder.decode(value, { stream: true });
      const lines = partial.split('\n');
      partial = lines.pop(); // keep incomplete line

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const payload = line.slice(6);

        if (payload === '[DONE]') {
          // Finalize
          aiEl.querySelector('.cursor')?.remove();
          const fullText = aiEl.textContent;
          history.push({ role: 'assistant', content: fullText });
          saveHistory(history);

          if (resultPane) renderMarkdown(resultPane, buffer);
          break;
        }

        if (payload.startsWith('[ERROR]')) {
          aiEl.querySelector('.cursor')?.remove();
          const errEl = document.createElement('span');
          errEl.className = 'msg-error';
          errEl.textContent = payload.replace('[ERROR] ', '');
          aiEl.appendChild(errEl);
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

        // Open a results tab on first chunk
        if (resultPane === null) {
          resultPane = openResultsTab('…');
        }
      }
    }

    // Update tab label once we have the full response
    if (resultPane) {
      const label = deriveTabLabel(buffer);
      const activeTab = document.querySelector('.tab.active');
      if (activeTab && activeTab.id !== 'tab-welcome') {
        activeTab.textContent = label;
      }
      renderMarkdown(resultPane, buffer);
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
