/**
 * app.js — Main application entry point.
 */

import State from './state.js';
import { sendChat, regenerateProvider } from './api.js';
import {
  autoResize,
  setSubmitLoading,
  showAttachmentPreview,
  clearAttachmentPreview,
  initModelGrid,
  setCardLoading,
  setCardSuccess,
  setCardError,
  setCardRegenLoading,
  getResponseText,
  resetCards,
  showToast,
} from './ui.js';

// ── DOM refs ───────────────────────────────────────────────
const promptTextarea   = document.getElementById('prompt-textarea');
const submitBtn        = document.getElementById('submit-btn');
const attachBtn        = document.getElementById('attach-btn');
const fileInput        = document.getElementById('file-input');
const attachPreview    = document.getElementById('attachment-preview');
const modelGrid        = document.getElementById('model-grid');
const newChatBtn       = document.getElementById('new-chat-btn');
const responsesSection = document.getElementById('responses-section');

// ── Initialise ─────────────────────────────────────────────
initModelGrid(modelGrid);
_updateSubmitState();

// ── Textarea ───────────────────────────────────────────────
promptTextarea.addEventListener('input', () => {
  autoResize(promptTextarea);
  State.set({ prompt: promptTextarea.value });
  _updateSubmitState();
});

promptTextarea.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    if (!submitBtn.disabled) _submit();
  }
  if (e.key === 'Escape') {
    promptTextarea.value = '';
    State.set({ prompt: '' });
    _updateSubmitState();
    autoResize(promptTextarea);
  }
});

// ── Submit ─────────────────────────────────────────────────
submitBtn.addEventListener('click', _submit);

async function _submit() {
  const prompt = promptTextarea.value.trim();
  if (!prompt && !State.get('attachment')) return;

  const attachment = State.get('attachment');

  State.set({
    isLoading: true,
    lastPrompt: prompt,
    lastAttachment: attachment,
  });

  responsesSection.hidden = false;

  ['mistral', 'gemini', 'openrouter'].forEach(setCardLoading);
  setSubmitLoading(submitBtn, true);
  submitBtn.disabled = true;

  try {
    const data = await sendChat(
      prompt,
      attachment?.b64 ?? null,
      attachment?.mime ?? null,
    );

    data.results.forEach(result => {
      if (result.status === 'success') {
        setCardSuccess(result);
      } else {
        setCardError(result);
      }
    });

  } catch (err) {
    showToast(`Request failed: ${err.message}`, '⚠');
    ['mistral', 'gemini', 'openrouter'].forEach(p => {
      setCardError({ provider: p, status: 'error', error: err.message, latency_ms: null });
    });
  } finally {
    State.set({ isLoading: false });
    setSubmitLoading(submitBtn, false);
    _updateSubmitState();
  }
}

// ── File attachment ────────────────────────────────────────
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
const MAX_SIZE_MB = 10;

attachBtn.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', () => {
  const file = fileInput.files[0];
  if (!file) return;

  if (!ALLOWED_TYPES.includes(file.type)) {
    showToast('Only JPEG, PNG and WebP images are supported.', '⚠');
    fileInput.value = '';
    return;
  }

  if (file.size > MAX_SIZE_MB * 1024 * 1024) {
    showToast(`Image must be under ${MAX_SIZE_MB} MB.`, '⚠');
    fileInput.value = '';
    return;
  }

  const reader = new FileReader();
  reader.onload = e => {
    const dataUrl = e.target.result;
    const b64 = dataUrl.split(',')[1];

    State.set({
      attachment: { dataUrl, b64, mime: file.type, name: file.name },
    });
    showAttachmentPreview(attachPreview, file, dataUrl);
    _updateSubmitState();
  };
  reader.readAsDataURL(file);
  fileInput.value = '';
});

// ── Remove attachment ──────────────────────────────────────
attachPreview.addEventListener('click', e => {
  if (e.target.closest('#remove-attachment-btn')) {
    State.set({ attachment: null });
    clearAttachmentPreview(attachPreview);
    _updateSubmitState();
  }
});

// ── New conversation ───────────────────────────────────────
newChatBtn.addEventListener('click', () => {
  promptTextarea.value = '';
  autoResize(promptTextarea);
  State.set({ prompt: '', attachment: null, lastPrompt: '', lastAttachment: null });
  clearAttachmentPreview(attachPreview);
  resetCards();
  _updateSubmitState();
  promptTextarea.focus();
  showToast('New conversation started');
});

// ── Model card actions (copy + regenerate) ─────────────────
modelGrid.addEventListener('click', async e => {
  const copyBtn = e.target.closest('.copy-btn');
  if (copyBtn) {
    const provider = copyBtn.dataset.provider;
    const text = getResponseText(provider);
    await navigator.clipboard.writeText(text);
    showToast('Response copied!');
    return;
  }

  const regenBtn = e.target.closest('.regen-btn');
  if (regenBtn) {
    const provider = regenBtn.dataset.provider;
    const lastPrompt = State.get('lastPrompt');
    const lastAttachment = State.get('lastAttachment');

    if (!lastPrompt) {
      showToast('No previous prompt to regenerate', '⚠');
      return;
    }

    setCardRegenLoading(provider);

    try {
      const result = await regenerateProvider(
        provider,
        lastPrompt,
        lastAttachment?.b64 ?? null,
        lastAttachment?.mime ?? null,
      );
      if (result.status === 'success') {
        setCardSuccess(result);
      } else {
        setCardError(result);
      }
    } catch (err) {
      setCardError({ provider, status: 'error', error: err.message, latency_ms: null });
      showToast(`Regenerate failed: ${err.message}`, '⚠');
    }
    return;
  }
});

// ── Submit button state ────────────────────────────────────
function _updateSubmitState() {
  const prompt = promptTextarea.value.trim();
  const attachment = State.get('attachment');
  const isLoading = State.get('isLoading');
  submitBtn.disabled = (!prompt && !attachment) || isLoading;
}
