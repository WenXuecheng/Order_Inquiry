<template>
  <section>
    <div class="row" style="justify-content: space-between; align-items:center; margin-bottom:12px;">
      <div class="title-wrap"><span class="title-fallback">订单后台管理</span></div>
      <button class="btn" @click="logout">退出</button>
    </div>

    <div class="stack">
      <!-- 权限不足提示（非 admin/superadmin） -->
      <GlassSurface v-if="!isAdminOrSuper" class-name="card" :width="'100%'" :height="'auto'" :background-opacity="0.12" :blur="8" :saturation="1.4" simple :center-content="false" :content-padding="12">
        <div class="alert403">无权限：当前账号无权访问后台功能，请联系管理员。</div>
        <div class="row" style="margin-top:8px;"><a class="btn" href="/">返回首页</a></div>
      </GlassSurface>
      <GlassSurface v-if="false && isAdminOrSuper" class-name="card" :width="'100%'" :height="'auto'" :background-opacity="0.12" :blur="8" :saturation="1.4" simple :center-content="false" :content-padding="12">
        <div class="title-wrap"><span class="title-fallback">新建订单</span></div>
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
          <button class="btn-gradient-text" @click="createOrder" :disabled="creating">{{ creating ? '创建中...' : '创建' }}</button>
        </div>
      </GlassSurface>

      <GlassSurface v-if="false && isAdminOrSuper" class-name="card" :width="'100%'" :height="'auto'" :background-opacity="0.12" :blur="8" :saturation="1.4" simple :center-content="false" :content-padding="12">
        <div class="title-wrap"><span class="title-fallback">编辑 / 删除订单</span></div>
        <div class="row">
          <input class="input" v-model="editOrderNo" placeholder="订单号" />
          <button class="btn-gradient-text" @click="loadByNo">加载</button>
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
          <button class="btn-gradient-text" @click="saveEdit">保存</button>
          <button class="btn danger" @click="deleteOrder">删除</button>
        </div>
      </GlassSurface>

      <GlassSurface v-if="isAdminOrSuper" class-name="card" :width="'100%'" :height="'auto'" :background-opacity="0.12" :blur="8" :saturation="1.4" simple :center-content="false" :content-padding="12">
        <h3>批量导入（.xlsx）</h3>
        <input type="file" accept=".xlsx" @change="onImport" :disabled="uploading" />
      </GlassSurface>

      <GlassSurface v-if="isAdminOrSuper" class-name="card" :width="'100%'" :height="'auto'" :background-opacity="0.12" :blur="8" :saturation="1.4" simple :center-content="false" :content-padding="12">
        <div class="title-wrap"><span class="title-fallback">订单列表</span></div>
        <div class="row">
          <input class="input" v-model="listCode" placeholder="筛选编号，如 2025-01 或 A（留空=全部）" />
          <button class="btn-gradient-text" @click="() => { page=1; queryList(); }">查询</button>
          <button class="btn btn-outline" @click="toggleNewForm">{{ showCreate ? '收起新建' : '新建订单' }}</button>
          <label class="btn btn-outline" style="cursor:pointer;">
            批量导入
            <input type="file" accept=".xlsx" @change="importExcel" :disabled="uploading" style="display:none;" />
          </label>
          <button class="btn danger" @click="bulkDelete" :disabled="selectedNos.length===0">批量删除 ({{ selectedNos.length }})</button>
        </div>
        <div v-if="showCreate" class="grid-2" style="margin-top:8px;">
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
          <div><button class="btn-gradient-text" @click="createOrder" :disabled="creating">{{ creating ? '创建中...' : '创建' }}</button></div>
        </div>
        <!-- 编辑表单 -->
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
          <div class="row" style="gap:8px;">
            <button class="btn-gradient-text" @click="saveEdit">保存</button>
            <button class="btn" @click="editing=null">取消</button>
          </div>
        </div>
        <div style="overflow:auto; margin-top:8px;">
          <table>
            <thead>
              <tr>
                <th><input type="checkbox" @change="toggleAll($event)"></th>
                <th>订单号</th><th>编号</th><th>重量</th><th>状态</th><th>更新</th><th>操作</th>
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
                <td>
                  <button class="btn btn-outline" @click="startEdit(o)">编辑</button>
                  <button class="btn danger" @click="deleteOne(o)">删除</button>
                </td>
              </tr>
            </tbody>
          </table>
            <div class="row" style="justify-content: space-between; margin-top:8px;">
              <div class="muted" style="font-size:12px;">合计：件数 {{ totals.count || 0 }} | 重量 {{ (totals.total_weight || 0).toFixed(2) }} kg | 运费 {{ (totals.total_shipping_fee || 0).toFixed(2) }}</div>
              <div class="row" style="gap:6px;">
              <button class="btn btn-outline" @click="prevPage" :disabled="page<=1">上一页</button>
              <span class="muted">第 {{ page }} / {{ pages }} 页</span>
              <button class="btn btn-outline" @click="nextPage" :disabled="page>=pages">下一页</button>
              <button class="btn danger" @click="bulkDelete" :disabled="selectedNos.length===0">批量删除 ({{ selectedNos.length }})</button>
              </div>
            </div>
        </div>
      </GlassSurface>

      <GlassSurface class-name="card" :width="'100%'" :height="'auto'" :background-opacity="0.12" :blur="8" :saturation="1.4" simple :center-content="false" :content-padding="12">
        <div class="title-wrap"><span class="title-fallback">公告栏管理</span></div>
        <div class="row" style="gap:8px; align-items:center; margin-bottom:8px;">
          <label style="display:grid; gap:6px; width:100%;">标题
            <input class="input" v-model="bulletinTitle" placeholder="如：重要通知" />
          </label>
          <button class="btn-gradient-text" @click="saveBulletin">保存公告</button>
          <button class="btn btn-outline" @click="showHistory = !showHistory">{{ showHistory ? '收起历史' : '历史版本' }}</button>
        </div>
        <div class="row" style="gap:8px; align-items:flex-start;">
          <textarea class="input" style="width:100%; min-height:160px;" v-model="bulletinHtml" @input="bulletinPreview = sanitizeHtml(bulletinHtml)" placeholder="支持 HTML 富文本与图片 <img> 标签"></textarea>
        </div>
        <div class="subtitle tight" style="margin-top:8px;">预览</div>
        <div style="background:#0b0f16; border:1px solid #182031; border-radius:8px; padding:10px; min-height:40px;" v-html="bulletinPreview"></div>
        <div v-if="showHistory" style="margin-top:12px;">
          <div class="subtitle tight" style="margin-bottom:6px;">历史版本</div>
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
                    <button class="btn-gradient-text" @click="confirmRevert(it.id)">恢复为当前</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
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
const isSuper = adminRole === 'superadmin';
const isAdminOrSuper = adminRole === 'admin' || adminRole === 'superadmin';

