<template>
  <section :class="['users-admin', { 'mobile-simplified': isCompact }]">
    <div class="table-card">
      <div class="table-toolbar">
        <div class="toolbar-title">用户管理</div>
        <div class="toolbar-actions">
          <input class="input toolbar-input" v-model="userQuery" placeholder="搜索用户名" />
          <select class="input toolbar-input" v-model="userRoleFilter">
            <option value="">全部角色</option>
            <option value="user">普通用户</option>
            <option value="admin">管理员</option>
            <option value="superadmin">超级管理员</option>
          </select>
          <button class="btn-solid toolbar-btn" @click="searchUsers">搜索</button>
          <button class="btn-outline toolbar-btn" type="button" @click="openCreate">新建用户</button>
        </div>
      </div>

      <div class="table-head">
        <div class="summary">{{ summaryText }}</div>
        <div class="table-buttons">
          <button class="btn-outline" type="button" @click="prevUserPage" :disabled="userPage <= 1">上一页</button>
          <button class="btn-outline" type="button" @click="nextUserPage" :disabled="userPage >= userPages">下一页</button>
          <button class="btn-danger" type="button" @click="deleteUsers" :disabled="selectedUserIds.length === 0">
            批量删除 ({{ selectedUserIds.length }})
          </button>
        </div>
      </div>

      <div class="table-wrapper" v-if="!isCompact">
        <table class="user-table">
          <thead>
            <tr>
              <th class="checkbox-cell">
                <input type="checkbox" class="checkbox" @change="toggleAllUsers" />
              </th>
              <th>用户名</th>
              <th>角色</th>
              <th>状态</th>
              <th>绑定编号</th>
              <th>创建时间</th>
              <th class="actions-cell">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td class="checkbox-cell">
                <input type="checkbox" class="checkbox" v-model="selectedUserIds" :value="user.id" />
              </td>
              <td>{{ user.username }}</td>
              <td>
                <select class="input" v-model="user.role">
                  <option value="user">user</option>
                  <option value="admin">admin</option>
                  <option value="superadmin">superadmin</option>
                </select>
              </td>
              <td>
                <select class="input" v-model="user.is_active">
                  <option :value="true">启用</option>
                  <option :value="false">停用</option>
                </select>
              </td>
              <td><input class="input" v-model="user.codesStr" placeholder="A666,2025-01" /></td>
              <td>{{ formatDateCn(user.created_at) }}</td>
              <td class="actions-cell">
                <button class="btn-outline" type="button" @click="saveUser(user)">保存</button>
              </td>
            </tr>
            <tr v-if="users.length === 0">
              <td colspan="7" class="empty">暂无用户数据</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-else class="compact-list">
        <article
          v-for="user in users"
          :key="user.id"
          class="compact-card"
          @click="openEditModal(user)"
        >
          <div class="card-header">
            <div class="card-title">{{ user.username }}</div>
            <label class="card-checkbox" @click.stop>
              <input type="checkbox" class="checkbox" v-model="selectedUserIds" :value="user.id" />
            </label>
          </div>
          <div class="card-meta">
            <span>角色：{{ user.role }}</span>
            <span>{{ user.is_active ? '启用' : '停用' }}</span>
          </div>
          <div class="card-meta">
            <span>编号：{{ user.codesStr || '—' }}</span>
          </div>
          <div class="card-meta">
            <span>创建：{{ formatDateCn(user.created_at) }}</span>
          </div>
          <div class="card-actions" @click.stop>
            <button class="btn-outline" type="button" @click="openEditModal(user)">管理</button>
          </div>
        </article>
        <div v-if="users.length === 0" class="empty">暂无用户数据</div>
      </div>

      <div class="status-text" v-if="msg">{{ msg }}</div>
    </div>

    <teleport to="body">
      <transition name="modal-fade">
        <div v-if="createState.visible" class="modal-overlay" @click.self="closeCreate">
          <div class="modal-card">
            <h3 class="modal-title">新建用户</h3>
            <div class="grid">
              <label>用户名
                <input class="input" v-model="createState.form.username" placeholder="必填" />
              </label>
              <label>密码
                <input class="input" type="password" v-model="createState.form.password" placeholder="必填" />
              </label>
              <label>角色
                <select class="input" v-model="createState.form.role">
                  <option value="user">普通用户</option>
                  <option value="admin">管理员</option>
                  <option value="superadmin">超级管理员</option>
                </select>
              </label>
              <label>绑定编号 (逗号分隔)
                <input class="input" v-model="createState.form.codesStr" placeholder="如 A666,2025-01" />
              </label>
            </div>
            <div class="modal-actions">
              <button class="btn-outline" type="button" @click="closeCreate" :disabled="createState.loading">取消</button>
              <button class="btn-gradient-text" type="button" @click="submitCreate" :disabled="createState.loading">
                {{ createState.loading ? '创建中…' : '确认创建' }}
              </button>
            </div>
          </div>
        </div>
      </transition>
    </teleport>

    <teleport to="body">
      <transition name="modal-fade">
        <div v-if="editState.visible" class="modal-overlay" @click.self="closeEditModal">
          <div class="modal-card">
            <h3 class="modal-title">管理用户</h3>
            <div class="grid">
              <label>用户名
                <input class="input" :value="editState.form.username" disabled />
              </label>
              <label>角色
                <select class="input" v-model="editState.form.role">
                  <option value="user">普通用户</option>
                  <option value="admin">管理员</option>
                  <option value="superadmin">超级管理员</option>
                </select>
              </label>
              <label>状态
                <select class="input" v-model="editState.form.is_active">
                  <option :value="true">启用</option>
                  <option :value="false">停用</option>
                </select>
              </label>
              <label>绑定编号 (逗号分隔)
                <input class="input" v-model="editState.form.codesStr" placeholder="如 A666,2025-01" />
              </label>
            </div>
            <div class="modal-actions">
              <button class="btn-outline" type="button" @click="closeEditModal" :disabled="editState.loading">取消</button>
              <button class="btn-gradient-text" type="button" @click="submitEditModal" :disabled="editState.loading">
                {{ editState.loading ? '保存中…' : '保存修改' }}
              </button>
            </div>
          </div>
        </div>
      </transition>
    </teleport>
  </section>
