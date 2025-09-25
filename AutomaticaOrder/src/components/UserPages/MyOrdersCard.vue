<template>
  <section class="my-orders">
    <div class="title-wrap"><span class="title-text">我的订单</span></div>
    <div v-if="!isLoggedIn" class="muted">请先登录后查看绑定的订单。</div>
    <div v-else>
      <div class="controls-card">
        <div class="controls-header">
          <span class="controls-label">我的编号</span>
          <button class="btn-outline" type="button" @click="loadCodes">刷新</button>
        </div>
        <div class="controls-grid">
          <select class="input controls-select" v-model="currentCode" @change="handleCodeChange">
            <option v-for="code in codes" :key="code" :value="code">{{ code }}</option>
          </select>
          <input class="input controls-input" v-model="newCode" placeholder="新增编号，如 A666" />
          <button class="btn-solid" type="button" @click="addCode">绑定编号</button>
          <button class="btn-outline" type="button" :disabled="!currentCode" @click="removeCode">解绑当前</button>
        </div>
      </div>

      <div class="content-card" v-if="currentCode">
        <div class="header-row">
          <div class="summary-row">
            <span class="muted">当前编号：{{ currentCode }}</span>
            <span class="muted">共 {{ filteredOrders.length }} 条</span>
          </div>
          <div class="filter-group">
            <button type="button" class="filter-btn" :class="{ active: filterMode === 'pending' }" @click="setFilter('pending')">
              未完成 ({{ pendingCount }})
            </button>
            <button type="button" class="filter-btn" :class="{ active: filterMode === 'completed' }" @click="setFilter('completed')">
              已完成 ({{ completedCount }})
            </button>
          </div>
        </div>

        <div v-if="loading" class="muted">加载中…</div>
        <template v-else>
          <template v-if="pagedOrders.length">
            <transition-group name="order-card" tag="div" class="orders-list">
              <article v-for="order in pagedOrders" :key="orderKey(order)" :class="['order-card', { expanded: isExpanded(order) }]">
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
              <button class="pager-btn" type="button" :disabled="page === 1" @click="prevPage">上一页</button>
              <span class="muted">第 {{ page }} / {{ pageCount }} 页</span>
              <button class="pager-btn" type="button" :disabled="page === pageCount" @click="nextPage">下一页</button>
            </div>
          </template>
          <div v-else class="muted">暂无此分类的订单。</div>
        </template>
      </div>

      <div v-else class="muted">{{ msg || '尚未绑定编号，可输入后点击绑定。' }}</div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { adminApi, apiFetch } from '../../composables/useAdminApi';
import { useAuthState } from '../../composables/useAuthState';
import { formatDateCn } from '../../utils/date';
import { useNotifier } from '../../composables/useNotifier';
import { STATUSES, statusIndex } from '../../composables/useOrders';

const { isLoggedIn } = useAuthState();
const { showNotice } = useNotifier();

const codes = ref<string[]>([]);
const currentCode = ref('');
const newCode = ref('');
const rawOrders = ref<any[]>([]);
const msg = ref('');
const loading = ref(false);

const pageSize = 5;
const page = ref(1);
const filterMode = ref<'pending' | 'completed'>('pending');
const expandedKeys = ref<Set<string>>(new Set());
const finalStatus = STATUSES[STATUSES.length - 1];

async function loadCodes() {
  if (!isLoggedIn.value) return;
  try {
    const j = await apiFetch('/orderapi/user/codes');
    codes.value = j.codes || [];
    if (!codes.value.includes(currentCode.value)) {
      currentCode.value = codes.value[0] || '';
    }
    if (currentCode.value) await loadOrders();
    msg.value = codes.value.length === 0 ? '尚未绑定编号，可输入后点击绑定。' : '';
  } catch (error: any) {
    const message = error?.message || '加载编号失败';
    msg.value = message;
    showNotice({ type: 'error', message });
  }
}

function handleCodeChange() {
  if (currentCode.value) loadOrders();
}

