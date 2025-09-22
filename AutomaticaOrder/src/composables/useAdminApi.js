import { getApiBase } from './useApi';

const TOKEN_KEY = 'admin_token';

export function getToken() {
  try { return localStorage.getItem(TOKEN_KEY) || ''; } catch { return ''; }
}

export function setToken(token) {
  try { localStorage.setItem(TOKEN_KEY, token || ''); } catch {}
}

export function clearToken() {
  try { localStorage.removeItem(TOKEN_KEY); } catch {}
}

export async function apiFetch(path, { method = 'GET', headers = {}, body, timeoutMs = 15000, withAuth = true } = {}) {
  const base = getApiBase();
  const url = `${base}${path}`;
  const ctrl = typeof AbortController !== 'undefined' ? new AbortController() : null;
  const timer = ctrl ? setTimeout(() => ctrl.abort(), timeoutMs) : null;
  try {
    const h = { ...headers };
    if (withAuth) {
      const t = getToken();
      if (t) h['Authorization'] = `Bearer ${t}`;
    }
    const resp = await fetch(url, {
      method,
      headers: h,
      body,
      credentials: 'include',
      signal: ctrl?.signal,
    });
    if (!resp.ok) {
      let t = `请求失败 ${resp.status}`;
      try { const j = await resp.json(); if (j && (j.detail || j.message)) t = j.detail || j.message; } catch {}
      throw new Error(t);
    }
    const ct = resp.headers.get('Content-Type') || '';
    if (ct.includes('application/json')) return await resp.json();
    return await resp.text();
  } finally {
    if (timer) clearTimeout(timer);
  }
}

export const adminApi = {
  login: async (username, password) => apiFetch('/orderapi/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }), withAuth: false }),
  getOrder: async (orderNo) => apiFetch(`/orderapi/orders/by-no/${encodeURIComponent(orderNo)}`),
  updateOrder: async (orderNo, payload) => apiFetch(`/orderapi/orders/by-no/${encodeURIComponent(orderNo)}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }),
  createOrder: async (payload) => apiFetch('/orderapi/orders', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }),
  deleteOrder: async (orderNo) => apiFetch(`/orderapi/orders/by-no/${encodeURIComponent(orderNo)}`, { method: 'DELETE' }),
  importExcel: async (file) => { const fd = new FormData(); fd.append('file', file); return apiFetch('/orderapi/import/excel', { method: 'POST', body: fd, headers: {} }); },
  listByCode: async (code) => apiFetch(`/orderapi/orders?code=${encodeURIComponent(code)}`),
  getAnnouncement: async () => apiFetch('/orderapi/announcement'),
  saveAnnouncement: async (payload) => apiFetch('/orderapi/announcement', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }),
  getAnnouncementHistory: async (limit = 20) => apiFetch(`/orderapi/announcement/history?limit=${encodeURIComponent(limit)}`),
  revertAnnouncement: async (id) => apiFetch('/orderapi/announcement/revert', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id }) }),
};
