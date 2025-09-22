<template>
  <div class="app-root">
    <!-- Background and cursor effects -->
    <LiquidEther :style="{ position: 'fixed', inset: '0', zIndex: 0 }" class-name="w-full h-full" :colors="['#5caeff','#6fe7c0','#1a1e2f']" />
    <SplashCursor />

    <!-- Header -->
    <header class="site-header">
      <div class="container header-inner">
        <div class="brand">
          <span class="logo-circle" aria-hidden="true"></span>
          <span class="brand-text">订单查询</span>
        </div>
        <nav class="nav">
          <a class="nav-link" href="/admin.html" target="_self">管理员登录</a>
        </nav>
      </div>
    </header>

    <main class="container main">
      <!-- Bulletin -->
      <section class="card">
        <h2 class="title small" id="bulletinTitle">{{ bulletin.title || '公告栏' }}</h2>
        <div class="bulletin" v-html="bulletin.html"></div>
      </section>

      <!-- Search -->
      <section class="card">
        <h1 class="title">查询订单</h1>
        <p class="subtitle">输入编号获取所属订单；输入 <strong>A</strong> 查看未分类订单</p>
        <div class="search-bar">
          <input v-model.trim="code" class="input" placeholder="输入编号，如 A666" maxlength="40" @keydown.enter="search" />
          <button class="btn primary" @click="search">查询</button>
        </div>
        <div class="stats" v-if="statsVisible">
          <div class="stat"><div class="stat-value">{{ totals.count }}</div><div class="stat-label">总件数</div></div>
          <div class="stat"><div class="stat-value">{{ (totals.total_weight||0).toFixed(2) }} kg</div><div class="stat-label">总重量</div></div>
          <div class="stat"><div class="stat-value">{{ (totals.total_shipping_fee||0).toFixed(2) }}</div><div class="stat-label">运费</div></div>
        </div>
      </section>

      <!-- Results -->
      <section class="card">
        <div class="results-header">
          <h2 class="title small">查询结果</h2>
          <div class="loading" v-if="loading">加载中...</div>
        </div>
        <div class="error" v-if="error">{{ error }}</div>
        <div class="empty" v-if="!loading && !error && orders.length === 0">暂无订单，请尝试其它编号。</div>
        <div class="orders">
          <div class="order" v-for="o in orders" :key="o.id" @click="o.__open = !o.__open" tabindex="0" @keydown.enter.prevent="o.__open = !o.__open" @keydown.space.prevent="o.__open = !o.__open">
            <div class="row">
              <div>
                <div class="muted">订单号</div>
                <div style="font-weight:600">{{ o.order_no }}</div>
              </div>
              <div class="chip" :class="{ ok: o.status === STATUSES[STATUSES.length-1] }">{{ o.status }}</div>
            </div>

            <template v-if="o.__open">
              <div class="row"><div class="muted">编号</div><div>{{ o.group_code || '' }}</div></div>
              <div class="row"><div class="muted">重量</div><div>{{ (o.weight_kg||0).toFixed(2) }} kg</div></div>
              <div class="row"><div class="muted">是否打木架</div><div>{{ o.wooden_crate == null ? '未设置' : (o.wooden_crate ? '是' : '否') }}</div></div>
              <div class="flow" aria-label="订单进度">
                <div v-for="(s,i) in STATUSES" :key="s" class="step" :class="{ active: i <= statusIndex(o.status) }"><div class="dot"></div><div class="label">{{ s }}</div></div>
              </div>
              <div class="row"><div class="muted">更新</div><div>{{ fmtDate(o.updated_at) }}</div></div>
            </template>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, computed } from 'vue';
import LiquidEther from './components/Backgrounds/LiquidEther/LiquidEther.vue';
import SplashCursor from './components/Animations/SplashCursor/SplashCursor.vue';

const STATUSES = [
  '打包发出',
  '在我国海岸等待检查',
  '已发往俄罗斯',
  '等待俄罗斯关口检查',
  '转运到彼得堡（1-3天）',
  '已到达彼得堡',
  '已结算',
];

const code = ref('');
const orders = reactive([]);
const totals = reactive({ count: 0, total_weight: 0, total_shipping_fee: 0 });
const loading = ref(false);
const error = ref('');
const bulletin = reactive({ title: '公告栏', html: '' });

const API_BASE = (() => {
  try { return (window.API_BASE_URL || 'https://api.wen-xc.site').replace(/\/$/, ''); } catch { return 'https://api.wen-xc.site'; }
})();

function statusIndex(s){ return Math.max(0, STATUSES.indexOf(s)); }
function fmtDate(iso){ try { return new Date(iso).toLocaleString(); } catch { return iso || ''; } }
const statsVisible = computed(() => (totals.count||orders.length)>0);

async function search(){
  const c = (code.value || '').trim();
  if (!c) return;
  loading.value = true; error.value = '';
  try {
    const resp = await fetch(`${API_BASE}/orderapi/orders?code=${encodeURIComponent(c)}`);
    if (!resp.ok) throw new Error(`请求失败 ${resp.status}`);
    const data = await resp.json();
    orders.splice(0, orders.length, ...(data.orders||[]).map(o => ({...o, __open:false})));
    Object.assign(totals, data.totals||{});
  } catch(e){ error.value = e.message || '请求出错'; }
  finally { loading.value = false; }
}

