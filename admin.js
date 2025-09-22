(() => {
  const q = (s) => document.querySelector(s);
  const el = {
    year: q('#year'),
    loginCard: q('#loginCard'),
    adminPanel: q('#adminPanel'),
    loginBtn: q('#loginBtn'),
    username: q('#username'),
    password: q('#password'),
    loginMsg: q('#loginMsg'),
    logoutBtn: q('#logoutBtn'),
    excelFile: q('#excelFile'),
    importBtn: q('#importBtn'),
    importMsg: q('#importMsg'),
    editOrderNo: q('#editOrderNo'),
    editGroupCode: q('#editGroupCode'),
    editWeight: q('#editWeight'),
    editStatus: q('#editStatus'),
    editFee: q('#editFee'),
    loadOrderBtn: q('#loadOrderBtn'),
    saveOrderBtn: q('#saveOrderBtn'),
    editMsg: q('#editMsg'),
  };

  const STATUSES = window.STATUSES || [];
  const API = async (path, init = {}) => {
    const token = localStorage.getItem('token');
    const headers = { ...(init.headers||{}), ...(init.body instanceof FormData ? {} : {'Content-Type':'application/json'}) };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const resp = await fetch(`${window.API_BASE_URL}/orderapi${path}`, { ...init, headers });
    return resp;
  };

  function setAuthed(authed) {
    el.loginCard.classList.toggle('hidden', authed);
    el.adminPanel.classList.toggle('hidden', !authed);
  }

  function populateStatuses() {
    el.editStatus.innerHTML = STATUSES.map(s => `<option value="${s}">${s}</option>`).join('');
  }

  async function login() {
    el.loginMsg.textContent = '';
    const username = el.username.value.trim();
    const password = el.password.value;
    try {
      const resp = await API('/login', { method:'POST', body: JSON.stringify({ username, password })});
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || '登录失败');
      // Redirect to backend admin system with token; backend will set HttpOnly cookie
      const base = (window.API_BASE_URL || '').replace(/\/$/, '');
      const url = `${base}/admin?token=${encodeURIComponent(data.access_token)}`;
      location.href = url;
    } catch (e) {
      el.loginMsg.textContent = e.message;
    }
  }

  async function logout() {
    localStorage.removeItem('token');
    setAuthed(false);
  }

  async function importExcel() {
    const file = el.excelFile.files?.[0];
    if (!file) { el.importMsg.textContent = '请选择文件'; return; }
    el.importMsg.textContent = '上传中...';
    try {
      const fd = new FormData();
      fd.append('file', file);
      const resp = await API('/import/excel', { method: 'POST', body: fd });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || '导入失败');
      el.importMsg.textContent = `导入成功：新增 ${data.created} 更新 ${data.updated}`;
    } catch (e) {
      el.importMsg.textContent = e.message;
    }
  }

  async function loadOrder() {
    const order_no = el.editOrderNo.value.trim();
    if (!order_no) { el.editMsg.textContent = '请输入订单号'; return; }
    el.editMsg.textContent = '加载中...';
    try {
      const resp = await API(`/orders/by-no/${encodeURIComponent(order_no)}`);
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || '未找到订单');
      el.editGroupCode.value = data.group_code || '';
      el.editWeight.value = data.weight_kg ?? '';
      el.editStatus.value = data.status || STATUSES[0];
      el.editFee.value = data.shipping_fee ?? '';
      el.editMsg.textContent = '已加载，可编辑后保存';
    } catch (e) {
      el.editMsg.textContent = e.message;
    }
  }

  async function saveOrder() {
    const order_no = el.editOrderNo.value.trim();
    if (!order_no) { el.editMsg.textContent = '请输入订单号'; return; }
    const payload = {
      group_code: el.editGroupCode.value.trim() || null,
      weight_kg: el.editWeight.value ? parseFloat(el.editWeight.value) : null,
      status: el.editStatus.value,
      shipping_fee: el.editFee.value ? parseFloat(el.editFee.value) : null,
    };
    try {
      const resp = await API(`/orders/by-no/${encodeURIComponent(order_no)}`, { method:'PUT', body: JSON.stringify(payload) });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || '保存失败');
      el.editMsg.textContent = '保存成功';
    } catch (e) {
      el.editMsg.textContent = e.message;
    }
  }

  // init
  const yearEl = document.getElementById('year'); if (yearEl) yearEl.textContent = new Date().getFullYear();
  // Hide footer if empty
  const footerInner = document.querySelector('.footer-inner');
  if (footerInner && footerInner.textContent.trim() === '' && footerInner.children.length === 0) {
    const footer = document.querySelector('.site-footer');
    if (footer) footer.style.display = 'none';
  }
  populateStatuses();
  setAuthed(false);

  // events
  el.loginBtn.addEventListener('click', login);
  el.logoutBtn.addEventListener('click', logout);
  el.importBtn.addEventListener('click', importExcel);
  el.loadOrderBtn.addEventListener('click', loadOrder);
  el.saveOrderBtn.addEventListener('click', saveOrder);
})();
