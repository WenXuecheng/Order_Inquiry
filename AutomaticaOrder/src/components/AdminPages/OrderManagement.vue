<template>
  <section class="order-admin">
    <div v-if="!isAdminOrSuper" class="alert-card">
      <div class="alert">无权限：当前账号无权访问后台功能，请联系超级管理员开启权限。</div>
      <div class="row" style="margin-top:10px;">
        <a class="btn" href="/#/">返回首页</a>
      </div>
    </div>

    <template v-else>
      <div class="table-card">
        <div class="table-toolbar">
          <div class="toolbar-title">订单管理</div>
          <div class="toolbar-actions">
            <input class="input toolbar-input" v-model="listCode" placeholder="筛选编号，如 2025-01 或 A（留空=全部）" />
            <div class="toolbar-date-range">
              <input
                class="input toolbar-input"
                type="date"
                v-model="startDate"
                :max="endDate || undefined"
                aria-label="开始日期"
              />
              <span class="toolbar-date-sep">至</span>
              <input
                class="input toolbar-input"
                type="date"
                v-model="endDate"
                :min="startDate || undefined"
                aria-label="结束日期"
              />
            </div>
            <select class="input toolbar-input" v-model="statusFilter">
              <option value="">全部状态</option>
              <option v-for="status in STATUSES" :key="status" :value="status">{{ status }}</option>
            </select>
            <button class="toolbar-clear" type="button" @click="clearFilters" :disabled="!hasActiveFilters">清除</button>
            <div class="toolbar-button-row">
              <button class="btn-solid toolbar-btn" @click="resetAndQuery">查询</button>
              <button class="btn-outline toolbar-btn" @click="openImportModal">批量导入</button>
              <button class="btn-outline toolbar-btn" @click="exportOrders" :disabled="exporting">{{ exporting ? '导出中…' : '导出 Excel' }}</button>
              <button class="btn-outline toolbar-btn" @click="openCreate">新建订单</button>
            </div>
          </div>
        </div>
        <div class="table-head">
          <div class="summary">{{ summaryText }}</div>
          <div class="table-buttons">
            <button class="btn-outline" @click="prevPage" :disabled="page <= 1">上一页</button>
            <button class="btn-outline" @click="nextPage" :disabled="page >= pages">下一页</button>
            <button class="btn-danger" @click="bulkDelete" :disabled="selectedNos.length === 0">批量删除 ({{ selectedNos.length }})</button>
          </div>
        </div>
        <div class="table-wrapper" v-if="!isCompact">
          <table class="order-table">
            <thead>
              <tr>
                <th class="checkbox-cell">
                  <input type="checkbox" :checked="allSelected" @change="toggleAll($event)" />
                </th>
                <th>订单号</th>
                <th>编号</th>
                <th>重量</th>
                <th>状态</th>
                <th>更新日期</th>
                <th class="actions-cell">操作</th>
              </tr>
            </thead>
            <transition-group tag="tbody" name="table-row" appear>
              <tr v-for="order in list" :key="order.id">
                <td class="checkbox-cell">
                  <input type="checkbox" v-model="selectedNos" :value="order.order_no" />
                </td>
                <td>{{ order.order_no }}</td>
                <td>{{ order.group_code || '—' }}</td>
                <td>{{ formatWeight(order.weight_kg) }}</td>
                <td>{{ order.status }}</td>
                <td>{{ formatDateCn(order.updated_at) }}</td>
                <td class="actions-cell">
                  <button class="btn-outline" @click="openEdit(order)">编辑</button>
                  <button class="btn-danger" @click="deleteOne(order)">删除</button>
                </td>
              </tr>
            </transition-group>
            <tbody v-if="list.length === 0">
              <tr>
                <td colspan="7" class="empty">暂无数据</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="compact-list">
          <article
            v-for="order in list"
            :key="order.id"
            class="compact-card"
            @click="toggleCardSelection(order)"
          >
            <div class="card-header">
              <div class="card-title">{{ order.order_no }}</div>
              <label class="card-checkbox" @click.stop>
                <input type="checkbox" v-model="selectedNos" :value="order.order_no" />
              </label>
            </div>
            <div class="card-meta">
              <span>编号：{{ order.group_code || '—' }}</span>
              <span>状态：{{ order.status }}</span>
            </div>
            <div class="card-meta">
              <span>重量：{{ formatWeight(order.weight_kg) }}</span>
              <span>更新：{{ formatDateCn(order.updated_at) }}</span>
            </div>
            <div class="card-actions" @click.stop>
              <button class="btn-outline" type="button" @click="openEdit(order)">编辑</button>
              <button class="btn-danger" type="button" @click="deleteOne(order)">删除</button>
            </div>
          </article>
          <div v-if="list.length === 0" class="empty">暂无数据</div>
        </div>
        <div v-if="msg" class="status-text">{{ msg }}</div>
      </div>
    </template>

    <teleport to="body">
      <transition name="modal-fade">
        <div v-if="importState.visible" class="modal-overlay" @click.self="closeImportModal">
          <div class="modal-card">
            <h3 class="modal-title">批量导入订单</h3>
            <p class="modal-tip">请选择 .xlsx 文件，系统会根据模板批量创建或更新订单。</p>
            <input class="input" type="file" accept=".xlsx" @change="onImportFile" />
            <div v-if="importState.message" class="modal-message">{{ importState.message }}</div>
            <div v-if="importState.stats" class="modal-stats">
              <div>成功：{{ importState.stats.created || 0 }} 条</div>
              <div>更新：{{ importState.stats.updated || 0 }} 条</div>
              <div>跳过：{{ importState.stats.skipped || 0 }} 条</div>
            </div>
            <div class="modal-actions">
              <button class="btn-outline" type="button" @click="closeImportModal" :disabled="importState.uploading">取消</button>
              <button class="btn-gradient-text" type="button" @click="handleImport" :disabled="importState.uploading || !importState.file">
                {{ importState.uploading ? '导入中…' : '开始导入' }}
              </button>
            </div>
          </div>
        </div>
      </transition>
    </teleport>

    <teleport to="body">
      <transition name="modal-fade">
        <div v-if="editState.visible" class="modal-overlay" @click.self="closeEdit">
          <div class="modal-card">
            <h3 class="modal-title">编辑订单</h3>
            <div v-if="editState.order" class="grid">
              <label>订单号
                <input class="input" :value="editState.order.order_no" disabled />
              </label>
              <label>所属编号
                <input class="input" v-model="editState.order.group_code" />
              </label>
              <label>重量(kg)
                <input class="input" type="number" step="0.01" v-model="editState.order.weight_kg" />
              </label>
              <label>运费
                <input class="input" type="number" step="0.01" v-model="editState.order.shipping_fee" />
              </label>
              <label>状态
                <select class="input" v-model="editState.order.status">
                  <option v-for="s in STATUSES" :key="s" :value="s">{{ s }}</option>
                </select>
              </label>
              <label>是否打木架
                <select class="input" v-model="editState.order.wooden_crate">
                  <option :value="null">未设置</option>
                  <option :value="true">是</option>
                  <option :value="false">否</option>
                </select>
              </label>
            </div>
            <div class="modal-actions">
              <button class="btn-outline" type="button" @click="closeEdit" :disabled="editState.loading">取消</button>
              <button class="btn-gradient-text" type="button" @click="saveEdit" :disabled="editState.loading">{{ editState.loading ? '保存中…' : '保存修改' }}</button>
            </div>
          </div>
        </div>
      </transition>
    </teleport>

    <teleport to="body">
      <transition name="modal-fade">
        <div v-if="createState.visible" class="modal-overlay" @click.self="closeCreate">
          <div class="modal-card">
            <h3 class="modal-title">新建订单</h3>
            <div class="grid">
              <label>订单号
                <input class="input" v-model="createState.form.order_no" placeholder="必填" />
              </label>
              <label>所属编号
                <input class="input" v-model="createState.form.group_code" placeholder="如 2025-01" />
              </label>
              <label>重量(kg)
                <input class="input" type="number" step="0.01" v-model="createState.form.weight_kg" />
              </label>
              <label>运费
                <input class="input" type="number" step="0.01" v-model="createState.form.shipping_fee" />
              </label>
              <label>状态
                <select class="input" v-model="createState.form.status">
                  <option v-for="s in STATUSES" :key="s" :value="s">{{ s }}</option>
                </select>
              </label>
              <label>是否打木架
                <select class="input" v-model="createState.form.wooden_crate">
                  <option :value="null">未设置</option>
                  <option :value="true">是</option>
                  <option :value="false">否</option>
                </select>
              </label>
            </div>
            <div class="modal-actions">
              <button class="btn-outline" type="button" @click="closeCreate" :disabled="createState.loading">取消</button>
              <button class="btn-gradient-text" type="button" @click="submitCreate" :disabled="createState.loading">{{ createState.loading ? '创建中…' : '确认创建' }}</button>
            </div>
          </div>
        </div>
      </transition>
    </teleport>

    <teleport to="body">
      <transition name="modal-fade">
        <div v-if="feedbackState.visible" class="modal-overlay" @click.self="closeFeedback">
          <div class="feedback-card" :class="`feedback-${feedbackState.type}`">
            <div class="feedback-message">{{ feedbackState.message }}</div>
          </div>
        </div>
      </transition>
    </teleport>

    <teleport to="body">
      <transition name="modal-fade">
        <div v-if="confirmDeleteState.visible" class="modal-overlay" @click.self="closeDeleteConfirm">
          <div class="modal-card confirm-card">
            <h3 class="modal-title">确认删除</h3>
            <p class="confirm-text">
              {{ confirmDeleteState.mode === 'single'
                ? `确定要删除订单 ${confirmDeleteState.targetOrderNo || ''} 吗？`
                : `确定要删除选中的 ${confirmDeleteState.count} 条订单吗？` }}
            </p>
            <div class="modal-actions">
              <button class="btn-outline" type="button" @click="closeDeleteConfirm" :disabled="confirmDeleteState.loading">取消</button>
              <button class="btn-danger" type="button" @click="confirmDelete" :disabled="confirmDeleteState.loading">
                {{ confirmDeleteState.loading ? '删除中…' : '确认删除' }}
              </button>
            </div>
          </div>
        </div>
      </transition>
    </teleport>
  </section>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue';