function friendlyError(e){
  const t = (e && (e.message || e)) || '';
  if (String(t).includes('无权限') || String(t).includes('403')) return '无权限：您的角色不允许进行此操作';
  if (String(t).includes('未授权') || String(t).includes('401')) return '登录失效或未登录，请重新登录';
  return t;
}

// Create
const createForm = reactive({ order_no: '', group_code: '', weight_kg: '', shipping_fee: '', status: STATUSES[0], wooden_crate: null });
const creating = ref(false);
const showCreate = ref(false);
function toggleNewForm(){ showCreate.value = !showCreate.value; }
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
  } catch(e) { msg.value = friendlyError(e); }
  finally { creating.value = false; }
}

// Edit/Delete
const editOrderNo = ref('');
const editing = ref(null);
function startEdit(o){
  editing.value = {
    order_no: o.order_no,
    group_code: o.group_code || '',
    weight_kg: o.weight_kg ?? '',
    shipping_fee: o.shipping_fee ?? '',
    status: o.status,
    wooden_crate: o.wooden_crate ?? null,
  };
  window.scrollTo({ top: 0, behavior: 'smooth' });
}
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
  } catch(e) { msg.value = friendlyError(e); editing.value = null; }
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
  } catch(e) { msg.value = friendlyError(e); }
}

async function deleteOrder(){
  if (!editing.value) return;
  if (!confirm('确认删除该订单？')) return;
  msg.value = '删除中...';
  try { await adminApi.deleteOrder(editing.value.order_no); editing.value = null; msg.value = '已删除'; }
  catch(e){ msg.value = friendlyError(e); }
}

async function deleteOne(o){
  if (!o || !o.order_no) return;
  if (!confirm(`确认删除订单 ${o.order_no} ？`)) return;
  msg.value = '删除中...';
  try { await adminApi.deleteOrder(o.order_no); msg.value = '已删除'; await queryList(); }
  catch(e){ msg.value = friendlyError(e); }
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
  msg.value = '查询中...';
  try {
    const code = (listCode.value || '').trim();
    const data = await adminApi.listByCode(code ? code : undefined, { page, page_size: pageSize });
    list.value = data.orders || []; totals.value = data.totals || {}; pages = data.pages || 1; page = data.page || 1; selectedNos.value = [];
    msg.value = '';
  } catch(e) { msg.value = friendlyError(e); }
}

onMounted(() => { if (isAdminOrSuper) { page = 1; listCode.value = ''; queryList(); } });

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
const showHistory = ref(false);
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
.btn { background:#1a1e27; border:1px solid #232736; color:#e6e7eb; padding:0 12px; border-radius:10px; cursor:pointer; display:inline-flex; align-items:center; justify-content:center; height:40px; line-height:1; }
.btn-gradient-text { height:40px; line-height:1; display:inline-flex; align-items:center; justify-content:center; }
.btn.danger { background:#35181b; border-color:#5b1f25; color:#ffb4c0; }
table { width: 100%; border-collapse: collapse; }
thead th { text-align: left; font-weight: 600; color: #aab0bd; padding: 6px 8px; border-bottom: 1px solid rgba(255,255,255,0.06); }
tbody td { padding: 6px 8px; border-bottom: 1px solid rgba(255,255,255,0.04); }
.title-wrap { margin: 0 0 4px; }
.title-fallback { font-size: 20px; font-weight: 800; letter-spacing: 0.5px; color: var(--text); }
.alert403 { color: #ffd7a0; background: rgba(255,183,77,0.08); border: 1px solid rgba(255,183,77,0.25); padding: 8px 10px; border-radius: 8px; }
</style>
