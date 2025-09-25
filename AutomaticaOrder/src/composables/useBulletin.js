import { reactive, watch } from 'vue';
import { fetchSiteMeta, setBulletinContent, useSiteMeta } from './useSiteMeta';

function sanitize(html) {
  try {
    const tmp = document.createElement('div');
    tmp.innerHTML = html || '';
    tmp.querySelectorAll('script').forEach(node => node.remove());
    tmp.querySelectorAll('*').forEach(el => {
      [...el.attributes].forEach(attr => {
        const name = attr.name?.toLowerCase?.();
        if (name && name.startsWith('on')) el.removeAttribute(attr.name);
        if (name === 'href' || name === 'src') {
          const v = (attr.value || '').trim().toLowerCase();
          if (v.startsWith('javascript:') || v.startsWith('data:text/html')) el.removeAttribute(attr.name);
        }
        if (name === 'style') {
          const val = (attr.value || '').replace(/expression\s*\(/gi, '');
          el.setAttribute('style', val);
        }
      });
    });
    return tmp.innerHTML || '<div class="muted">暂无公告</div>';
  } catch {
    return '<div class="muted">暂无公告</div>';
  }
}

export function useBulletin() {
  const siteMeta = useSiteMeta();
  const bulletin = reactive({ title: siteMeta.bulletin.title, html: sanitize(siteMeta.bulletin.html) });

  const sync = () => {
    bulletin.title = siteMeta.bulletin.title || '公告栏';
    bulletin.html = sanitize(siteMeta.bulletin.html);
  };

  watch(() => [siteMeta.bulletin.title, siteMeta.bulletin.html], sync, { immediate: true });

  async function load(force = false) {
    await fetchSiteMeta(force);
    sync();
    setBulletinContent({ title: bulletin.title, html: bulletin.html });
  }

  return { bulletin, load };
}