async function addCode() {
  const code = (newCode.value || '').trim();
  if (!code) {
    showNotice({ type: 'error', message: '请输入要绑定的编号' });
    return;
  }
  try {
    await apiFetch('/orderapi/user/codes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code }) });
    showNotice({ type: 'success', message: '编号已绑定' });
    newCode.value = '';
    await loadCodes();
  } catch (error: any) {
    showNotice({ type: 'error', message: error?.message || '绑定失败' });
  }
}

async function removeCode() {
  if (!currentCode.value) return;
  if (!window.confirm(`确认解绑编号 ${currentCode.value} 吗？`)) return;
  try {
    await apiFetch('/orderapi/user/codes', { method: 'DELETE', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code: currentCode.value }) });
    showNotice({ type: 'success', message: '编号已解绑' });
    currentCode.value = '';
    rawOrders.value = [];
    await loadCodes();
  } catch (error: any) {
    showNotice({ type: 'error', message: error?.message || '解绑失败' });
  }
}

async function loadOrders() {
  if (!currentCode.value) return;
  loading.value = true;
  msg.value = '加载中…';
  try {
    const data = await adminApi.listByCode(currentCode.value, { page: 1, page_size: 200 });
    const list = Array.isArray(data.orders) ? data.orders.slice() : [];
    list.sort((a, b) => {
      const timeA = Date.parse(a?.updated_at || '');
      const timeB = Date.parse(b?.updated_at || '');
      return (isNaN(timeB) ? 0 : timeB) - (isNaN(timeA) ? 0 : timeA);
    });
    rawOrders.value = list;
    msg.value = list.length ? '' : '暂无订单';
    page.value = 1;
    expandedKeys.value = new Set();
  } catch (error: any) {
    const message = error?.message || '加载失败';
    msg.value = message;
    showNotice({ type: 'error', message });
  } finally {
    loading.value = false;
  }
}

const pendingOrders = computed(() => rawOrders.value.filter(order => !isCompleted(order)));
const completedOrders = computed(() => rawOrders.value.filter(order => isCompleted(order)));
const pendingCount = computed(() => pendingOrders.value.length);
const completedCount = computed(() => completedOrders.value.length);

const filteredOrders = computed(() => (filterMode.value === 'completed' ? completedOrders.value : pendingOrders.value));
const pageCount = computed(() => Math.max(1, Math.ceil(filteredOrders.value.length / pageSize)));
const pagedOrders = computed(() => {
  const start = (page.value - 1) * pageSize;
  return filteredOrders.value.slice(start, start + pageSize);
});

watch(isLoggedIn, loggedIn => {
  if (loggedIn) {
    loadCodes();
  } else {
    codes.value = [];
    currentCode.value = '';
    rawOrders.value = [];
    msg.value = '';
  }
});

function setFilter(mode: 'pending' | 'completed') {
  if (filterMode.value === mode) return;
  filterMode.value = mode;
  page.value = 1;
  expandedKeys.value = new Set();
}

watch(filteredOrders, () => {
  const maxPage = pageCount.value;
  if (page.value > maxPage) page.value = maxPage;
  cleanupExpanded();
});

function prevPage() {
  if (page.value > 1) page.value -= 1;
}

function nextPage() {
  if (page.value < pageCount.value) page.value += 1;
}

function orderKey(order: any) {
  if (!order) return '';
  if (order.id != null) return `id-${order.id}`;
  if (order.order_no) return `no-${order.order_no}`;
  if (order.group_code || order.updated_at) return `g-${order.group_code || 'unknown'}-${order.updated_at || ''}`;
  return JSON.stringify(order);
}

function toggleExpand(order: any) {
  const key = orderKey(order);
  const next = new Set(expandedKeys.value);
  if (next.has(key)) next.delete(key); else next.add(key);
  expandedKeys.value = next;
}

function isExpanded(order: any) {
  return expandedKeys.value.has(orderKey(order));
}

function cleanupExpanded() {
  const valid = new Set(filteredOrders.value.map(orderKey));
  const next = new Set<string>();
  expandedKeys.value.forEach(key => {
    if (valid.has(key)) next.add(key);
  });
  expandedKeys.value = next;
}

function isCompleted(order: any) {
  return (order?.status || '') === finalStatus;
}

function formatWeight(value: any) {
  const n = Number(value || 0);
  return `${n.toFixed(2)} kg`;
}

function woodenText(flag: any) {
  if (flag === true) return '是';
  if (flag === false) return '否';
  return '未设置';
}

onMounted(() => {
  if (isLoggedIn.value) loadCodes();
});
</script>