import { adminApi, getRole } from '../../composables/useAdminApi';
import { formatDateCn } from '../../utils/date';
import { STATUSES } from '../../composables/useOrders';
import { useNotifier } from '../../composables/useNotifier';

const { showNotice } = useNotifier();
const adminRole = getRole() || '';
const isAdminOrSuper = adminRole === 'admin' || adminRole === 'superadmin';

const list = ref([]);
const listCode = ref('');
const startDate = ref('');
const endDate = ref('');
const statusFilter = ref('');
const page = ref(1);
const pages = ref(1);
const total = ref(0);
const msg = ref('');
const loading = ref(false);
const exporting = ref(false);
const pageSize = 20;
const isCompact = ref(false);
let compactQuery = null;
const compactListener = event => {
  isCompact.value = event.matches;
};

const createState = reactive({
  visible: false,
  loading: false,
  form: {
    order_no: '',
    group_code: '',
    weight_kg: '',
    shipping_fee: '',
    status: STATUSES[0],
    wooden_crate: null,
  },
});

const importState = reactive({
  visible: false,
  file: null,
  message: '',
  stats: null,
  uploading: false,
});

const editState = reactive({
  visible: false,
  order: null,
  loading: false,
});

const confirmDeleteState = reactive({
  visible: false,
  loading: false,
  mode: 'single',
  targetOrderNo: '',
  count: 0,
});

