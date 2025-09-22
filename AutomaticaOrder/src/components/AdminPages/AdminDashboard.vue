<template>
  <section>
    <div class="row" style="justify-content: space-between; align-items:center; margin-bottom:12px;">
      <h2>订单后台管理</h2>
      <button class="btn" @click="logout">退出</button>
    </div>

    <div class="stack">
      <!-- 用户管理（仅超级管理员） -->
      <GlassSurface v-if="adminRole==='superadmin'" class-name="card" :width="'100%'" :height="'auto'" :background-opacity="0.12" :blur="8" :saturation="1.4" simple :center-content="false" :content-padding="12">
        <h3>用户管理</h3>
        <div class="row" style="gap:8px; margin-bottom:8px;">
          <input class="input" v-model="userQuery" placeholder="搜索用户名" />
          <select class="input" v-model="userRoleFilter"><option value="">全部角色</option><option value="user">普通用户</option><option value="admin">管理员</option><option value="superadmin">超级管理员</option></select>
          <button class="btn" @click="() => { userPage=1; loadUsers(); }">搜索</button>
          <button class="btn danger" :disabled="selectedUserIds.length===0" @click="deleteUsers">批量删除 ({{ selectedUserIds.length }})</button>
        </div>
        <div class="row" style="gap:8px; align-items:flex-end; margin-bottom:8px;">
          <label style="display:grid; gap:4px;">用户名<input class="input" v-model="newUser.username" /></label>
          <label style="display:grid; gap:4px;">密码<input class="input" type="password" v-model="newUser.password" /></label>
          <label style="display:grid; gap:4px;">角色<select class="input" v-model="newUser.role"><option value="user">普通用户</option><option value="admin">管理员</option><option value="superadmin">超级管理员</option></select></label>
          <label style="display:grid; gap:4px;">绑定编号(逗号分隔)<input class="input" v-model="newUser.codesStr" placeholder="如 A666,2025-01" /></label>
          <button class="btn" @click="createUser">创建用户</button>
        </div>
        <div style="overflow:auto;">
          <table>
            <thead><tr>
              <th><input type="checkbox" @change="toggleAllUsers($event)"></th>
              <th>用户名</th><th>角色</th><th>状态</th><th>编号</th><th>创建时间</th><th>操作</th>
            </tr></thead>
            <tbody>
              <tr v-for="u in users" :key="u.id">
                <td><input type="checkbox" v-model="selectedUserIds" :value="u.id"></td>
                <td>{{ u.username }}</td>
                <td>
                  <select class="input" v-model="u.role"><option value="user">user</option><option value="admin">admin</option><option value="superadmin">superadmin</option></select>
                </td>
                <td>
                  <select class="input" v-model="u.is_active"><option :value="true">启用</option><option :value="false">停用</option></select>
                </td>
                <td><input class="input" v-model="u.codesStr" placeholder="A666,2025-01" /></td>
                <td>{{ u.created_at }}</td>
                <td><button class="btn" @click="saveUser(u)">保存</button></td>
              </tr>
            </tbody>
          </table>
          <div class="row" style="gap:6px; justify-content:flex-end; margin-top:8px;">
            <button class="btn" @click="prevUserPage" :disabled="userPage<=1">上一页</button>
            <span class="muted">第 {{ userPage }} / {{ userPages }} 页</span>
            <button class="btn" @click="nextUserPage" :disabled="userPage>=userPages">下一页</button>
          </div>
        </div>
      </GlassSurface>
      <GlassSurface class-name="card" :width="'100%'" :height="'auto'" :background-opacity="0.12" :blur="8" :saturation="1.4" simple :center-content="false" :content-padding="12">
        <h3>新建订单</h3>
        <div class="grid-2">
          <label>订单号 <input class="input" v-model="createForm.order_no" placeholder="必填" /></label>
          <label>所属编号 <input class="input" v-model="createForm.group_code" /></label>
          <label>重量(kg) <input class="input" type="number" step="0.01" v-model="createForm.weight_kg" /></label>
          <label>运费 <input class="input" type="number" step="0.01" v-model="createForm.shipping_fee" /></label>
          <label>状态
            <select class="input" v-model="createForm.status">
              <option v-for="s in STATUSES" :key="s" :value="s">{{ s }}</option>
            </select>
          </label>
          <label>是否打木架
            <select class="input" v-model="createForm.wooden_crate">
              <option :value="null">未设置</option>
              <option :value="true">是</option>
              <option :value="false">否</option>
            </select>
          </label>
        </div>
        <div class="row">
          <button class="btn" @click="createOrder" :disabled="creating">{{ creating ? '创建中...' : '创建' }}</button>
        </div>
      </GlassSurface>

      <GlassSurface class-name="card" :width="'100%'" :height="'auto'" :background-opacity="0.12" :blur="8" :saturation="1.4" simple :center-content="false" :content-padding="12">
        <h3>编辑 / 删除订单</h3>
        <div class="row">
          <input class="input" v-model="editOrderNo" placeholder="订单号" />
          <button class="btn" @click="loadByNo">加载</button>
        </div>
        <div v-if="editing" class="grid-2" style="margin-top:8px;">
          <label>所属编号 <input class="input" v-model="editing.group_code" /></label>
          <label>重量(kg) <input class="input" type="number" step="0.01" v-model="editing.weight_kg" /></label>
          <label>状态
            <select class="input" v-model="editing.status">
              <option v-for="s in STATUSES" :key="s" :value="s">{{ s }}</option>
            </select>
          </label>
          <label>运费 <input class="input" type="number" step="0.01" v-model="editing.shipping_fee" /></label>
          <label>是否打木架
            <select class="input" v-model="editing.wooden_crate">
              <option :value="null">未设置</option>
              <option :value="true">是</option>
              <option :value="false">否</option>
            </select>
          </label>
        </div>
        <div v-if="editing" class="row" style="gap:8px; margin-top:6px;">
          <button class="btn" @click="saveEdit">保存</button>
          <button class="btn danger" @click="deleteOrder">删除</button>
        </div>
      </GlassSurface>

      <GlassSurface class-name="card" :width="'100%'" :height="'auto'" :background-opacity="0.12" :blur="8" :saturation="1.4" simple :center-content="false" :content-padding="12">
        <h3>批量导入（.xlsx）</h3>
        <input type="file" accept=".xlsx" @change="onImport" :disabled="uploading" />
      </GlassSurface>

      <GlassSurface class-name="card" :width="'100%'" :height="'auto'" :background-opacity="0.12" :blur="8" :saturation="1.4" simple :center-content="false" :content-padding="12">
        <h3>查询列表（分页/批量删除）</h3>
        <div class="row">
          <input class="input" v-model="listCode" placeholder="编号，如 2025-01 或 A" />
          <button class="btn" @click="() => { page=1; queryList(); }">查询</button>
        </div>
        <div style="overflow:auto; margin-top:8px;">
          <table>
            <thead>
              <tr>
                <th><input type="checkbox" @change="toggleAll($event)"></th>
                <th>订单号</th><th>编号</th><th>重量</th><th>状态</th><th>更新</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="o in list" :key="o.id">
                <td><input type="checkbox" v-model="selectedNos" :value="o.order_no"></td>
                <td>{{ o.order_no }}</td>
                <td>{{ o.group_code || '' }}</td>
                <td>{{ (o.weight_kg ?? 0).toFixed(2) }} kg</td>
                <td>{{ o.status }}</td>
                <td>{{ o.updated_at }}</td>
              </tr>
            </tbody>
          </table>
          <div class="row" style="justify-content: space-between; margin-top:8px;">
            <div class="muted" style="font-size:12px;">合计：件数 {{ totals.count || 0 }} | 重量 {{ (totals.total_weight || 0).toFixed(2) }} kg | 运费 {{ (totals.total_shipping_fee || 0).toFixed(2) }}</div>
            <div class="row" style="gap:6px;">
              <button class="btn" @click="prevPage" :disabled="page<=1">上一页</button>
              <span class="muted">第 {{ page }} / {{ pages }} 页</span>
              <button class="btn" @click="nextPage" :disabled="page>=pages">下一页</button>
              <button class="btn danger" @click="bulkDelete" :disabled="selectedNos.length===0">批量删除 ({{ selectedNos.length }})</button>
            </div>
          </div>
        </div>
      </GlassSurface>

      <GlassSurface class-name="card" :width="'100%'" :height="'auto'" :background-opacity="0.12" :blur="8" :saturation="1.4" simple :center-content="false" :content-padding="12">
        <h3>公告栏管理</h3>
        <div class="row" style="gap:8px; align-items:center; margin-bottom:8px;">
          <label style="display:grid; gap:6px; width:100%;">标题
            <input class="input" v-model="bulletinTitle" placeholder="如：重要通知" />
          </label>
          <button class="btn" @click="saveBulletin">保存公告</button>
        </div>
        <div class="row" style="gap:8px; align-items:flex-start;">
          <textarea class="input" style="width:100%; min-height:160px;" v-model="bulletinHtml" @input="bulletinPreview = sanitizeHtml(bulletinHtml)" placeholder="支持 HTML 富文本与图片 <img> 标签"></textarea>
        </div>
        <div class="subtitle tight" style="margin-top:8px;">预览</div>
        <div style="background:#0b0f16; border:1px solid #182031; border-radius:8px; padding:10px; min-height:40px;" v-html="bulletinPreview"></div>
      </GlassSurface>

      <GlassSurface class-name="card" :width="'100%'" :height="'auto'" :background-opacity="0.12" :blur="8" :saturation="1.4" simple :center-content="false" :content-padding="12">
        <h3>公告历史</h3>
        <div style="overflow:auto;">
          <table>
            <thead><tr><th>ID</th><th>标题</th><th>时间</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="it in bulletinHistory" :key="it.id">
                <td>{{ it.id }}</td>
                <td>{{ it.title || '（无标题）' }}</td>
                <td>{{ it.created_at }}</td>
                <td>
                  <button class="btn" @click="loadHistoryEntry(it.id)">载入到编辑器</button>
                  <button class="btn" @click="confirmRevert(it.id)">恢复为当前</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </GlassSurface>

      <div class="muted">{{ msg }}</div>
    </div>
  </section>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import GlassSurface from '../vue_bits/Components/GlassSurface/GlassSurface.vue';
