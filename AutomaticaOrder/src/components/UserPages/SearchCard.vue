<template>
  <section class="search-shell">
    <div class="search-card">
      <div class="title-wrap">
        <span class="title-fallback">查询订单</span>
      </div>
      <p class="muted">输入编号获取所属订单；输入 <strong>A</strong> 查看未分类订单</p>
      <div class="form-stack">
        <input
          class="input"
          :value="code"
          @input="onInput"
          placeholder="输入编号，如 A666"
          maxlength="40"
          @keydown.enter="emitSearch"
        />
        <button class="btn-accent" :disabled="loading" @click="emitSearch">{{ loading ? '查询中…' : '查询' }}</button>
      </div>
      <div v-if="statsVisible" class="search-stats">
        <span>结果：{{ totals.count || 0 }} 单</span>
        <span>总重量：{{ (totals.total_weight || 0).toFixed(2) }} kg</span>
        <span>预计运费：{{ (totals.total_shipping_fee || 0).toFixed(2) }}</span>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  code: { type: String, default: '' },
  totals: { type: Object, default: () => ({}) },
  orders: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
});

const emit = defineEmits(['search', 'update:code']);

const statsVisible = computed(() => ((props.totals?.count || 0) > 0) || (props.orders?.length || 0) > 0);

function onInput(e){
  emit('update:code', (e?.target?.value || '').trim());
}
function emitSearch(){ emit('search', props.code?.trim?.() || ''); }
</script>

<style scoped>
.search-shell { display: flex; flex-direction: column; }
.search-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: rgba(12, 18, 28, 0.45);
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 20px;
  padding: 20px 22px;
  box-shadow: 0 18px 36px rgba(3, 10, 20, 0.24);
  backdrop-filter: blur(18px) saturate(1.3);
  -webkit-backdrop-filter: blur(18px) saturate(1.3);
}
.title-wrap { margin: 0; }
.title-fallback { font-size: 20px; font-weight: 800; letter-spacing: 0.5px; color: var(--text); }
.muted { color: rgba(204, 213, 235, 0.72); font-size: 0.92rem; }
.form-stack { display: flex; gap: 12px; align-items: center; }
.form-stack .input { flex: 1; }
.btn-accent {
  border: 1px solid rgba(102, 212, 255, 0.4);
  background: linear-gradient(135deg, rgba(56, 189, 248, 0.32), rgba(59, 130, 246, 0.28));
  color: #f0f9ff;
  border-radius: 12px;
  padding: 10px 22px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 160ms ease, box-shadow 220ms ease, border-color 220ms ease;
  box-shadow: 0 16px 30px rgba(17, 62, 140, 0.28);
}
.btn-accent:disabled { opacity: 0.6; cursor: not-allowed; box-shadow: none; }
.btn-accent:not(:disabled):hover {
  transform: translateY(-1px);
  border-color: rgba(102, 212, 255, 0.6);
  box-shadow: 0 22px 40px rgba(17, 62, 140, 0.36);
}
.search-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(10, 22, 38, 0.52);
  border: 1px solid rgba(148, 163, 184, 0.18);
  color: rgba(226, 238, 255, 0.82);
  font-size: 0.88rem;
}

@media (max-width: 640px) {
  .form-stack { flex-direction: column; align-items: stretch; }
  .btn-accent { width: 100%; }
}
</style>
