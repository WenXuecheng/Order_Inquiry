import { shallowRef, readonly } from 'vue';
import { getToken, getRole } from '../composables/useAdminApi';

const ROUTES = [
  { name: 'home', path: '', meta: { title: '订单查询' } },
  { name: 'login', path: 'login', meta: { title: '登录', requiresGuest: true } },
  { name: 'register', path: 'register', meta: { title: '注册', requiresGuest: true } },
  { name: 'order-management', path: 'admin/orders', meta: { title: '订单管理', requiresAuth: true, roles: ['admin', 'superadmin'] } },
  { name: 'user-management', path: 'admin/users', meta: { title: '用户管理', requiresAuth: true, roles: ['superadmin'] } },
  { name: 'content-management', path: 'admin/content', meta: { title: '内容管理', requiresAuth: true, roles: ['admin', 'superadmin'] } },
];

const routesByName = new Map();
const routesByPath = new Map();
for (const route of ROUTES) {
  routesByName.set(route.name, route);
  routesByPath.set(route.path, route);
}

const currentRoute = shallowRef({ ...ROUTES[0], path: '', query: {} });
let routerInitialised = false;

function parseHash(hash) {
  let raw = hash || '';
  if (raw.startsWith('#')) raw = raw.slice(1);
  if (raw.startsWith('/')) raw = raw.slice(1);
  const [pathPart = '', queryString = ''] = raw.split('?');
  const path = decodeURIComponent((pathPart || '').replace(/\/+$/g, ''));
  const query = {};
  if (queryString) {
    const params = new URLSearchParams(queryString);
    params.forEach((value, key) => {
      query[key] = value;
    });
  }
  return { path, query };
}

function buildHash(path, query = {}) {
  const trimmedPath = (path || '').replace(/^\/+/, '').replace(/\/+$/g, '');
  const qs = new URLSearchParams(Object.entries(query).filter(([, v]) => v !== undefined && v !== null && v !== '')).toString();
  return `#/${trimmedPath}${qs ? `?${qs}` : ''}`;
}

function pickRoute(path) {
  const normalised = (path || '').replace(/^\/+/, '').replace(/\/+$/g, '');
  return routesByPath.get(normalised) || routesByName.get('home');
}

function runGuards(route) {
  const token = getToken();
  const role = getRole();
  if (route.meta?.requiresAuth && !token) {
    return { redirectTo: { name: 'login', query: route.path ? { redirect: route.path } : {} } };
  }
  if (route.meta?.roles && route.meta.roles.length) {
    if (!role || !route.meta.roles.includes(role)) {
      if (!token) {
        return { redirectTo: { name: 'login', query: route.path ? { redirect: route.path } : {} } };
      }
      return { redirectTo: { name: 'home' } };
    }
  }
  if (route.meta?.requiresGuest && token) {
    return { redirectTo: { name: 'home' } };
  }
  return { route };
}

function updateFromHash() {
  if (typeof window === 'undefined') return;
  const parsed = parseHash(window.location.hash);
  const targetRoute = pickRoute(parsed.path);
  const guardResult = runGuards(targetRoute);
  if (guardResult.redirectTo) {
    const destination = routesByName.get(guardResult.redirectTo.name) || routesByName.get('home');
    const hash = buildHash(destination.path, guardResult.redirectTo.query || {});
    const base = window.location.href.split('#')[0];
    history.replaceState(null, '', `${base}${hash}`);
    currentRoute.value = { ...destination, path: destination.path, query: guardResult.redirectTo.query || {} };
    return;
  }
  currentRoute.value = { ...targetRoute, path: targetRoute.path, query: parsed.query };
}

function initRouter() {
  if (routerInitialised || typeof window === 'undefined') return;
  routerInitialised = true;
  if (!window.location.hash) {
    const base = window.location.href.split('#')[0];
    history.replaceState(null, '', `${base}#/`);
  }
  updateFromHash();
  window.addEventListener('hashchange', updateFromHash);
}

function navigateTo(name, { query = {}, replace = false } = {}) {
  if (typeof window === 'undefined') return;
  const route = routesByName.get(name) || routesByName.get('home');
  const hash = buildHash(route.path, query);
  const currentHash = window.location.hash || '';
  if (replace) {
    const base = window.location.href.split('#')[0];
    history.replaceState(null, '', `${base}${hash}`);
    updateFromHash();
    return;
  }
  if (currentHash === hash) {
    updateFromHash();
  } else {
    window.location.hash = hash;
  }
}

function useCurrentRoute() {
  return readonly(currentRoute);
}

export { ROUTES, initRouter, navigateTo, useCurrentRoute, currentRoute };