import { adminApi } from '../../composables/useAdminApi';
import { getRole } from '../../composables/useAdminApi';
import { STATUSES } from '../../composables/useOrders';
import { clearToken } from '../../composables/useAdminApi';

const msg = ref('');
const adminRole = getRole() || '';

// Create
const createForm = reactive({ order_no: '', group_code: '', weight_kg: '', shipping_fee: '', status: STATUSES[0], wooden_crate: null });
const creating = ref(false);
async function createOrder(){
  if (!createForm.order_no) { msg.value = '请填写订单号'; return; }
  creating.value = true; msg.value = '创建中...';
  try {
    const payload = {
      order_no: createForm.order_no.trim(),
      group_code: createForm.group_code || null,
      weight_kg: createForm.weight_kg !== '' ? parseFloat(createForm.weight_kg) : null,
      shipping_fee: createForm.shipping_fee !== '' ? parseFloat(createForm.shipping_fee) : null,
      status: createForm.status,
      wooden_crate: createForm.wooden_crate,
    };
    await adminApi.createOrder(payload);
    msg.value = '创建成功';
    createForm.order_no = ''; createForm.group_code = ''; createForm.weight_kg = ''; createForm.shipping_fee=''; createForm.status = STATUSES[0]; createForm.wooden_crate = null;
  } catch(e) { msg.value = e.message; }
  finally { creating.value = false; }
}

