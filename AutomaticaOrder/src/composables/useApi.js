const _cache = new Map();
const DEFAULT_TTL_MS = 30_000;
const DEFAULT_TIMEOUT_MS = 10_000;

export function getApiBase() {
  try {
    return (window.API_BASE_URL || 'https://api.wen-xc.site').replace(/\/$/, '');
  } catch {
    return 'https://api.wen-xc.site';
  }
}

export async function apiGet(path, { ttlMs = DEFAULT_TTL_MS, timeoutMs = DEFAULT_TIMEOUT_MS } = {}) {
  const base = getApiBase();
  const url = `${base}${path}`;

  // serve from cache if fresh
  const cached = _cache.get(url);
  const now = Date.now();
  if (cached && (now - cached.time) < (ttlMs || 0)) {
    return cached.data;
  }

  const ctrl = typeof AbortController !== 'undefined' ? new AbortController() : null;
  const timer = ctrl ? setTimeout(() => ctrl.abort(), timeoutMs) : null;
  try {
    const resp = await fetch(url, {
      credentials: 'include',
      headers: { 'Accept': 'application/json' },
      signal: ctrl?.signal
    });
    if (!resp.ok) {
      let t = `请求失败 ${resp.status}`;
      try { const j = await resp.json(); if (j && (j.detail || j.message)) t = j.detail || j.message; } catch {}
      throw new Error(t);
    }
    const data = await resp.json();
    if (ttlMs && ttlMs > 0) _cache.set(url, { time: now, data });
    return data;
  } catch (e) {
    if (e?.name === 'AbortError') throw new Error('请求超时，请稍后再试');
    throw e;
  } finally {
    if (timer) clearTimeout(timer);
  }
}
