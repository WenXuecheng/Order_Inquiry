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
      tmp.querySelectorAll('script').forEach(n => n.remove());
      bulletin.html = tmp.innerHTML || '<div class="muted">暂无公告</div>';
    } catch {}
  }
  return { bulletin, load };
}