const selectedNos = ref([]);
const feedbackState = reactive({ visible: false, message: '', type: 'success' });
let feedbackTimer = null;

const pageStartIndex = computed(() => {
  if (!list.value.length) return 0;
  return (page.value - 1) * pageSize + 1;
});

const pageEndIndex = computed(() => {
  if (!list.value.length) return 0;
  return pageStartIndex.value + list.value.length - 1;
});

const summaryText = computed(() => {
  const totalCount = total.value;
  if (!totalCount) {
    return list.value.length
      ? `第 ${page.value} / ${pages.value} 页 · 显示 ${list.value.length} 条`
      : '暂无数据';
  }
  if (!list.value.length) {
    return `共 ${totalCount} 条 · 第 ${page.value} / ${pages.value} 页`;
  }
  return `显示 ${pageStartIndex.value}-${pageEndIndex.value} / ${totalCount} 条 · 第 ${page.value} / ${pages.value} 页`;
});

const allSelected = computed(() => list.value.length > 0 && selectedNos.value.length === list.value.length);

const hasActiveFilters = computed(() => {
  return Boolean(
    listCode.value.trim() ||
    startDate.value ||
    endDate.value ||
    statusFilter.value
  );
});

function resetCreateForm() {
  createState.form.order_no = '';
  createState.form.group_code = '';
  createState.form.weight_kg = '';
  createState.form.shipping_fee = '';
  createState.form.status = STATUSES[0];
  createState.form.wooden_crate = null;
}