</template>

<script setup>
import { reactive, ref, onMounted, onUnmounted, computed } from 'vue';
import { adminApi } from '../../composables/useAdminApi';
import { formatDateCn } from '../../utils/date';
import { useNotifier } from '../../composables/useNotifier';

const users = ref([]);
const userQuery = ref('');
const userRoleFilter = ref('');
const selectedUserIds = ref([]);
const userPage = ref(1);
const userPages = ref(1);
const userPageSize = 10;
const userTotal = ref(0);
const msg = ref('');
const isCompact = ref(false);
let compactQuery = null;
const compactListener = event => {
  isCompact.value = event.matches;
};

const createState = reactive({
  visible: false,
  loading: false,
  form: { username: '', password: '', role: 'user', codesStr: '' },
});

const editState = reactive({
  visible: false,
  loading: false,
  form: {
    id: 0,
    username: '',
    role: 'user',
    is_active: true,
    codesStr: '',
  },
});

const { showNotice } = useNotifier();

const summaryText = computed(() => {
  if (!userTotal.value) {
    return `当前第 ${userPage.value} / ${userPages.value} 页，${users.value.length} 条显示`;
  }
  return `总计 ${userTotal.value} 条 · 第 ${userPage.value} / ${userPages.value} 页`;
});

async function loadUsers(page = userPage.value) {
  try {
    const data = await adminApi.usersList({ q: userQuery.value, role: userRoleFilter.value, page, page_size: userPageSize });
    users.value = (data.items || []).map(u => ({
      ...u,
      codesStr: (u.codes || []).join(','),
      is_active: !!u.is_active,
    }));
    userPages.value = data.pages || 1;
    userPage.value = data.page || page;
    userTotal.value = data.total || users.value.length;
    selectedUserIds.value = [];
    msg.value = '';
  } catch (error) {
    msg.value = error?.message || '加载失败';
  }
}

