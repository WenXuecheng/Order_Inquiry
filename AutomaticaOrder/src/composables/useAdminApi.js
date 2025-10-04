import { getApiBase } from './useApi';

const TOKEN_KEY = 'admin_token';
const ROLE_KEY = 'admin_role';

function emitAuthChanged() {
  try {
    window.dispatchEvent(new CustomEvent('admin-auth-changed'));
  } catch {}
}

export function getToken() {
  try { return localStorage.getItem(TOKEN_KEY) || ''; } catch { return ''; }
}

export function setToken(token) {
  try { localStorage.setItem(TOKEN_KEY, token || ''); } catch {}
  emitAuthChanged();
}

export function clearToken() {
  try { localStorage.removeItem(TOKEN_KEY); } catch {}
  emitAuthChanged();
}

export function getRole() {
  try { return localStorage.getItem(ROLE_KEY) || ''; } catch { return ''; }
}

export function setRole(role) {
  try { localStorage.setItem(ROLE_KEY, role || ''); } catch {}
  emitAuthChanged();
}

export function clearRole() {
  try { localStorage.removeItem(ROLE_KEY); } catch {}
  emitAuthChanged();
}

function handleAuthFailure() {
  clearToken();
  clearRole();
  try { document.cookie = 'admin_token=; Max-Age=0; path=/;'; } catch {}
  if (typeof window === 'undefined') return;
  if (window.__AUTOMATICA_FORCED_LOGOUT_ACTIVE) return;
  window.__AUTOMATICA_FORCED_LOGOUT_ACTIVE = true;
  try {
    const rawHash = window.location.hash || '#/';
    const trimmed = rawHash.replace(/^#\/?/, '');
    const [pathPart = '', queryPart = ''] = trimmed.split('?');
    if (pathPart === 'login') {
      return;
    }
    const redirectTarget = queryPart ? `${pathPart}?${queryPart}` : pathPart;
    const redirectSuffix = redirectTarget ? `?redirect=${encodeURIComponent(redirectTarget)}` : '';
    const destination = `#/login${redirectSuffix}`;
    if (rawHash !== destination) {
      window.location.hash = destination;
    }
  } finally {
    setTimeout(() => {
      window.__AUTOMATICA_FORCED_LOGOUT_ACTIVE = false;
    }, 200);
  }
}

export async function apiFetch(path, { method = 'GET', headers = {}, body, timeoutMs = 15000, withAuth = true, responseType = 'auto' } = {}) {
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
      let message = `请求失败 ${resp.status}`;
      let payload;
      try {
        payload = await resp.json();
        if (payload && (payload.detail || payload.message)) {
          message = payload.detail || payload.message;
        }
      } catch {}
      if (resp.status === 401 && withAuth) {
        handleAuthFailure();
        message = '登录已失效，请重新登录';
      }
      throw new Error(message);
    }
    if (responseType === 'blob') {
      return await resp.blob();
    }
    if (responseType === 'arrayBuffer') {
      return await resp.arrayBuffer();
    }
    if (responseType === 'text') {
      return await resp.text();
    }
    const ct = resp.headers.get('Content-Type') || '';
    if (ct.includes('application/json')) return await resp.json();
    if (ct.startsWith('text/')) return await resp.text();
    return await resp.text();
  } finally {
    if (timer) clearTimeout(timer);
  }
}

export const adminApi = {
  login: async (username, password) => apiFetch('/orderapi/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }), withAuth: false }),
  register: async (username, password, codes = [], inviteCode = '') => apiFetch('/orderapi/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password, codes, invite_code: inviteCode }), withAuth: false }),
  checkUsername: async (username) => apiFetch(`/orderapi/register/check-username?username=${encodeURIComponent(username)}`, { withAuth: false }),
  randomUsername: async (prefix = 'user') => apiFetch(`/orderapi/register/random-username?prefix=${encodeURIComponent(prefix)}`, { withAuth: false }),
  getOrder: async (orderNo) => apiFetch(`/orderapi/orders/by-no/${encodeURIComponent(orderNo)}`),
  updateOrder: async (orderNo, payload) => apiFetch(`/orderapi/orders/by-no/${encodeURIComponent(orderNo)}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }),
  createOrder: async (payload) => apiFetch('/orderapi/orders', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }),
  deleteOrder: async (orderNo) => apiFetch(`/orderapi/orders/by-no/${encodeURIComponent(orderNo)}`, { method: 'DELETE' }),
  deleteOrdersBulk: async (orderNos) => apiFetch('/orderapi/orders/bulk', { method: 'DELETE', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ order_nos: orderNos }) }),
  exportOrders: async (params = {}) => {
    const search = new URLSearchParams();
    if (params.code) search.set('code', params.code);
    if (params.status) search.set('status', params.status);
    if (params.start_date) search.set('start_date', params.start_date);
    if (params.end_date) search.set('end_date', params.end_date);
    const suffix = search.toString() ? `?${search.toString()}` : '';
    return apiFetch(`/orderapi/orders/export${suffix}`, { responseType: 'blob' });
  },
  importExcel: async (file) => { const fd = new FormData(); fd.append('file', file); return apiFetch('/orderapi/import/excel', { method: 'POST', body: fd, headers: {} }); },
  listByCode: async (code, options = {}) => {
    const params = new URLSearchParams();
    if (code !== undefined && code !== null && String(code).length > 0) params.set('code', String(code));
    const { page, page_size, status, start_date, end_date } = options || {};
    if (page) params.set('page', String(page));
    if (page_size) params.set('page_size', String(page_size));
    if (status) params.set('status', status);
    if (start_date) params.set('start_date', start_date);
    if (end_date) params.set('end_date', end_date);
    const qs = params.toString();
    return apiFetch(`/orderapi/orders${qs ? ('?' + qs) : ''}`);
  },
  getAnnouncement: async () => apiFetch('/orderapi/announcement'),
  saveAnnouncement: async (payload) => apiFetch('/orderapi/announcement', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }),
  getAnnouncementHistory: async (limit = 20) => apiFetch(`/orderapi/announcement/history?limit=${encodeURIComponent(limit)}`),
  revertAnnouncement: async (id) => apiFetch('/orderapi/announcement/revert', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id }) }),
  usersList: async ({ q='', role='', page=1, page_size=20 }={}) => apiFetch(`/orderapi/admin/users?q=${encodeURIComponent(q)}&role=${encodeURIComponent(role)}&page=${page}&page_size=${page_size}`),
  usersCreate: async (payload) => apiFetch('/orderapi/admin/users', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }),
  usersUpdate: async (id, payload) => apiFetch(`/orderapi/admin/users/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }),
  usersDeleteBulk: async (ids) => apiFetch('/orderapi/admin/users', { method: 'DELETE', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ids }) }),
  changePassword: async ({ old_password, new_password }) => apiFetch('/orderapi/user/change-password', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ old_password, new_password }) }),
};