async function loadList(targetPage = 1) {
  loading.value = true;
  msg.value = '加载中…';
  try {
    const code = listCode.value.trim();
    const queryParams = {
      page: targetPage,
      page_size: pageSize,
    };
    if (statusFilter.value) queryParams.status = statusFilter.value;
    if (startDate.value) queryParams.start_date = startDate.value;
    if (endDate.value) queryParams.end_date = endDate.value;
    const data = await adminApi.listByCode(code, queryParams);
    list.value = data.orders || [];
    page.value = data.page || targetPage;
    const totalCount = data.total ?? data.totals?.count ?? list.value.length;
    total.value = totalCount;
    pages.value = data.pages || Math.max(1, Math.ceil(totalCount / pageSize));
    if (list.value.length === 0 && totalCount > 0 && page.value > pages.value) {
      await loadList(Math.max(1, pages.value));
      return;
    }
    selectedNos.value = [];
    msg.value = list.value.length ? '' : '暂无数据';
  } catch (error) {
    const message = error?.message || '加载失败';
    msg.value = message;
    showNotice({ type: 'error', message });
  } finally {
    loading.value = false;
  }
}

function resetAndQuery() {
  loadList(1);
}

function clearFilters() {
  const hadFilters = hasActiveFilters.value;
  listCode.value = '';
  startDate.value = '';
  endDate.value = '';
  statusFilter.value = '';
  selectedNos.value = [];
  if (hadFilters) {
    loadList(1);
  }
}

function toggleAll(event) {
  const checked = event?.target?.checked;
  if (checked) {
    selectedNos.value = list.value
      .map(item => String(item.order_no || '').trim())
      .filter(value => value.length > 0);
  } else {
    selectedNos.value = [];
  }
}

function toggleCardSelection(order) {
  const value = String(order?.order_no || '').trim();
  if (!value) return;
  const current = [...selectedNos.value];
  const idx = current.indexOf(value);
  if (idx >= 0) {
    current.splice(idx, 1);
  } else {
    current.push(value);
  }
  selectedNos.value = current;
}

function prevPage() {
  if (page.value > 1) loadList(page.value - 1);
}

function nextPage() {
  if (page.value < pages.value) loadList(page.value + 1);
}

function openEdit(order) {
  editState.visible = true;
  editState.order = { ...order };
}

function closeEdit() {
  if (editState.loading) return;
  editState.visible = false;
  editState.order = null;
}

function showFeedback(message, type = 'success') {
  feedbackState.visible = true;
  feedbackState.message = message;
  feedbackState.type = type;
  if (typeof window !== 'undefined') {
    if (feedbackTimer) {
      window.clearTimeout(feedbackTimer);
      feedbackTimer = null;
    }
    feedbackTimer = window.setTimeout(() => {
      closeFeedback();
    }, 2400);
  }
}

function closeFeedback() {
  feedbackState.visible = false;
  feedbackState.message = '';
  if (typeof window !== 'undefined' && feedbackTimer) {
    window.clearTimeout(feedbackTimer);
    feedbackTimer = null;
  }
}

function closeDeleteConfirm() {
  if (confirmDeleteState.loading) return;
  confirmDeleteState.visible = false;
  confirmDeleteState.targetOrderNo = '';
  confirmDeleteState.count = 0;
  confirmDeleteState.mode = 'single';
}

async function confirmDelete() {
  if (confirmDeleteState.loading) return;
  confirmDeleteState.loading = true;
  let success = false;
  try {
    if (confirmDeleteState.mode === 'single') {
      if (!confirmDeleteState.targetOrderNo) throw new Error('未找到订单号');
      await adminApi.deleteOrder(confirmDeleteState.targetOrderNo);
      const idx = selectedNos.value.indexOf(confirmDeleteState.targetOrderNo);
      if (idx >= 0) {
        const next = [...selectedNos.value];
        next.splice(idx, 1);
        selectedNos.value = next;
      }
      showFeedback('订单已删除', 'success');
    } else {
      const codes = selectedNos.value.map(code => String(code || '').trim()).filter(Boolean);
      if (!codes.length) throw new Error('未选择订单');
      await adminApi.deleteOrdersBulk(codes);
      selectedNos.value = [];
      showFeedback('批量删除完成', 'success');
    }
    success = true;
    confirmDeleteState.visible = false;
    confirmDeleteState.targetOrderNo = '';
    confirmDeleteState.count = 0;
    confirmDeleteState.mode = 'single';
    await loadList(page.value);
  } catch (error) {
    const message = error?.message || '删除失败';
    showFeedback(message, 'error');
  } finally {
    confirmDeleteState.loading = false;
    if (success || !confirmDeleteState.loading) {
      closeDeleteConfirm();
    }
  }
}