function searchUsers() {
  userPage.value = 1;
  loadUsers(1);
}

function prevUserPage() {
  if (userPage.value > 1) loadUsers(userPage.value - 1);
}

function nextUserPage() {
  if (userPage.value < userPages.value) loadUsers(userPage.value + 1);
}

function toggleAllUsers(event) {
  const checked = !!event?.target?.checked;
  selectedUserIds.value = checked ? users.value.map(u => u.id) : [];
}

function openEditModal(user) {
  editState.form.id = user.id;
  editState.form.username = user.username;
  editState.form.role = user.role;
  editState.form.is_active = !!user.is_active;
  editState.form.codesStr = user.codesStr || '';
  editState.visible = true;
}

function closeEditModal() {
  if (editState.loading) return;
  editState.visible = false;
}

async function submitEditModal() {
  editState.loading = true;
  try {
    const codes = (editState.form.codesStr || '').split(',').map(s => s.trim()).filter(Boolean);
    await adminApi.usersUpdate(editState.form.id, {
      role: editState.form.role,
      is_active: !!editState.form.is_active,
      codes,
    });
    showNotice({ type: 'success', message: '用户已更新' });
    editState.visible = false;
    await loadUsers(userPage.value);
  } catch (error) {
    msg.value = error?.message || '保存失败';
  } finally {
    editState.loading = false;
  }
}

function resetCreateForm() {
  createState.form.username = '';
  createState.form.password = '';
  createState.form.role = 'user';
  createState.form.codesStr = '';
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
  if (!createState.form.username.trim() || !createState.form.password.trim()) {
    msg.value = '请输入用户名与密码';
    return;
  }
  createState.loading = true;
  try {
    const codes = createState.form.codesStr.split(',').map(s => s.trim()).filter(Boolean);
    await adminApi.usersCreate({
      username: createState.form.username.trim(),
      password: createState.form.password,
      role: createState.form.role,
      is_active: true,
      codes,
    });
    showNotice({ type: 'success', message: '用户已创建' });
    createState.visible = false;
    resetCreateForm();
    await loadUsers(userPage.value);
  } catch (error) {
    msg.value = error?.message || '创建失败';
  } finally {
    createState.loading = false;
  }
}

async function saveUser(user) {
  try {
    const codes = (user.codesStr || '').split(',').map(s => s.trim()).filter(Boolean);
    await adminApi.usersUpdate(user.id, { role: user.role, is_active: !!user.is_active, codes });
    showNotice({ type: 'success', message: '用户已更新' });
  } catch (error) {
    msg.value = error?.message || '保存失败';
  }
}

async function deleteUsers() {
  if (selectedUserIds.value.length === 0) return;
  if (!window.confirm(`确认批量删除 ${selectedUserIds.value.length} 个用户？`)) return;
  try {
    await adminApi.usersDeleteBulk([...selectedUserIds.value]);
    showNotice({ type: 'success', message: '已删除所选用户' });
    await loadUsers(userPage.value);
  } catch (error) {
    msg.value = error?.message || '删除失败';
  }
}

