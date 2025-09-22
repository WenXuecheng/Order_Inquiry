<template>
  <section>
    <div class="title-wrap compact">
      <span class="title-fallback">查询结果</span>
    </div>
    <div v-if="isLoading" class="muted">加载中...</div>
    <div v-else-if="errorText" class="muted">{{ errorText }}</div>
    <div v-else-if="state.orders.length === 0" class="muted">暂无订单，请尝试其它编号。</div>
    <div v-else>
      <div v-if="statsVisible" class="stats-row">
        <div class="stat-chip">
          <span class="stat-label">总件数</span>
          <span class="stat-value">{{ (totals.count || 0) }} 个</span>
        </div>
        <div class="stat-chip">
          <span class="stat-label">总重量</span>
          <span class="stat-value">{{ (totals.total_weight||0).toFixed(2) }} kg</span>
        </div>
        <div class="stat-chip">
          <span class="stat-label">总运费</span>
          <span class="stat-value">{{ (totals.total_shipping_fee||0).toFixed(2) }} 元</span>
        </div>
      </div>
      <div class="orders-list">
        <div v-for="o in state.orders" :key="o.id || o.order_no" class="order-card">
          <div class="order-top">
            <div class="order-no">订单号：{{ o.order_no }}</div>
            <span class="order-status">{{ o.status }}</span>
          </div>
          <div class="order-grid">
            <div class="og-item">
              <span class="og-label">编号</span>
              <span class="og-value">{{ o.group_code || '—' }}</span>
            </div>
            <div class="og-item">
              <span class="og-label">重量</span>
              <span class="og-value">{{ (o.weight_kg||0).toFixed(2) }} kg</span>
            </div>
            <div class="og-item">
              <span class="og-label">木架</span>
              <span class="og-value">{{ o.wooden_crate == null ? '未设置' : (o.wooden_crate ? '是' : '否') }}</span>
            </div>
            <div class="og-item og-span">
              <span class="og-label">进度</span>
              <span class="og-value">
                <div class="steps">
                  <div
                    v-for="(s,i) in STATUSES"
                    :key="s"
                    class="step-card"
                    :class="{ done: i <= statusIndex(o.status), current: i === statusIndex(o.status) }"
                  >
                    <span class="led" :class="{ on: i <= statusIndex(o.status) }" />
                    <span class="step-label">{{ s }}</span>
                  </div>
                </div>
              </span>
            </div>
            <div class="og-item">
              <span class="og-label">更新</span>
              <span class="og-value muted">{{ fmtDate(o.updated_at) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    </section>
  </template>

<script setup>
import { computed } from 'vue';
import { STATUSES, statusIndex, fmtDate } from '../../composables/useOrders';
const props = defineProps({ state: { type: Object, required: true } });

const isLoading = computed(() => {
  const l = props.state.loading;
  return typeof l === 'boolean' ? l : !!(l && l.value);
});

const errorText = computed(() => {
  const e = props.state.error;
  if (typeof e === 'string') return e;
  return e && e.value ? String(e.value) : '';
});

const totals = computed(() => props.state.totals || {});
const statsVisible = computed(() => {
  const t = totals.value || {};
  const ordersLen = Array.isArray(props.state.orders) ? props.state.orders.length : 0;
  return ordersLen > 0 || (t.count || 0) > 0 || (t.total_weight || 0) > 0 || (t.total_shipping_fee || 0) > 0;
});

// progress now rendered as step cards with LED, no percent bar
</script>

<style>
 .title-wrap { margin: 0 0 8px; }
 .title-wrap.compact { margin-bottom: 6px; }
.title-fallback { font-size: 18px; font-weight: 800; letter-spacing: 0.5px; color: var(--text); }

.orders-list { display: grid; gap: 10px; }
.stats-row { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin-bottom: 8px; align-items: stretch; }
.stat-chip { display: inline-flex; align-items: center; justify-content: space-between; gap: 8px; padding: 12px 14px; border-radius: 12px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); color: #cbd5e1; font-size: 15px; width: 100%; box-sizing: border-box; }
.stat-label { color: #9ca3af; font-size: 14px; }
.stat-value { color: #e5e7eb; font-weight: 700; }
@media (max-width: 800px) { .stats-row { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 480px) { .stats-row { grid-template-columns: 1fr; } }
.order-card { padding: 12px; border: 1px solid rgba(255,255,255,0.12); border-radius: 12px; background: rgba(255,255,255,0.06); }
.order-top { display:flex; align-items:center; justify-content: space-between; gap: 8px; margin-bottom: 8px; }
.order-no { color:#e5e7eb; font-weight: 700; }
.order-status { display:inline-block; padding: 4px 8px; border-radius: 999px; border:1px solid rgba(126,246,177,0.45); color:#a7f3d0; background: rgba(126,246,177,0.08); font-size: 12px; white-space: nowrap; }
.order-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px 12px; }
.og-item { display:flex; align-items: baseline; gap: 6px; min-width: 0; }
.og-label { color:#9ca3af; font-size: 13px; white-space: nowrap; }
.og-value { color:#d1d5db; font-size: 14px; overflow: hidden; text-overflow: ellipsis; }
.og-item.og-span { grid-column: 1 / -1; }
.muted { color:#9ca3af; }
@media (max-width: 560px) { .order-grid { grid-template-columns: 1fr; } }

/* step cards progress */
.steps { display: flex; flex-wrap: wrap; gap: 8px; }
.step-card { display: inline-flex; align-items: center; gap: 8px; padding: 8px 10px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.14); background: rgba(255,255,255,0.05); }
.step-card.done { border-color: rgba(126,246,177,0.45); background: rgba(126,246,177,0.06); }
.step-card.current { box-shadow: 0 0 0 2px rgba(126,246,177,0.18) inset; }
.led { width: 12px; height: 12px; border-radius: 999px; background: #4b5563; border: 2px solid rgba(255,255,255,0.25); box-sizing: border-box; }
.led.on { background: #22c55e; border-color: rgba(126,246,177,0.8); box-shadow: 0 0 8px rgba(34,197,94,0.45); }
.step-label { color:#d1d5db; font-size: 13px; }
</style>