// Edit/Delete
const editOrderNo = ref('');
const editing = ref(null);
async function loadByNo(){
  if (!editOrderNo.value) { msg.value = '请输入订单号'; return; }
  msg.value = '加载中...';
  try {
    const d = await adminApi.getOrder(editOrderNo.value);
    editing.value = {
      order_no: d.order_no,
      group_code: d.group_code || '',
      weight_kg: d.weight_kg ?? '',
      shipping_fee: d.shipping_fee ?? '',
      status: d.status,
      wooden_crate: d.wooden_crate ?? null,
    };
    msg.value = '';
  } catch(e) { msg.value = e.message; editing.value = null; }
}

async function saveEdit(){
  if (!editing.value) return;
  msg.value = '保存中...';
  try {
    const payload = {
      group_code: editing.value.group_code || null,
      weight_kg: editing.value.weight_kg !== '' ? parseFloat(editing.value.weight_kg) : null,
      shipping_fee: editing.value.shipping_fee !== '' ? parseFloat(editing.value.shipping_fee) : null,
      status: editing.value.status,
      wooden_crate: editing.value.wooden_crate,
    };
    await adminApi.updateOrder(editing.value.order_no, payload);
    msg.value = '保存成功';
  } catch(e) { msg.value = e.message; }
}

async function deleteOrder(){
  if (!editing.value) return;
  if (!confirm('确认删除该订单？')) return;
  msg.value = '删除中...';
  try { await adminApi.deleteOrder(editing.value.order_no); editing.value = null; msg.value = '已删除'; }
  catch(e){ msg.value = e.message; }
}