<style scoped>
.my-orders { display: flex; flex-direction: column; gap: 26px; }
.title-wrap { margin: 0 0 8px; }
.title-text { font-size: 20px; font-weight: 800; letter-spacing: 0.5px; color: var(--text); }
.muted { color: #9ca3af; }

.controls-card { background: rgba(12, 18, 28, 0.48); border: 1px solid rgba(148, 163, 184, 0.24); border-radius: 20px; padding: 18px; display: flex; flex-direction: column; gap: 14px; backdrop-filter: blur(18px) saturate(1.4); box-shadow: 0 18px 38px rgba(3, 10, 20, 0.28); }
.controls-header { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.controls-label { font-size: 0.92rem; font-weight: 600; color: rgba(225, 233, 245, 0.84); letter-spacing: 0.3px; }
.controls-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; align-items: center; }
.controls-select, .controls-input { width: 100%; }

.controls-card .btn-outline,
.controls-card .btn-solid {
  height: 40px;
  border-radius: 12px;
  font-weight: 600;
  letter-spacing: 0.3px;
  padding: 0 18px;
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  transition: transform 180ms ease, box-shadow 220ms ease, border-color 200ms ease, background 200ms ease;
}

.controls-card .btn-outline {
  border: 1px solid rgba(148, 176, 215, 0.35);
  background: linear-gradient(135deg, rgba(148, 176, 215, 0.12), rgba(24, 40, 68, 0.32));
  color: #dbeafe;
}
.controls-card .btn-outline:hover:not(:disabled) {
  border-color: rgba(148, 205, 255, 0.55);
  background: linear-gradient(135deg, rgba(73, 119, 199, 0.24), rgba(17, 32, 58, 0.48));
  box-shadow: 0 16px 32px rgba(28, 67, 140, 0.32);
  color: #f8fbff;
}

.controls-card .btn-solid {
  border: 1px solid rgba(102, 212, 255, 0.4);
  background: linear-gradient(135deg, rgba(56, 189, 248, 0.32), rgba(56, 130, 248, 0.22));
  color: #f0f9ff;
  box-shadow: 0 16px 34px rgba(23, 78, 166, 0.32);
}
.controls-card .btn-solid:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: rgba(102, 212, 255, 0.6);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.32), rgba(14, 165, 233, 0.32));
  box-shadow: 0 22px 42px rgba(17, 62, 140, 0.38);
}
.controls-card .btn-solid:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 12px 26px rgba(17, 62, 140, 0.28);
}

.content-card { background: rgba(12, 18, 28, 0.45); border: 1px solid rgba(148, 163, 184, 0.22); border-radius: 20px; padding: 18px; display: flex; flex-direction: column; gap: 14px; backdrop-filter: blur(18px) saturate(1.35); box-shadow: 0 18px 38px rgba(3, 10, 20, 0.24); }
.header-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.summary-row { display: flex; align-items: center; gap: 16px; }
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
.card-toggle.open .chevron { transform: rotate(180deg); }
.preview-line { display: flex; flex: 1; align-items: center; justify-content: space-between; gap: 12px; }
.order-no { font-weight: 700; color: #f3f7ff; font-size: 1.02rem; letter-spacing: 0.4px; }
.order-status { display: inline-flex; align-items: center; justify-content: center; padding: 4px 12px; border-radius: 999px; border: 1px solid rgba(126,246,177,0.32); color: #bbf7d0; background: rgba(34,197,94,0.14); font-size: 0.82rem; min-width: 94px; transition: transform 160ms ease, box-shadow 200ms ease; }
.order-status.done { border-color: rgba(59,130,246,0.38); color: #bfdbfe; background: rgba(59,130,246,0.18); box-shadow: 0 6px 18px rgba(59,130,246,0.22); }
.chevron { width: 16px; height: 10px; color: rgba(226,238,255,0.65); transition: transform 200ms ease, color 200ms ease; }
.card-toggle:hover .chevron { color: rgba(255,255,255,0.9); }

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

@media (max-width: 960px) {
  .controls-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .content-card { padding: 14px; }
}

@media (max-width: 640px) {
  .controls-grid { grid-template-columns: 1fr; }
  .header-row { flex-direction: column; align-items: flex-start; gap: 16px; }
  .detail-grid { grid-template-columns: 1fr; }
  .filter-group { width: 100%; justify-content: center; flex-wrap: wrap; }
  .pagination { justify-content: center; }
}

@media (max-width: 480px) {
  .preview-line { flex-direction: column; align-items: flex-start; gap: 8px; }
  .order-status { align-self: flex-start; }
  .card-toggle { padding: 16px 18px; }
}
</style>