async function saveEdit() {
  if (!editState.order) return;
  editState.loading = true;
  try {
    await adminApi.updateOrder(editState.order.order_no, { ...editState.order });
    showFeedback('订单已更新', 'success');
    editState.loading = false;
    closeEdit();
    loadList(page.value);
    return;
  } catch (error) {
    const message = error?.message || '保存失败';
    showFeedback(message, 'error');
  } finally {
    editState.loading = false;
  }
}

function openCreate() {
  resetCreateForm();
  createState.visible = true;
}

function closeCreate() {
  if (createState.loading) return;
  createState.visible = false;
}

async function submitCreate() {
  if (!createState.form.order_no.trim()) {
    showNotice({ type: 'error', message: '请填写订单号' });
    return;
  }
  createState.loading = true;
  try {
    const weight = createState.form.weight_kg !== '' ? Number(createState.form.weight_kg) : null;
    if (weight !== null && Number.isNaN(weight)) {
      showNotice({ type: 'error', message: '重量格式不正确' });
      createState.loading = false;
      return;
    }
    const fee = createState.form.shipping_fee !== '' ? Number(createState.form.shipping_fee) : null;
    if (fee !== null && Number.isNaN(fee)) {
      showNotice({ type: 'error', message: '运费格式不正确' });
      createState.loading = false;
      return;
    }
    const payload = {
      order_no: createState.form.order_no.trim(),
      group_code: createState.form.group_code.trim() || null,
      weight_kg: weight,
      shipping_fee: fee,
      status: createState.form.status,
      wooden_crate: createState.form.wooden_crate,
    };
    await adminApi.createOrder(payload);
    showFeedback('订单已创建', 'success');
    createState.visible = false;
    resetCreateForm();
    loadList(page.value);
  } catch (error) {
    const message = error?.message || '创建失败';
    showFeedback(message, 'error');
  } finally {
    createState.loading = false;
  }
}

async function deleteOne(order) {
  const orderNo = String(order?.order_no || '').trim();
  if (!orderNo) return;
  confirmDeleteState.mode = 'single';
  confirmDeleteState.targetOrderNo = orderNo;
  confirmDeleteState.count = 1;
  confirmDeleteState.loading = false;
  confirmDeleteState.visible = true;
}

async function bulkDelete() {
  if (selectedNos.value.length === 0) return;
  confirmDeleteState.mode = 'bulk';
  confirmDeleteState.count = selectedNos.value.length;
  confirmDeleteState.targetOrderNo = '';
  confirmDeleteState.loading = false;
  confirmDeleteState.visible = true;
}

function openImportModal() {
  importState.visible = true;
  importState.message = '';
  importState.stats = null;
  importState.file = null;
}

function closeImportModal() {
  if (importState.uploading) return;
  importState.visible = false;
}

function onImportFile(event) {
  const [file] = event.target?.files || [];
  importState.file = file || null;
}

async function handleImport() {
  if (!importState.file) return;
  importState.uploading = true;
  importState.message = '正在上传…';
  try {
    const stats = await adminApi.importExcel(importState.file);
    importState.message = '导入完成';
    importState.stats = stats;
    showNotice({ type: 'success', message: '导入完成' });
    loadList(page.value);
  } catch (error) {
    importState.message = error?.message || '导入失败';
    showNotice({ type: 'error', message: importState.message });
  } finally {
    importState.uploading = false;
    importState.file = null;
  }
}

function formatWeight(value) {
  const n = Number(value || 0);
  return `${n.toFixed(2)} kg`;
}

async function exportOrders() {
  if (exporting.value) return;
  exporting.value = true;
  try {
    const code = listCode.value.trim();
    const params = {
      code: code || undefined,
      status: statusFilter.value || undefined,
      start_date: startDate.value || undefined,
      end_date: endDate.value || undefined,
    };
    const blob = await adminApi.exportOrders(params);
    if (blob && blob.size) {
      const url = URL.createObjectURL(blob);
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const suffix = code ? code : 'all';
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `orders-${suffix}-${timestamp}.xlsx`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      URL.revokeObjectURL(url);
    }
  } catch (error) {
    const message = error?.message || '导出失败';
    showFeedback(message, 'error');
  } finally {
    exporting.value = false;
  }
}

