<template>
  <section>
    <div class="row" style="justify-content: space-between; align-items:center; margin-bottom:12px;">
      <div class="title-wrap"><span class="title-fallback">用户管理</span></div>
      <a class="btn" href="/">返回首页</a>
    </div>

    <GlassSurface class-name="card" :width="'100%'" :height="'auto'" :background-opacity="0.12" :blur="8" :saturation="1.4" simple :center-content="false" :content-padding="12">
      <div class="row" style="gap:8px; margin-bottom:8px;">
        <input class="input" v-model="userQuery" placeholder="搜索用户名" />
        <select class="input" v-model="userRoleFilter"><option value="">全部角色</option><option value="user">普通用户</option><option value="admin">管理员</option><option value="superadmin">超级管理员</option></select>
        <button class="btn-gradient-text" @click="() => { userPage=1; loadUsers(); }">搜索</button>
        <button class="btn danger" :disabled="selectedUserIds.length===0" @click="deleteUsers">批量删除 ({{ selectedUserIds.length }})</button>
      </div>
      <div class="row" style="gap:8px; align-items:flex-end; margin-bottom:8px;">
        <label style="display:grid; gap:4px;">用户名<input class="input" v-model="newUser.username" /></label>
        <label style="display:grid; gap:4px;">密码<input class="input" type="password" v-model="newUser.password" /></label>
        <label style="display:grid; gap:4px;">角色<select class="input" v-model="newUser.role"><option value="user">普通用户</option><option value="admin">管理员</option><option value="superadmin">超级管理员</option></select></label>
        <label style="display:grid; gap:4px;">绑定编号(逗号分隔)<input class="input" v-model="newUser.codesStr" placeholder="如 A666,2025-01" /></label>
        <button class="btn-gradient-text" @click="createUser">创建用户</button>
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
              <td><button class="btn-gradient-text" @click="saveUser(u)">保存</button></td>
            </tr>
          </tbody>
        </table>
        <div class="row" style="gap:6px; justify-content:flex-end; margin-top:8px;">
          <button class="btn btn-outline" @click="prevUserPage" :disabled="userPage<=1">上一页</button>
          <span class="muted">第 {{ userPage }} / {{ userPages }} 页</span>
          <button class="btn btn-outline" @click="nextUserPage" :disabled="userPage>=userPages">下一页</button>
        </div>
      </div>
      <div class="muted" style="margin-top:8px;">{{ msg }}</div>
    </GlassSurface>
  </section>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import GlassSurface from '../vue_bits/Components/GlassSurface/GlassSurface.vue';
import { adminApi } from '../../composables/useAdminApi';

const users = ref([]);
const userQuery = ref('');
const userRoleFilter = ref('');
const selectedUserIds = ref([]);
const newUser = reactive({ username: '', password: '', role: 'user', codesStr: '' });
let userPage = 1; let userPages = 1; const userPageSize = 10;
const msg = ref('');

async function loadUsers(){
  try {
    const data = await adminApi.usersList({ q: userQuery.value, role: userRoleFilter.value, page: userPage, page_size: userPageSize });
    users.value = (data.items || []).map(u => ({ ...u, codesStr: (u.codes || []).join(',') }));
    userPages = data.pages || 1; userPage = data.page || 1; selectedUserIds.value = [];
  } catch(e) { msg.value = e.message; }
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

onMounted(() => { loadUsers(); });
</script>

<style scoped>
.title-wrap { margin: 0 0 4px; }
.title-fallback { font-size: 20px; font-weight: 800; letter-spacing: 0.5px; color: var(--text); }
table { width: 100%; border-collapse: collapse; }
thead th { text-align: left; font-weight: 600; color: #aab0bd; padding: 6px 8px; border-bottom: 1px solid rgba(255,255,255,0.06); }
tbody td { padding: 6px 8px; border-bottom: 1px solid rgba(255,255,255,0.04); }
</style>

