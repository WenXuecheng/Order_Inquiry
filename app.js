(() => {
  const q = (s) => document.querySelector(s);
  const el = {
    code: q('#codeInput'),
    search: q('#searchBtn'),
    orders: q('#orders'),
    empty: q('#emptyState'),
    error: q('#errorBox'),
    loading: q('#loading'),
    statCount: q('#statCount'),
    statWeight: q('#statWeight'),
    statFee: q('#statFee'),
    flowDemo: q('#flowDemo'),
  };

  const STATUSES = window.STATUSES || [];
  const API = (path, init = {}) => fetch(`${window.API_BASE_URL}/orderapi${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init.headers||{}) },
  });

  // Bulletin
  async function loadBulletin() {
    try {
      const resp = await API('/announcement');
      if (!resp.ok) throw new Error('公告获取失败');
      const data = await resp.json();
      const container = document.getElementById('bulletin');
      if (!container) return;
      const titleEl = document.getElementById('bulletinTitle');
      if (titleEl) titleEl.textContent = (data && data.title) || '公告栏';
      const html = data.html || '';
      // Simple sanitize: strip <script>
      const tmp = document.createElement('div'); tmp.innerHTML = html; tmp.querySelectorAll('script').forEach(n=>n.remove());
      container.innerHTML = tmp.innerHTML || '<div class="muted">暂无公告</div>';
    } catch (e) {
      const container = document.getElementById('bulletin');
      if (container) container.innerHTML = '<div class="muted">公告加载失败</div>';
    }
  }

  function fmtDate(iso) {
    try { return new Date(iso).toLocaleString(); } catch { return iso; }
  }

  function statusIndex(s) { return Math.max(0, STATUSES.indexOf(s)); }

  function renderOrders(res) {
    const { orders = [], totals = {} } = res || {};
    el.orders.innerHTML = '';
    el.empty.classList.toggle('hidden', orders.length !== 0);

    function renderCardContent(order, expanded) {
      const isDone = STATUSES[STATUSES.length - 1] === order.status;
      if (!expanded) {
        return `
          <div class="row">
            <div style="font-weight:600">${order.order_no}</div>
            <div class="chip ${isDone ? 'ok' : ''}" title="状态">${order.status}</div>
          </div>
        `;
      }
      return `
        <div class="row">
          <div>
            <div class="muted">订单号</div>
            <div style="font-weight:600">${order.order_no}</div>
          </div>
          <div class="chip ${isDone ? 'ok' : ''}" title="状态">${order.status}</div>
        </div>
        <div class="row">
          <div class="muted">编号</div>
          <div>${order.group_code || ''}</div>
        </div>
        <div class="row">
          <div class="muted">重量</div>
          <div>${(order.weight_kg ?? 0).toFixed(2)} kg</div>
        </div>
        <div class="row">
          <div class="muted">是否打木架</div>
          <div>${order.wooden_crate === null || order.wooden_crate === undefined ? '未设置' : (order.wooden_crate ? '是' : '否')}</div>
        </div>
        
        <div class="row">
          <div class="muted">更新</div>
          <div>${fmtDate(order.updated_at)}</div>
        </div>
      `;
    }

    const frag = document.createDocumentFragment();
    orders.forEach(o => {
      const card = document.createElement('div');
      card.className = 'order';
      card.setAttribute('tabindex', '0');
      card.innerHTML = renderCardContent(o, false);
      let expanded = false;
      const toggle = () => {
        expanded = !expanded;
        card.classList.toggle('expanded', expanded);
        card.innerHTML = renderCardContent(o, expanded);
      };
      card.addEventListener('click', toggle);
      card.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); } });
      frag.appendChild(card);
    });
    el.orders.appendChild(frag);

    el.statCount.textContent = totals.count ?? orders.length;
    const w = totals.total_weight ?? orders.reduce((a,b)=>a+(b.weight_kg||0),0);
    el.statWeight.textContent = `${w.toFixed(2)} kg`;
    const fee = totals.total_shipping_fee ?? 0;
    el.statFee.textContent = fee.toFixed ? fee.toFixed(2) : `${fee}`;
  }

  async function search() {
    const code = (el.code.value || '').trim();
    if (!code) return;
    el.loading.classList.remove('hidden');
    el.error.classList.add('hidden');
    try {
      const resp = await API(`/orders?code=${encodeURIComponent(code)}`);
      if (!resp.ok) throw new Error(`请求失败 ${resp.status}`);
      const data = await resp.json();
      renderOrders(data);
    } catch (e) {
      el.error.textContent = e.message || '请求出错';
      el.error.classList.remove('hidden');
    } finally {
      el.loading.classList.add('hidden');
    }
  }

  // events
  el.search.addEventListener('click', search);
  el.code.addEventListener('keydown', (e) => { if (e.key === 'Enter') search(); });

  // subtle glow pulse on .btn click/tap
  function attachButtonPulse() {
    const trigger = (btn) => {
      if (!btn) return;
      btn.classList.remove('btn-pulse');
      // reflow to restart animation
      void btn.offsetWidth;
      btn.classList.add('btn-pulse');
      setTimeout(() => btn && btn.classList.remove('btn-pulse'), 650);
    };
    document.addEventListener('mousedown', (e) => { const b = e.target && e.target.closest && e.target.closest('.btn'); if (b) trigger(b); }, { passive: true });
    document.addEventListener('touchstart', (e) => { const t = e.target; const b = t && t.closest && t.closest('.btn'); if (b) trigger(b); }, { passive: true });
  }
  attachButtonPulse();

  // header remains static (no auto-condense on scroll)

  // initial
  const yearEl = document.getElementById('year'); if (yearEl) yearEl.textContent = new Date().getFullYear();
  // Hide footer if empty
  const footerInner = document.querySelector('.footer-inner');
  if (footerInner && footerInner.textContent.trim() === '' && footerInner.children.length === 0) {
    const footer = document.querySelector('.site-footer');
    if (footer) footer.style.display = 'none';
  }

  // Single-column layout across devices; no breakpoint re-render needed
  loadBulletin();

  // optional: prefill from URL ?code=
  const params = new URLSearchParams(location.search);
  const initCode = params.get('code');
  if (initCode) { el.code.value = initCode; search(); }
})();