// Import
const uploading = ref(false);
async function onImport(ev){
  const f = ev.target.files && ev.target.files[0];
  if (!f) return;
  uploading.value = true; msg.value = '上传中...';
  try { await adminApi.importExcel(f); msg.value='导入成功'; }
  catch(e){ msg.value = e.message; }
  finally { uploading.value = false; ev.target.value=''; }
}

// List
const listCode = ref('');
const list = ref([]);
const totals = ref({});
let page = 1; let pages = 1; const pageSize = 20;
const selectedNos = ref([]);
async function queryList(){
  if (!listCode.value) { msg.value = '请输入编号'; return; }
  msg.value = '查询中...';
  try {
    const data = await adminApi.listByCode(listCode.value, { page, page_size: pageSize });
    list.value = data.orders || []; totals.value = data.totals || {}; pages = data.pages || 1; page = data.page || 1; selectedNos.value = [];
    msg.value = '';
  } catch(e) { msg.value = e.message; }
}

function prevPage(){ if (page>1){ page--; queryList(); } }
function nextPage(){ if (page<pages){ page++; queryList(); } }
function toggleAll(ev){ const checked = !!ev.target.checked; selectedNos.value = checked ? list.value.map(x=>x.order_no) : []; }
async function bulkDelete(){ if (selectedNos.value.length===0) return; if (!confirm(`确认批量删除 ${selectedNos.value.length} 条订单？`)) return; msg.value='删除中...'; try { await adminApi.deleteOrdersBulk(selectedNos.value); msg.value='已删除'; await queryList(); } catch(e){ msg.value = e.message; } }

// Users (superadmin only)
const users = ref([]);
const userQuery = ref('');
const userRoleFilter = ref('');
const selectedUserIds = ref([]);
const newUser = reactive({ username: '', password: '', role: 'user', codesStr: '' });
let userPage = 1; let userPages = 1; const userPageSize = 10;