onMounted(() => {
  if (typeof window !== 'undefined' && 'matchMedia' in window) {
    compactQuery = window.matchMedia('(max-width: 900px)');
    isCompact.value = compactQuery.matches;
    if (compactQuery.addEventListener) compactQuery.addEventListener('change', compactListener);
    else compactQuery.addListener(compactListener);
  }
  if (isAdminOrSuper) {
    loadList(1);
  }
});

onUnmounted(() => {
  if (compactQuery) {
    if (compactQuery.removeEventListener) compactQuery.removeEventListener('change', compactListener);
    else compactQuery.removeListener(compactListener);
    compactQuery = null;
  }
});
</script>

<style scoped>
.order-admin { display: flex; flex-direction: column; gap: 18px; }
.row { display: flex; align-items: center; gap: 10px; }

.alert-card {
  background: rgba(9, 16, 28, 0.62);
  border: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 20px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  backdrop-filter: blur(16px) saturate(1.35);
  -webkit-backdrop-filter: blur(16px) saturate(1.35);
  box-shadow: 0 22px 42px rgba(0, 0, 0, 0.32);
}

.alert {
  color: #ffe9be;
  background: rgba(255, 183, 77, 0.12);
  border: 1px solid rgba(255, 183, 77, 0.32);
  padding: 12px 14px;
  border-radius: 12px;
}

.btn,
.btn-outline,
.btn-solid,
.btn-gradient-text,
.btn-danger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  border-radius: 12px;
  padding: 0 16px;
  cursor: pointer;
  font-weight: 600;
  letter-spacing: 0.3px;
  transition: transform 180ms ease, box-shadow 220ms ease, background 220ms ease, border-color 220ms ease, color 220ms ease;
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
}

.btn {
  background: linear-gradient(135deg, rgba(22, 41, 72, 0.48), rgba(10, 24, 44, 0.42));
  border: 1px solid rgba(148, 176, 215, 0.32);
  color: #dbeafe;
}
.btn:hover {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.32), rgba(14, 32, 58, 0.48));
  border-color: rgba(148, 205, 255, 0.52);
  box-shadow: 0 16px 32px rgba(37, 99, 235, 0.28);
  color: #f8fbff;
}

.btn-outline {
  background: linear-gradient(135deg, rgba(16, 45, 88, 0.32), rgba(10, 20, 38, 0.46));
  border: 1px solid rgba(148, 205, 255, 0.38);
  color: #e1efff;
}
.btn-outline:hover:not(:disabled) {
  transform: translateY(-1px);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.38), rgba(37, 211, 164, 0.26));
  border-color: rgba(148, 205, 255, 0.6);
  box-shadow: 0 18px 36px rgba(30, 90, 180, 0.32);
  color: #0b172a;
}

.btn-solid {
  background: linear-gradient(135deg, rgba(56, 189, 248, 0.42), rgba(59, 130, 246, 0.28));
  border: 1px solid rgba(102, 212, 255, 0.45);
  color: #f0f9ff;
  box-shadow: 0 18px 38px rgba(17, 62, 140, 0.32);
}
.btn-solid:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: rgba(102, 212, 255, 0.66);
  box-shadow: 0 22px 44px rgba(17, 62, 140, 0.4);
}
.btn-solid:active:not(:disabled) { transform: translateY(0); box-shadow: 0 12px 26px rgba(17, 62, 140, 0.28); }

.btn-gradient-text {
  background: linear-gradient(135deg, rgba(39, 255, 160, 0.7), rgba(126, 243, 255, 0.68));
  border: 1px solid rgba(148, 255, 225, 0.28);
  color: #052032;
  box-shadow: 0 18px 34px rgba(20, 200, 160, 0.28);
}
.btn-gradient-text:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 22px 42px rgba(20, 200, 160, 0.36);
}

.btn-danger {
  background: linear-gradient(135deg, rgba(140, 32, 32, 0.45), rgba(75, 18, 27, 0.55));
  border: 1px solid rgba(255, 149, 149, 0.48);
  color: #ffe4e6;
}
.btn-danger:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: rgba(255, 149, 149, 0.68);
  box-shadow: 0 16px 32px rgba(120, 32, 46, 0.36);
}

.btn[disabled],
.btn-outline[disabled],
.btn-solid[disabled],
.btn-gradient-text[disabled],
.btn-danger[disabled] {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.table-card {
  background: rgba(9, 16, 28, 0.66);
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 20px;
  padding: 18px 20px;
  backdrop-filter: blur(18px) saturate(1.3);
  -webkit-backdrop-filter: blur(18px) saturate(1.3);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.32);
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 960px;
  margin: 0 auto;
}

