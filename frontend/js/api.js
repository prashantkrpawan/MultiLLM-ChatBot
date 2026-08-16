/**
 * api.js — HTTP communication layer.
 */

const BASE = '/api';

export async function sendChat(message, attachmentB64 = null, attachmentMime = null) {
  const body = { message };
  if (attachmentB64) {
    body.attachment = attachmentB64;
    body.attachment_mime = attachmentMime;
  }

  const res = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed: HTTP ${res.status}`);
  }

  return res.json();
}

export async function regenerateProvider(providerId, message, attachmentB64 = null, attachmentMime = null) {
  const body = { message };
  if (attachmentB64) {
    body.attachment = attachmentB64;
    body.attachment_mime = attachmentMime;
  }

  const res = await fetch(`${BASE}/chat/regenerate/${providerId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Regenerate failed: HTTP ${res.status}`);
  }

  return res.json();
}

export async function fetchProviders() {
  const res = await fetch(`${BASE}/providers`);
  if (!res.ok) throw new Error('Failed to fetch providers');
  return res.json();
}
