/**
 * ui.js — All DOM manipulation.
 * Takes data, produces HTML. No fetch() calls here.
 */

// ── Provider metadata ──────────────────────────────────────
const PROVIDER_META = {
  mistral:    { name: 'Mistral AI',       model: 'Mistral Small',              vision: false },
  gemini:     { name: 'Google Gemini',    model: 'Gemini 2.0 Flash',           vision: false },
  openrouter: { name: 'OpenRouter',       model: 'Gemini 2.5 Flash (free)',    vision: false },
};

const PROVIDER_ORDER = ['mistral', 'gemini', 'openrouter'];

// ── Toast queue ───────────────────────────────────────────
const toastContainer = document.getElementById('toast-container');

export function showToast(message, icon = '✓') {
  const el = document.createElement('div');
  el.className = 'toast';
  el.innerHTML = `<span>${icon}</span><span>${message}</span>`;
  toastContainer.appendChild(el);
  setTimeout(() => el.remove(), 2500);
}

// ── Textarea auto-resize ──────────────────────────────────
export function autoResize(textarea) {
  textarea.style.height = 'auto';
  textarea.style.height = Math.min(textarea.scrollHeight, 320) + 'px';
}

// ── Submit button state ───────────────────────────────────
export function setSubmitLoading(btn, loading) {
  if (loading) {
    btn.classList.add('loading');
    btn.disabled = true;
  } else {
    btn.classList.remove('loading');
  }
}

// ── Attachment preview ────────────────────────────────────
export function showAttachmentPreview(container, file, dataUrl) {
  container.innerHTML = '';
  const chip = document.createElement('div');
  chip.className = 'attachment-chip';
  chip.innerHTML = `
    <img src="${dataUrl}" alt="preview" />
    <span title="${file.name}">${file.name}</span>
    <button class="remove-attachment" id="remove-attachment-btn" aria-label="Remove attachment" type="button">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
    </button>
  `;
  container.appendChild(chip);
  container.classList.add('visible');
}

export function clearAttachmentPreview(container) {
  container.innerHTML = '';
  container.classList.remove('visible');
}

// ── Model grid initialisation ─────────────────────────────
export function initModelGrid(gridEl) {
  gridEl.innerHTML = '';
  PROVIDER_ORDER.forEach(providerId => {
    gridEl.appendChild(_createCard(providerId));
  });
}

function _createCard(providerId) {
  const meta = PROVIDER_META[providerId];
  const card = document.createElement('article');
  card.className = 'model-card';
  card.dataset.provider = providerId;
  card.setAttribute('aria-label', `${meta.name} response`);

  card.innerHTML = `
    <header class="card-header">
      <div class="provider-info">
        <span class="provider-name">${meta.name}</span>
        <span class="model-name">${meta.model}</span>
      </div>
      <div style="display:flex;align-items:center;gap:8px;">
        <span class="status-pill idle" id="status-${providerId}">
          <span class="dot"></span>
          <span class="status-text">Ready</span>
        </span>
      </div>
    </header>
    <div class="card-body" id="body-${providerId}">
      <div class="idle-state">
        <span class="idle-icon">◈</span>
        <p class="idle-text">Enter a prompt above to compare responses</p>
      </div>
    </div>
    <footer class="card-footer" id="footer-${providerId}" style="display:none;">
      <div class="card-actions">
        <button class="btn btn-ghost btn-sm copy-btn" id="copy-${providerId}" data-provider="${providerId}" aria-label="Copy response" type="button">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
          </svg>
          Copy
        </button>
        <button class="btn btn-ghost btn-sm regen-btn" id="regen-${providerId}" data-provider="${providerId}" aria-label="Regenerate ${meta.name} response" type="button">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M23 4v6h-6"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/>
          </svg>
          Regenerate
        </button>
      </div>
      <span class="latency-label" id="latency-${providerId}"></span>
    </footer>
  `;
  return card;
}

// ── Card state updates ────────────────────────────────────

export function setCardLoading(providerId) {
  _setStatus(providerId, 'loading', 'Generating…');
  const body = document.getElementById(`body-${providerId}`);
  const footer = document.getElementById(`footer-${providerId}`);
  body.innerHTML = `
    <div class="skeleton-lines" aria-live="polite" aria-label="Generating response…">
      <div class="skeleton-line"></div>
      <div class="skeleton-line"></div>
      <div class="skeleton-line"></div>
      <div class="skeleton-line"></div>
      <div class="skeleton-line"></div>
    </div>
  `;
  footer.style.display = 'none';
}