.table-toolbar {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
}

.toolbar-title {
  font-size: 1.12rem;
  font-weight: 700;
  letter-spacing: 0.6px;
  color: #f4f8ff;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.toolbar-date-range {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.toolbar-date-range .toolbar-input {
  flex: 0 1 200px;
  width: 200px;
  min-width: 160px;
}

.toolbar-date-sep {
  color: rgba(221, 229, 248, 0.72);
  font-size: 0.9rem;
  letter-spacing: 0.2px;
}

.toolbar-clear {
  height: 36px;
  min-width: 72px;
  padding: 0 12px;
  border-radius: 10px;
  border: 1px solid rgba(148, 205, 255, 0.32);
  background: rgba(12, 22, 40, 0.48);
  color: rgba(221, 229, 248, 0.9);
  cursor: pointer;
  transition: transform 160ms ease, border-color 200ms ease, background 200ms ease;
}

.toolbar-clear:hover:not(:disabled),
.toolbar-clear:focus-visible {
  border-color: rgba(102, 212, 255, 0.6);
  background: rgba(24, 38, 60, 0.62);
  transform: translateY(-1px);
  outline: none;
}

.toolbar-clear:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none;
}

.toolbar-button-row {
  display: flex;
  align-items: stretch;
  gap: 10px;
  width: 100%;
}

.toolbar-button-row .toolbar-btn {
  flex: 1 1 0;
  min-width: 140px;
  height: 40px;
  justify-content: center;
}

.toolbar-input {
  flex: 0 1 240px;
  width: 240px;
  max-width: 320px;
  min-width: 200px;
}
.toolbar-input,
.table-card .input {
  height: 36px;
  min-height: 36px;
  border-radius: 10px;
  padding: 0 12px;
}
.toolbar-btn { min-width: 96px; }

.create-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(12, 22, 40, 0.46);
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.create-form .grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px 16px;
}

.create-actions { display: flex; justify-content: flex-end; }

.table-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.summary { color: rgba(221, 229, 248, 0.88); font-weight: 600; }
.table-buttons { display: flex; gap: 10px; flex-wrap: wrap; }

.table-wrapper {
  overflow-x: auto;
  border-radius: 16px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: rgba(7, 14, 26, 0.48);
}

.order-table { width: 100%; border-collapse: collapse; min-width: 720px; }
.order-table th,
.order-table td {
  padding: 12px 14px;
  text-align: left;
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
}
.order-table th { color: #aeb7c9; font-size: 0.92rem; letter-spacing: 0.3px; }
.order-table td { color: #f1f5ff; font-size: 0.9rem; }

.compact-list { display: grid; gap: 12px; }
.compact-card {
  background: rgba(9, 16, 28, 0.72);
  border: 1px solid rgba(148, 205, 255, 0.28);
  border-radius: 20px;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-shadow: 0 20px 40px rgba(5, 15, 30, 0.32);
  cursor: pointer;
  transition: transform 180ms ease, box-shadow 220ms ease;
}
.compact-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 28px 52px rgba(12, 32, 64, 0.38);
}
.compact-card:active { transform: translateY(0); }
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.card-title { font-size: 1.02rem; font-weight: 700; letter-spacing: 0.4px; color: #f0f6ff; }
.card-checkbox input {
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 6px;
  border: 1px solid rgba(148, 205, 255, 0.5);
  background: linear-gradient(135deg, rgba(13, 25, 44, 0.78), rgba(9, 18, 34, 0.72));
  display: inline-block;
  position: relative;
}
.card-checkbox input:checked {
  border-color: rgba(102, 212, 255, 0.7);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.65), rgba(37, 211, 164, 0.55));
}
.card-checkbox input:checked::after {
  content: '';
  position: absolute;
  inset: 4px 6px 4px 5px;
  border-right: 2px solid #0b172a;
  border-bottom: 2px solid #0b172a;
  transform: rotate(40deg);
}
.card-meta { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px; color: rgba(214, 229, 255, 0.85); font-size: 0.88rem; }
.card-actions { display: flex; gap: 10px; }

