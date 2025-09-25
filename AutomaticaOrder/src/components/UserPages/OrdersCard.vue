<template>
  <section class="orders-shell">
    <div class="header-row">
      <div class="title-wrap compact">
        <span class="title-fallback">查询结果</span>
      </div>
      <div class="filter-group">
        <button
          type="button"
          class="filter-btn"
          :class="{ active: filterMode === 'pending' }"
          @click="setFilter('pending')"
        >
          未完成 ({{ pendingCount }})
        </button>
        <button
          type="button"
          class="filter-btn"
          :class="{ active: filterMode === 'completed' }"
          @click="setFilter('completed')"
        >
          已完成 ({{ completedCount }})
        </button>
      </div>
    </div>

    <div v-if="isLoading" class="muted">加载中...</div>
    <div v-else-if="errorText" class="muted">{{ errorText }}</div>
    <div v-else>
      <template v-if="pagedOrders.length">
        <transition-group name="order-card" tag="div" class="orders-list">
          <article
            v-for="order in pagedOrders"
            :key="orderKey(order)"
            :class="['order-card', { expanded: isExpanded(order) }]"
          >
            <button type="button" class="card-toggle" :class="{ open: isExpanded(order) }" @click="toggleExpand(order)">
              <div class="preview-line">
                <span class="order-no">{{ order.order_no }}</span>
                <span class="order-status" :class="{ done: isCompleted(order) }">{{ order.status }}</span>
              </div>
              <svg class="chevron" viewBox="0 0 16 10" fill="none">
                <path d="M1 1l7 7 7-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </button>
            <transition name="expand-card">
              <div v-if="isExpanded(order)" class="order-details">
                <div class="detail-grid">
                  <div class="detail-item">
                    <span class="label">编号</span>
                    <span class="value">{{ order.group_code || '—' }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="label">重量</span>
                    <span class="value">{{ formatWeight(order.weight_kg) }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="label">木架</span>
                    <span class="value">{{ woodenText(order.wooden_crate) }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="label">更新</span>
                    <span class="value muted">{{ formatDateCn(order.updated_at) }}</span>
                  </div>
                </div>
                <div class="step-flow">
                  <div
                    v-for="(status, idx) in STATUSES"
                    :key="status"
                    class="step-chip"
                    :class="{ passed: idx <= statusIndex(order.status), current: idx === statusIndex(order.status) }"
                  >
                    <span class="dot" />
                    <span class="text">{{ status }}</span>
                  </div>
                </div>
              </div>
            </transition>
          </article>
        </transition-group>

        <div v-if="pageCount > 1" class="pagination">
          <button type="button" class="pager-btn" :disabled="page === 1" @click="prevPage">上一页</button>
          <span class="muted">第 {{ page }} / {{ pageCount }} 页</span>
          <button type="button" class="pager-btn" :disabled="page === pageCount" @click="nextPage">下一页</button>
        </div>
      </template>
      <div v-else class="muted">暂无此分类的订单。</div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { STATUSES, statusIndex } from '../../composables/useOrders';
import { formatDateCn } from '../../utils/date';

const props = defineProps({ state: { type: Object, required: true } });

const pageSize = 5;
const filterMode = ref('pending');
const page = ref(1);
const expandedKeys = ref(new Set());
const finalStatus = STATUSES[STATUSES.length - 1];

const sortedOrders = computed(() => {
  const list = Array.isArray(props.state.orders) ? props.state.orders.slice() : [];
  return list.sort((a, b) => {
    const timeA = Date.parse(a?.updated_at || '');
    const timeB = Date.parse(b?.updated_at || '');
    return (isNaN(timeB) ? 0 : timeB) - (isNaN(timeA) ? 0 : timeA);
  });
});

const pendingOrders = computed(() => sortedOrders.value.filter(order => !isCompleted(order)));
const completedOrders = computed(() => sortedOrders.value.filter(order => isCompleted(order)));

const filteredOrders = computed(() => (filterMode.value === 'completed' ? completedOrders.value : pendingOrders.value));
const pendingCount = computed(() => pendingOrders.value.length);
const completedCount = computed(() => completedOrders.value.length);

const pageCount = computed(() => Math.max(1, Math.ceil(filteredOrders.value.length / pageSize)));

const pagedOrders = computed(() => {
  const start = (page.value - 1) * pageSize;
  return filteredOrders.value.slice(start, start + pageSize);
});

const isLoading = computed(() => {
  const l = props.state.loading;
  return typeof l === 'boolean' ? l : !!(l && l.value);
});

const errorText = computed(() => {
  const e = props.state.error;
  if (typeof e === 'string') return e;
  return e && e.value ? String(e.value) : '';
});

function resetPage() {
  page.value = 1;
}

watch(() => props.state.orders, () => {
  resetPage();
  cleanupExpanded();
});

watch(filterMode, () => {
  resetPage();
  cleanupExpanded();
});

watch(filteredOrders, () => {
  const max = pageCount.value;
  if (page.value > max) page.value = max;
  cleanupExpanded();
});

function setFilter(mode) {
  if (filterMode.value === mode) return;
  filterMode.value = mode;
  expandedKeys.value = new Set();
}

function prevPage() {
  if (page.value > 1) page.value -= 1;
}

function nextPage() {
  if (page.value < pageCount.value) page.value += 1;
}

function orderKey(order) {
  if (!order) return '';
  if (order.id != null) return `id-${order.id}`;
  if (order.order_no) return `no-${order.order_no}`;
  if (order.group_code || order.updated_at) return `g-${order.group_code || 'unknown'}-${order.updated_at || ''}`;
  return JSON.stringify(order);
}

function toggleExpand(order) {
  const key = orderKey(order);
  const next = new Set(expandedKeys.value);
  if (next.has(key)) next.delete(key); else next.add(key);
  expandedKeys.value = next;
}

function isExpanded(order) {
  return expandedKeys.value.has(orderKey(order));
}

function cleanupExpanded() {
  const validKeys = new Set(sortedOrders.value.map(order => orderKey(order)));
  const next = new Set();
  expandedKeys.value.forEach(key => {
    if (validKeys.has(key)) next.add(key);
  });
  expandedKeys.value = next;
}

function isCompleted(order) {
  return (order?.status || '') === finalStatus;
}

function formatWeight(value) {
  const num = Number(value || 0);
  return `${num.toFixed(2)} kg`;
}

function woodenText(flag) {
  if (flag === true) return '是';
  if (flag === false) return '否';
  return '未设置';
}
</script>

<style>
.orders-shell { display: flex; flex-direction: column; gap: 18px; }
.header-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.filter-group { display: inline-flex; align-items: center; gap: 8px; background: rgba(12, 26, 48, 0.58); border-radius: 999px; padding: 6px; border: 1px solid rgba(148, 205, 255, 0.22); box-shadow: inset 0 1px 0 rgba(255,255,255,0.08); backdrop-filter: blur(16px); }
.filter-btn { border: none; background: rgba(15, 40, 78, 0.18); color: rgba(226, 238, 255, 0.82); font-weight: 600; padding: 8px 18px; border-radius: 999px; cursor: pointer; transition: background 200ms ease, color 200ms ease, box-shadow 220ms ease, transform 160ms ease; }
.filter-btn:hover { background: rgba(59, 130, 246, 0.24); color: #f1f5ff; box-shadow: 0 10px 24px rgba(37, 99, 235, 0.28); }
.filter-btn.active { background: linear-gradient(135deg, rgba(96, 165, 250, 0.42), rgba(125, 211, 252, 0.28)); color: #0f172a; box-shadow: 0 12px 26px rgba(96, 165, 250, 0.32); transform: translateY(-1px); }

.orders-list { display: grid; gap: 12px; }
.order-card {
  background: rgba(13, 19, 32, 0.62);
  border: 1px solid rgba(148, 163, 184, 0.26);
  border-radius: 18px;
  overflow: hidden;
  position: relative;
  padding: 0 0 10px;
  box-shadow: 0 18px 36px rgba(2, 10, 20, 0.28);
  backdrop-filter: blur(18px);
}
.order-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.22), rgba(59, 130, 246, 0.18));
  box-shadow: 0 22px 42px rgba(17, 62, 140, 0.32);
  opacity: 0;
  transition: opacity 220ms ease;
  pointer-events: none;
  z-index: 0;
}
.order-card:hover::before,
.order-card:focus-within::before { opacity: 0.55; }
.order-card.expanded::before { opacity: 0.9; }
.order-card > * { position: relative; z-index: 1; }
.card-toggle { width: 100%; display: flex; align-items: center; justify-content: space-between; gap: 12px; background: transparent; border: none; color: inherit; padding: 18px 20px; cursor: pointer; position: relative; }
.card-toggle::after { content: ''; position: absolute; inset: 0; border-radius: inherit; background: linear-gradient(135deg, rgba(14,165,233,0.16), rgba(59,130,246,0.12)); opacity: 0; transition: opacity 220ms ease; z-index: -1; }
.card-toggle:hover::after { opacity: 1; }
.preview-line { display: flex; flex: 1; align-items: center; justify-content: space-between; gap: 12px; }
.order-no { font-weight: 700; color: #f3f7ff; font-size: 1.02rem; letter-spacing: 0.4px; }
.order-status { display: inline-flex; align-items: center; justify-content: center; padding: 4px 12px; border-radius: 999px; border: 1px solid rgba(126,246,177,0.32); color: #bbf7d0; background: rgba(34,197,94,0.14); font-size: 0.82rem; min-width: 94px; transition: transform 160ms ease, box-shadow 200ms ease; }
.order-status.done { border-color: rgba(59,130,246,0.38); color: #bfdbfe; background: rgba(59,130,246,0.18); box-shadow: 0 6px 18px rgba(59,130,246,0.22); }
.chevron { width: 16px; height: 10px; color: rgba(226,238,255,0.65); transition: transform 200ms ease, color 200ms ease; }
.card-toggle:hover .chevron { color: rgba(255,255,255,0.9); }
.card-toggle.open .chevron { transform: rotate(180deg); }

.order-details { padding: 0 20px 16px; display: grid; gap: 14px; }
.detail-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px 16px; }
.detail-item { display: flex; flex-direction: column; gap: 4px; }
.detail-item .label { font-size: 0.78rem; color: rgba(148, 163, 184, 0.85); letter-spacing: 0.2px; }
.detail-item .value { font-size: 0.92rem; color: #e5e7eb; }
.step-flow { display: flex; flex-wrap: wrap; gap: 10px; }
.step-chip { display: inline-flex; align-items: center; gap: 10px; padding: 9px 12px; border-radius: 12px; border: 1px solid rgba(148, 163, 184, 0.26); background: rgba(14, 23, 42, 0.58); color: rgba(229,231,235,0.86); font-size: 0.82rem; transition: border-color 200ms ease, background 200ms ease, box-shadow 200ms ease; box-shadow: inset 0 1px 0 rgba(255,255,255,0.08); }
.step-chip.passed,
.step-chip.current { border-color: rgba(39,255,100,0.32); background: rgba(39,255,100,0.12); color: #c5f9df; }
.step-chip.current { box-shadow: 0 0 0 1px rgba(125,211,252,0.28); }
.step-chip .dot { width: 10px; height: 10px; border-radius: 50%; background: rgba(125, 211, 252, 0.32); box-shadow: 0 0 8px rgba(96, 165, 250, 0.25); opacity: 1; }
.step-chip.passed .dot,
.step-chip.current .dot { background: #60a5fa; box-shadow: 0 0 12px rgba(96, 165, 250, 0.45); }

.pagination { display: flex; align-items: center; justify-content: flex-end; gap: 12px; margin-top: 12px; }
.pager-btn { border: 1px solid rgba(148, 205, 255, 0.26); background: rgba(15, 40, 78, 0.35); color: #e5f0ff; padding: 8px 18px; border-radius: 999px; cursor: pointer; transition: background 200ms ease, border-color 200ms ease, color 200ms ease, transform 160ms ease; backdrop-filter: blur(12px); }
.pager-btn:hover:not(:disabled) { background: rgba(59,130,246,0.24); border-color: rgba(148,205,255,0.48); color: #f8fbff; transform: translateY(-1px); box-shadow: 0 12px 26px rgba(37, 99, 235, 0.28); }
.pager-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.order-card-enter-active, .order-card-leave-active { transition: opacity 220ms ease, transform 220ms ease; }
.order-card-enter-from, .order-card-leave-to { opacity: 0; transform: translateY(8px); }
.expand-card-enter-active, .expand-card-leave-active { transition: opacity 200ms ease, transform 200ms ease; }
.expand-card-enter-from, .expand-card-leave-to { opacity: 0; transform: translateY(-6px); }

@media (max-width: 720px) {
  .header-row { flex-direction: column; align-items: flex-start; }
  .detail-grid { grid-template-columns: 1fr; }
  .filter-group { width: 100%; justify-content: center; flex-wrap: wrap; }
  .card-toggle { padding: 14px; }
}

@media (max-width: 480px) {
  .preview-line { flex-direction: column; align-items: flex-start; gap: 8px; }
  .order-status { align-self: flex-start; }
  .card-toggle { padding: 14px 16px; }
}
</style>
