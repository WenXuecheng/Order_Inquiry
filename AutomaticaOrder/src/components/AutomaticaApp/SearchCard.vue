<template>
  <section class="card">
    <h1 class="title">查询订单</h1>
    <p class="subtitle">输入编号获取所属订单；输入 <strong>A</strong> 查看未分类订单</p>
    <div class="search-bar">
      <input v-model.trim="code" class="input" placeholder="输入编号，如 A666" maxlength="40" @keydown.enter="emitSearch" />
      <button class="btn primary" @click="emitSearch">查询</button>
    </div>
    <div class="stats" v-if="statsVisible">
      <div class="stat"><div class="stat-value">{{ totals.count }}</div><div class="stat-label">总件数</div></div>
      <div class="stat"><div class="stat-value">{{ (totals.total_weight||0).toFixed(2) }} kg</div><div class="stat-label">总重量</div></div>
      <div class="stat"><div class="stat-value">{{ (totals.total_shipping_fee||0).toFixed(2) }}</div><div class="stat-label">运费</div></div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue';
import { useOrders } from '../../composables/useOrders';
const emit = defineEmits(['search']);
const { code, totals, orders } = useOrders();
const statsVisible = computed(() => (totals.count || orders.length) > 0);
function emitSearch(){ emit('search', code.value); }
</script>

<style scoped>
.title { margin:4px 0 10px; font-size:22px; }
.subtitle { color:#a3a7b3; margin:0 0 12px; }
.search-bar { display:grid; grid-template-columns: 1fr auto; gap:10px; margin:10px 0 14px; }
.input { width:100%; background:#0b0e14; border:1px solid #1a1e27; color:#e6e7eb; border-radius:10px; padding:10px 12px; }
.btn { background:#1a1e27; color:#e6e7eb; border:1px solid #232736; padding:10px 14px; border-radius:10px; cursor:pointer; }
.btn.primary { background: linear-gradient(90deg,#5caeff,#6fe7c0); color:#0c1016; border:0; font-weight:600; }
.stats { display:grid; grid-template-columns: repeat(3,1fr); gap:12px; }
.stat { background: rgba(11,13,20,.35); backdrop-filter: blur(8px) saturate(140%); border:1px solid rgba(255,255,255,.05); border-radius:12px; padding:12px; text-align:center; }
.stat-value { font-size:20px; font-weight:700; }
.stat-label { color:#a3a7b3; font-size:12px; margin-top:4px; }
</style>