onMounted(() => {
  if (typeof window !== 'undefined' && 'matchMedia' in window) {
    compactQuery = window.matchMedia('(max-width: 900px)');
    isCompact.value = compactQuery.matches;
    if (compactQuery.addEventListener) compactQuery.addEventListener('change', compactListener);
    else compactQuery.addListener(compactListener);
  }
  loadUsers();
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
.users-admin { display: flex; flex-direction: column; gap: 18px; }
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
}
.users-admin .table-card {
  background: none;
  border: none;
  box-shadow: none;
  padding: 0;
  gap: 14px;
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
.toolbar-input {
  flex: 0 1 240px;
  width: 240px;
  max-width: 320px;
  min-width: 160px;
}
.toolbar-input,
.table-card .input {
  height: 36px;
  min-height: 36px;
  border-radius: 10px;
  padding: 0 12px;
}
.toolbar-btn { min-width: 110px; }

.table-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.summary { color: rgba(221, 229, 248, 0.88); font-weight: 600; }
.table-buttons { display: flex; gap: 10px; flex-wrap: wrap; }

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
.btn[disabled], .btn-outline[disabled], .btn-solid[disabled], .btn-danger[disabled] {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.table-wrapper { overflow-x: auto; border-radius: 16px; border: 1px solid rgba(148, 163, 184, 0.16); background: rgba(7, 14, 26, 0.48); }
.user-table { width: 100%; border-collapse: collapse; min-width: 720px; }
.user-table th, .user-table td { padding: 12px 14px; text-align: left; border-bottom: 1px solid rgba(148, 163, 184, 0.16); }
.user-table th { color: #aeb7c9; font-size: 0.92rem; letter-spacing: 0.3px; }
.user-table td { color: #f1f5ff; font-size: 0.9rem; }
.compact-list { display: grid; gap: 12px; }
.compact-card {
  background: rgba(9, 16, 28, 0.72);
  border: 1px solid rgba(148, 205, 255, 0.28);
  border-radius: 18px;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-shadow: 0 18px 40px rgba(5, 15, 30, 0.34);
  cursor: pointer;
  transition: transform 180ms ease, box-shadow 220ms ease;
}
.compact-card:hover { transform: translateY(-2px); box-shadow: 0 26px 52px rgba(12, 32, 64, 0.38); }
.compact-card:active { transform: translateY(0); }
.card-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.card-title { font-size: 1.02rem; font-weight: 700; letter-spacing: 0.4px; color: #f2f7ff; }
.card-checkbox .checkbox { margin: 0; }
.card-meta { display: flex; flex-wrap: wrap; gap: 12px; color: rgba(214, 229, 255, 0.85); font-size: 0.88rem; }
.card-actions { display: flex; gap: 10px; justify-content: flex-end; }
.checkbox-cell { width: 52px; }
.checkbox {
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
.checkbox:focus-visible { outline: none; box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.35); }
.checkbox:checked {
  border-color: rgba(102, 212, 255, 0.7);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.65), rgba(37, 211, 164, 0.55));
  box-shadow: 0 10px 20px rgba(37, 99, 235, 0.34);
}
.checkbox:checked::after {
  content: '';
  position: absolute;
  inset: 4px 6px 4px 5px;
  border-right: 2px solid #0b172a;
  border-bottom: 2px solid #0b172a;
  transform: rotate(40deg);
}
.actions-cell { display: flex; gap: 8px; }
.empty { text-align: center; padding: 32px 0; color: rgba(199, 206, 224, 0.75); }

.muted { color: rgba(204, 213, 235, 0.75); }
.status-text { color: rgba(199, 210, 228, 0.78); font-size: 0.88rem; }

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
  width: min(480px, 88vw);
  background: rgba(15, 20, 32, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 18px;
  padding: 24px 28px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.45);
}
.modal-title { margin: 0; font-size: 1.2rem; font-weight: 700; color: #f1f5ff; }
.modal-card .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px 16px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 12px; }

@media (max-width: 1024px) {
  .modal-card .grid { grid-template-columns: 1fr; }
  .toolbar-actions { flex-direction: column; align-items: stretch; }
  .toolbar-input { width: 100%; max-width: none; flex: 1 1 auto; }
  .table-buttons { width: 100%; justify-content: flex-start; }
}

@media (max-width: 640px) {
  .table-card { padding: 18px; }
  .modal-card { padding: 20px 22px; }
  .user-table { min-width: 100%; }
  .toolbar-btn { width: 100%; }
  .table-buttons { flex-direction: column; align-items: stretch; width: 100%; }
}
</style>