export function setCardSuccess(result) {
  const { provider, response, latency_ms } = result;
  _setStatus(provider, 'success', latency_ms != null ? `${(latency_ms / 1000).toFixed(2)}s` : 'Done');

  const body = document.getElementById(`body-${provider}`);
  const footer = document.getElementById(`footer-${provider}`);
  const latencyEl = document.getElementById(`latency-${provider}`);

  const rendered = _renderMarkdown(response || '');
  const div = document.createElement('div');
  div.className = 'markdown-body';
  div.setAttribute('aria-live', 'polite');
  div.innerHTML = rendered;

  div.querySelectorAll('pre').forEach(pre => {
    _enhanceCodeBlock(pre);
  });

  body.innerHTML = '';
  body.appendChild(div);

  if (latency_ms != null) {
    latencyEl.textContent = `${(latency_ms / 1000).toFixed(2)}s`;
  }
  footer.style.display = 'flex';
}

export function setCardError(result) {
  const { provider, status, error } = result;
  const statusMap = {
    timeout:      { label: 'Timed out',    msg: 'The provider did not respond in time.' },
    rate_limited: { label: 'Rate limited', msg: 'Rate limit reached. Try again in a moment.' },
    error:        { label: 'Error',        msg: error || 'An unexpected error occurred.' },
    unsupported:  { label: 'Unsupported',  msg: 'This model does not support the requested input type.' },
  };
  const info = statusMap[status] || statusMap.error;
  _setStatus(provider, status, info.label);

  const body = document.getElementById(`body-${provider}`);
  const footer = document.getElementById(`footer-${provider}`);

  body.innerHTML = `
    <div class="error-state" role="alert">
      <div class="error-title">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        Unable to generate response
      </div>
      <p class="error-message">${_esc(info.msg)}</p>
    </div>
  `;
  footer.style.display = 'flex';
  const latencyEl = document.getElementById(`latency-${provider}`);
  latencyEl.textContent = result.latency_ms != null ? `${(result.latency_ms / 1000).toFixed(2)}s` : '';
}

export function setCardRegenLoading(providerId) {
  setCardLoading(providerId);
}

// ── Helpers ───────────────────────────────────────────────

function _setStatus(providerId, statusClass, label) {
  const pill = document.getElementById(`status-${providerId}`);
  if (!pill) return;
  pill.className = `status-pill ${statusClass}`;
  pill.querySelector('.status-text').textContent = label;
}

function _esc(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function _renderMarkdown(text) {
  if (typeof marked === 'undefined') {
    return `<pre>${_esc(text)}</pre>`;
  }
  const raw = marked.parse(text, { gfm: true, breaks: true });
  if (typeof DOMPurify !== 'undefined') {
    return DOMPurify.sanitize(raw, {
      ALLOWED_TAGS: [
        'p','br','strong','em','del','h1','h2','h3','h4','h5','h6',
        'ul','ol','li','a','code','pre','blockquote','table','thead',
        'tbody','tr','th','td','hr','img','span','div',
      ],
      ALLOWED_ATTR: ['href','src','alt','class','target','rel'],
    });
  }
  return raw;
}

function _enhanceCodeBlock(pre) {
  const code = pre.querySelector('code');
  if (!code) return;

  const langClass = Array.from(code.classList).find(c => c.startsWith('language-'));
  const lang = langClass ? langClass.replace('language-', '') : 'code';

  const header = document.createElement('div');
  header.className = 'code-block-header';
  header.innerHTML = `
    <span class="code-lang">${_esc(lang)}</span>
    <button class="copy-code-btn" type="button" aria-label="Copy code">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="9" y="9" width="13" height="13" rx="2"/>
        <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
      </svg>
      Copy
    </button>
  `;
  header.querySelector('.copy-code-btn').addEventListener('click', () => {
    navigator.clipboard.writeText(code.innerText).then(() => {
      showToast('Code copied!');
    });
  });
  pre.insertBefore(header, code);
}

// ── Get response text for clipboard ──────────────────────
export function getResponseText(providerId) {
  const body = document.getElementById(`body-${providerId}`);
  return body ? body.innerText : '';
}

// ── Reset all cards to idle ───────────────────────────────
export function resetCards() {
  PROVIDER_ORDER.forEach(providerId => {
    _setStatus(providerId, 'idle', 'Ready');
    const body = document.getElementById(`body-${providerId}`);
    const footer = document.getElementById(`footer-${providerId}`);
    if (body) {
      body.innerHTML = `
        <div class="idle-state">
          <span class="idle-icon">◈</span>
          <p class="idle-text">Enter a prompt above to compare responses</p>
        </div>
      `;
    }
    if (footer) footer.style.display = 'none';
  });
}