async function loadBulletin(){
  try {
    const resp = await fetch(`${API_BASE}/orderapi/announcement`);
    const data = await resp.json();
    bulletin.title = data.title || '公告栏';
    // simple sanitize
    const tmp = document.createElement('div'); tmp.innerHTML = data.html || ''; tmp.querySelectorAll('script').forEach(n=>n.remove());
    bulletin.html = tmp.innerHTML || '<div class="muted">暂无公告</div>';
  } catch {}
}

onMounted(() => {
  // prefill from ?code=
  const p = new URLSearchParams(location.search);
  const init = p.get('code');
  if (init) { code.value = init; search(); }
  loadBulletin();
});
</script>

<style scoped>
.app-root { position: relative; min-height: 100vh; color: #e6e7eb; }
.container { width: min(1100px, 92vw); margin: 0 auto; position: relative; z-index: 1; }
.site-header { position: sticky; top:0; background: rgba(13,16,24,.35); backdrop-filter: blur(12px) saturate(140%); border-bottom: 1px solid rgba(255,255,255,.06); box-shadow: 0 1px 0 rgba(255,255,255,.04) inset, 0 6px 20px rgba(0,0,0,.25); z-index: 2; }
.header-inner { display:flex; align-items:center; justify-content: space-between; padding:14px 0; }
.brand { display:flex; align-items:center; gap:10px; font-weight:600; }
.logo-circle { width:14px; height:14px; border-radius:50%; background: radial-gradient(circle at 30% 30%, #67b8ff, #7ae0b8); box-shadow: 0 0 18px rgba(103,184,255,.5); }
.nav-link { color: #e6e7eb; opacity:.9; text-decoration:none; padding:6px 10px; border-radius:8px; }
.nav-link:hover { background: rgba(26,28,36,.5); }
.main { display:grid; grid-template-columns: 1fr; gap:16px; padding:18px 0 40px; }
.card { background: rgba(13,16,24,.35); backdrop-filter: blur(12px) saturate(140%); border:1px solid rgba(255,255,255,.06); border-radius:14px; padding:18px; box-shadow: 0 1px 0 rgba(255,255,255,.04) inset, 0 10px 30px rgba(0,0,0,.25); }
.title { margin:4px 0 10px; font-size:22px; }
.title.small { font-size:18px; }
.subtitle { color:#a3a7b3; margin:0 0 12px; }
.search-bar { display:grid; grid-template-columns: 1fr auto; gap:10px; margin:10px 0 14px; }
.input { width:100%; background:#0b0e14; border:1px solid #1a1e27; color:#e6e7eb; border-radius:10px; padding:10px 12px; }
.btn { background:#1a1e27; color:#e6e7eb; border:1px solid #232736; padding:10px 14px; border-radius:10px; cursor:pointer; }
.btn.primary { background: linear-gradient(90deg,#5caeff,#6fe7c0); color:#0c1016; border:0; font-weight:600; }
.stats { display:grid; grid-template-columns: repeat(3,1fr); gap:12px; }
.stat { background: rgba(11,13,20,.35); backdrop-filter: blur(8px) saturate(140%); border:1px solid rgba(255,255,255,.05); border-radius:12px; padding:12px; text-align:center; }
.stat-value { font-size:20px; font-weight:700; }
.stat-label { color:#a3a7b3; font-size:12px; margin-top:4px; }
.results-header { display:flex; align-items:center; justify-content: space-between; }
.orders { display:grid; grid-template-columns: 1fr; gap:12px; }
.order { display:grid; gap:8px; padding:14px; border-radius:12px; background:#0b0f16; border:1px solid #182031; }
.order:hover { border-color:#24314a; }
.row { display:flex; align-items:center; justify-content: space-between; gap:8px; }
.chip { padding:4px 8px; border-radius:999px; border:1px solid #26324a; color:#a3a7b3; font-size:12px; }
.chip.ok { border-color:#194530; color:#a2f5c4; }
.muted { color:#a3a7b3; font-size:13px; }
.error { background:#160b0b; border:1px solid #3a1717; color:#ffb9b9; border-radius:10px; padding:10px; }
.empty { color:#a3a7b3; text-align:center; padding:20px; }
.loading { color:#a3a7b3; }
.bulletin img, .bulletin video, .bulletin iframe { max-width:100%; height:auto; border-radius:8px; display:block; margin:8px 0; }
.flow { display:grid; gap:10px; grid-template-columns: repeat(7, minmax(90px, 1fr)); align-items: stretch; }
.step { position:relative; padding:10px; background:#0b0f16; border:1px solid #182031; border-radius:12px; text-align:center; display:flex; flex-direction:column; justify-content:center; }
.step .dot { width:10px; height:10px; border-radius:50%; margin:0 auto 6px; background:#26324a; box-shadow:0 0 0 2px #182031; }
.step.active .dot { background:#7ae0b8; box-shadow:0 0 0 4px rgba(122,224,184,.2), 0 0 20px rgba(122,224,184,.4); }
.step .label { font-size:12px; color:#a3a7b3; white-space:normal; word-break:break-word; }
</style>
