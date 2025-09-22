<template>
  <div class="app-root">
    <BackgroundEffects />
    <AppHeader />
    <main class="container main">
      <BulletinCard />
      <SearchCard @search="onSearch" />
      <OrdersCard :state="ordersState" />
    </main>
  </div>
  
</template>

<script setup>
import { onMounted } from 'vue';
import AppHeader from './components/AutomaticaApp/AppHeader.vue';
import BackgroundEffects from './components/AutomaticaApp/BackgroundEffects.vue';
import BulletinCard from './components/AutomaticaApp/BulletinCard.vue';
import SearchCard from './components/AutomaticaApp/SearchCard.vue';
import OrdersCard from './components/AutomaticaApp/OrdersCard.vue';
import { useOrders } from './composables/useOrders';

const ordersState = useOrders();
function onSearch(code){ ordersState.search(code); }

onMounted(() => {
  const p = new URLSearchParams(location.search);
  const init = p.get('code');
  if (init) ordersState.search(init);
});
</script>

<style scoped>
.app-root { position: relative; min-height: 100vh; color: #e6e7eb; }
.container { width: min(1100px, 92vw); margin: 0 auto; position: relative; z-index: 1; }
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