async function loadUsers(){
  try {
    const data = await adminApi.usersList({ q: userQuery.value, role: userRoleFilter.value, page: userPage, page_size: userPageSize });
    users.value = (data.items || []).map(u => ({ ...u, codesStr: (u.codes || []).join(',') }));
    userPages = data.pages || 1; userPage = data.page || 1; selectedUserIds.value = [];
  } catch(e) { /* ignore */ }
}
function prevUserPage(){ if (userPage>1){ userPage--; loadUsers(); } }
function nextUserPage(){ if (userPage<userPages){ userPage++; loadUsers(); } }
function toggleAllUsers(ev){ const checked = !!ev.target.checked; selectedUserIds.value = checked ? users.value.map(x=>x.id) : []; }
async function createUser(){
  if (!newUser.username || !newUser.password) { msg.value = '请输入用户名与密码'; return; }
  try {
    await adminApi.usersCreate({ username: newUser.username, password: newUser.password, role: newUser.role, is_active: true, codes: (newUser.codesStr||'').split(',').map(s=>s.trim()).filter(Boolean) });
    newUser.username=''; newUser.password=''; newUser.role='user'; newUser.codesStr='';
    await loadUsers();
  } catch(e) { msg.value = e.message; }
}
async function saveUser(u){
  try {
    await adminApi.usersUpdate(u.id, { role: u.role, is_active: !!u.is_active, codes: (u.codesStr||'').split(',').map(s=>s.trim()).filter(Boolean) });
    msg.value = '已保存';
  } catch(e) { msg.value = e.message; }
}
async function deleteUsers(){ if (selectedUserIds.value.length===0) return; if(!confirm(`确认批量删除 ${selectedUserIds.value.length} 个用户？`)) return; try { await adminApi.usersDeleteBulk(selectedUserIds.value); await loadUsers(); } catch(e) { msg.value = e.message; } }

function logout(){
  clearToken();
  try { window.location.href = '/'; } catch {}
}

// Bulletin
const bulletinTitle = ref('');
const bulletinHtml = ref('');
const bulletinPreview = ref('');
const bulletinHistory = ref([]);
function sanitizeHtml(html){
  try {
    const tmp = document.createElement('div');
    tmp.innerHTML = html || '';
    tmp.querySelectorAll('script').forEach(n=>n.remove());
    return tmp.innerHTML;
  } catch { return html || ''; }
}
async function loadBulletin(){
  try {
    const d = await adminApi.getAnnouncement();
    bulletinTitle.value = (d && d.title) || '公告栏';
    bulletinHtml.value = (d && d.html) || '';
    bulletinPreview.value = sanitizeHtml(bulletinHtml.value);
    const h = await adminApi.getAnnouncementHistory(20);
    bulletinHistory.value = (h && h.items) || [];
  } catch(e){ /* ignore */ }
}
async function saveBulletin(){
  msg.value = '保存公告中...';
  try { await adminApi.saveAnnouncement({ title: bulletinTitle.value, html: bulletinHtml.value }); msg.value = '公告已保存'; }
  catch(e){ msg.value = e.message; }
  finally { await loadBulletin(); }
}

function loadHistoryEntry(id){
  const it = (bulletinHistory.value || []).find(x=>x.id===id);
  if (!it) return;
  bulletinTitle.value = it.title || '公告栏';
  bulletinHtml.value = it.html || '';
  bulletinPreview.value = sanitizeHtml(bulletinHtml.value);
}

async function confirmRevert(id){
  if (!confirm('确认将此历史版本恢复为当前公告？')) return;
  msg.value = '恢复中...';
  try { await adminApi.revertAnnouncement(id); msg.value = '已恢复，当前公告为所选版本'; }
  catch(e){ msg.value = e.message; }
  finally { await loadBulletin(); }
}

onMounted(() => { loadBulletin(); });
// If superadmin, load users on mount
onMounted(() => { if (adminRole==='superadmin') loadUsers(); });
</script>

<style scoped>
.grid-2 { display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.btn { background:#1a1e27; border:1px solid #232736; color:#e6e7eb; padding:8px 12px; border-radius:10px; cursor:pointer; }
.btn.danger { background:#35181b; border-color:#5b1f25; color:#ffb4c0; }
table { width: 100%; border-collapse: collapse; }
thead th { text-align: left; font-weight: 600; color: #aab0bd; padding: 6px 8px; border-bottom: 1px solid rgba(255,255,255,0.06); }
tbody td { padding: 6px 8px; border-bottom: 1px solid rgba(255,255,255,0.04); }
</style>
