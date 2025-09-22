import { reactive } from 'vue';
import { apiGet } from './useApi';

export function useBulletin() {
  const bulletin = reactive({ title: '公告栏', html: '' });
  async function load() {
    try {
      const data = await apiGet('/orderapi/announcement');
      bulletin.title = data.title || '公告栏';
      const tmp = document.createElement('div');
      tmp.innerHTML = data.html || '';
      // basic sanitization: remove scripts, event attrs, and dangerous urls
      tmp.querySelectorAll('script').forEach(n => n.remove());
      tmp.querySelectorAll('*').forEach(el => {
        // remove inline event handlers
        [...el.attributes].forEach(attr => {
          const name = attr.name?.toLowerCase?.();
          if (name && name.startsWith('on')) el.removeAttribute(attr.name);
          if (name === 'href' || name === 'src') {
            const v = (attr.value || '').trim().toLowerCase();
            if (v.startsWith('javascript:') || v.startsWith('data:text/html')) el.removeAttribute(attr.name);
          }
          if (name === 'style') {
            // optionally keep safe inline styles; drop filter/expression
            const val = (attr.value || '').replace(/expression\s*\(/gi, '');
            el.setAttribute('style', val);
          }
        });
      });
      bulletin.html = tmp.innerHTML || '<div class="muted">暂无公告</div>';
    } catch {}
  }
  return { bulletin, load };
}
