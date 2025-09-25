import { reactive, ref } from 'vue';
import { apiGet } from './useApi';

export const STATUSES = [
  '打包发出',
  '在我国海岸等待检查',
  '已发往俄罗斯',
  '等待俄罗斯关口检查',
  '转运到彼得堡（1-3天）',
  '已到达彼得堡',
  '已结算',
];

export function statusIndex(s) { return Math.max(0, STATUSES.indexOf(s)); }
export function fmtDate(iso) { try { return new Date(iso).toLocaleString(); } catch { return iso || ''; } }

export function useOrders() {
  const code = ref('');
  const orders = reactive([]);
  const totals = reactive({ count: 0, total_weight: 0, total_shipping_fee: 0 });
  const loading = ref(false);
  const error = ref('');
  let reqSeq = 0;

  async function search(c) {
    const query = (c ?? code.value ?? '').trim();
    if (!query) return;
    const currentReq = ++reqSeq;
    loading.value = true; error.value = '';
    try {
      const data = await apiGet(`/orderapi/orders?code=${encodeURIComponent(query)}`);
      if (currentReq !== reqSeq) return; // stale response
      const sorted = (data.orders || []).slice().sort((a, b) => {
        const timeA = Date.parse(a?.updated_at || '');
        const timeB = Date.parse(b?.updated_at || '');
        return (isNaN(timeB) ? 0 : timeB) - (isNaN(timeA) ? 0 : timeA);
      });
      orders.splice(0, orders.length, ...sorted.map(o => ({ ...o, __open: false })));
      Object.assign(totals, data.totals || {});
      code.value = query;
    } catch (e) {
      if (currentReq !== reqSeq) return; // ignore if superseded
      error.value = e.message || '请求出错';
    } finally {
      if (currentReq === reqSeq) loading.value = false;
    }
  }

  return { code, orders, totals, loading, error, search };
}