.checkbox-cell { width: 52px; }
.checkbox-cell input[type='checkbox'] {
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 6px;
  border: 1px solid rgba(148, 176, 215, 0.5);
  background: linear-gradient(135deg, rgba(13, 25, 44, 0.78), rgba(9, 18, 34, 0.72));
  position: relative;
  cursor: pointer;
  transition: border-color 200ms ease, background 200ms ease, box-shadow 200ms ease;
}
.checkbox-cell input[type='checkbox']:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.35);
}
.checkbox-cell input[type='checkbox']:checked {
  border-color: rgba(102, 212, 255, 0.7);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.65), rgba(37, 211, 164, 0.55));
  box-shadow: 0 10px 20px rgba(37, 99, 235, 0.34);
}
.checkbox-cell input[type='checkbox']:checked::after {
  content: '';
  position: absolute;
  inset: 4px 6px 4px 5px;
  border-right: 2px solid #0b172a;
  border-bottom: 2px solid #0b172a;
  transform: rotate(40deg);
}

.actions-cell { display: flex; gap: 8px; }
.empty { text-align: center; padding: 32px 0; color: rgba(199, 206, 224, 0.75); }
.status-text { color: rgba(199, 210, 228, 0.78); font-size: 0.88rem; }

.slide-fade-enter-active,
.slide-fade-leave-active { transition: opacity 240ms ease, transform 240ms ease; }
.slide-fade-enter-from,
.slide-fade-leave-to { opacity: 0; transform: translateY(-10px); }

.table-row-enter-active,
.table-row-leave-active { transition: opacity 220ms ease, transform 220ms ease; }
.table-row-enter-from,
.table-row-leave-to { opacity: 0; transform: translateY(6px); }

.modal-fade-enter-active,
.modal-fade-leave-active { transition: opacity 220ms ease; }
.modal-fade-enter-from,
.modal-fade-leave-to { opacity: 0; }

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(5, 10, 18, 0.68);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  z-index: 9999;
}

.modal-card {
  width: min(520px, 88vw);
  background: rgba(15, 20, 32, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 18px;
  padding: 24px 28px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.45);
}

.confirm-card { width: min(360px, 88vw); gap: 18px; }
.confirm-text {
  margin: 4px 0;
  color: rgba(221, 233, 255, 0.88);
  line-height: 1.6;
  letter-spacing: 0.3px;
}

.modal-title { margin: 0; font-size: 1.2rem; font-weight: 700; color: #f1f5ff; }
.modal-tip { color: rgba(204, 213, 235, 0.8); }
.modal-message { color: rgba(139, 215, 255, 0.82); }
.modal-stats { display: grid; gap: 6px; color: rgba(226, 238, 255, 0.92); }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; }

.feedback-card {
  min-width: min(360px, 90vw);
  max-width: min(420px, 92vw);
  background: rgba(12, 22, 40, 0.9);
  border-radius: 20px;
  padding: 24px 26px;
  border: 1px solid rgba(102, 212, 255, 0.35);
  display: flex;
  flex-direction: column;
  gap: 18px;
  align-items: center;
  text-align: center;
  box-shadow: 0 24px 46px rgba(0, 0, 0, 0.4);
}
.feedback-card.feedback-success { border-color: rgba(102, 212, 255, 0.45); box-shadow: 0 24px 52px rgba(17, 62, 140, 0.4); }
.feedback-card.feedback-error { border-color: rgba(255, 149, 149, 0.55); box-shadow: 0 24px 52px rgba(120, 32, 46, 0.42); }

.feedback-message { font-size: 1rem; color: #f0f5ff; letter-spacing: 0.3px; text-align: center; }

@media (max-width: 1024px) {
  .create-form .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 800px) {
  .table-card { padding: 16px 18px; }
  .toolbar-actions { flex-direction: column; align-items: flex-start; gap: 10px; }
  .toolbar-input { width: min(100%, 240px); max-width: 240px; flex: 0 0 auto; }
  .toolbar-date-range { width: auto; flex-direction: row; align-items: center; flex-wrap: wrap; gap: 8px; }
  .toolbar-date-range .toolbar-input { width: min(100%, 240px); max-width: 240px; }
  .toolbar-date-sep { display: inline-flex; align-items: center; }
  .toolbar-clear { width: 100%; }
  .toolbar-button-row { flex-direction: column; width: 100%; }
  .toolbar-button-row .toolbar-btn { min-width: 100%; width: 100%; }
  .table-wrapper { min-width: 100%; }
}

@media (max-width: 640px) {
  .table-card { padding: 14px; border-radius: 16px; }
  .create-form { padding: 14px; }
  .create-form .grid { grid-template-columns: 1fr; }
  .actions-cell { flex-direction: column; }
}
</style>
