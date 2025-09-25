import { reactive } from 'vue';
import { apiGet } from './useApi';
import { adminContacts as fallbackContacts } from '../config/siteMeta';

const siteState = reactive({
  bulletin: {
    title: '公告栏',
    html: '',
  },
  contacts: [...fallbackContacts],
  loaded: false,
  loading: false,
  error: '',
});

function normalizeContacts(raw) {
  if (!Array.isArray(raw)) return [];
  return raw
    .map(item => ({
      icon: String(item?.icon || 'custom'),
      label: String(item?.label || '').trim(),
      value: String(item?.value || '').trim(),
      href: String(item?.href || '').trim(),
    }))
    .filter(item => item.label || item.value);
}

export async function fetchSiteMeta(force = false) {
  if (siteState.loading) return siteState;
  if (siteState.loaded && !force) return siteState;
  siteState.loading = true;
  siteState.error = '';
  try {
    const data = await apiGet('/orderapi/announcement', { ttlMs: 0 });
    siteState.bulletin.title = data?.title || '公告栏';
    siteState.bulletin.html = data?.html || '';
    const contacts = normalizeContacts(data?.contacts);
    siteState.contacts = contacts.length ? contacts : [...fallbackContacts];
    siteState.loaded = true;
  } catch (error) {
    siteState.error = error?.message || '站点信息加载失败';
    siteState.loaded = false;
    siteState.contacts = [...fallbackContacts];
  } finally {
    siteState.loading = false;
  }
  return siteState;
}

export function setSiteContacts(contacts) {
  const normalized = normalizeContacts(contacts);
  siteState.contacts = normalized.length ? normalized : [...fallbackContacts];
}

export function setBulletinContent({ title, html }) {
  if (typeof title === 'string') siteState.bulletin.title = title;
  if (typeof html === 'string') siteState.bulletin.html = html;
}

export function useSiteMeta() {
  return siteState;
}
