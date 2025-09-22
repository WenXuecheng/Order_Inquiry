<template>
  <section>
    <h3>我的订单</h3>
    <div v-if="!isLoggedIn" class="muted">请先登录</div>
    <div v-else>
      <div class="row" style="gap:8px; align-items:center; margin-bottom:8px;">
        <label>我的编号
          <select class="input" v-model="currentCode" @change="loadOrders(1)">
            <option v-for="c in codes" :key="c" :value="c">{{ c }}</option>
          </select>
        </label>
        <input class="input" v-model="newCode" placeholder="新增编号" />
        <button class="btn" @click="addCode">绑定</button>
        <button class="btn danger" :disabled="!currentCode" @click="removeCode">解绑当前</button>
      </div>
      <div class="muted" v-if="codes.length===0">尚未绑定编号，可输入后点击绑定。</div>

      <div v-if="currentCode" style="overflow:auto;">
        <table>
          <thead><tr><th>订单号</th><th>编号</th><th>重量</th><th>状态</th><th>更新</th></tr></thead>
          <tbody>
            <tr v-for="o in list" :key="o.id">
              <td>{{ o.order_no }}</td>
              <td>{{ o.group_code || '' }}</td>
              <td>{{ (o.weight_kg ?? 0).toFixed(2) }} kg</td>
              <td>{{ o.status }}</td>
              <td>{{ o.updated_at }}</td>
            </tr>
          </tbody>
        </table>
        <div class="row" style="gap:8px; justify-content:flex-end; margin-top:8px;">
          <button class="btn" @click="prevPage" :disabled="page<=1">上一页</button>
          <span class="muted">第 {{ page }} / {{ pages }} 页</span>
          <button class="btn" @click="nextPage" :disabled="page>=pages">下一页</button>
        </div>
      </div>
      <div class="muted">{{ msg }}</div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { adminApi, getToken } from '../../composables/useAdminApi';

const isLoggedIn = computed(() => !!getToken());
const codes = ref([]);
const currentCode = ref('');
const newCode = ref('');
const list = ref([]);
const pageSize = 20; let page = 1; let pages = 1;
const msg = ref('');

async function loadCodes(){
  try { const d = await adminApi.apiFetch ? adminApi.apiFetch : null; } catch {}
  try {
    const r = await fetch(`${location.origin.replace(/\/$/,'')}/orderapi/user/codes`, { credentials:'include', headers: { 'Authorization': `Bearer ${localStorage.getItem('admin_token')||''}` } });
    if (!r.ok) throw new Error('加载编号失败');
    const j = await r.json(); codes.value = j.codes || [];
    if (!currentCode.value && codes.value.length) { currentCode.value = codes.value[0]; await loadOrders(1); }
  } catch(e){ msg.value = e.message; }
}

async function addCode(){
  const c = (newCode.value || '').trim(); if (!c) return;
  try {
    const r = await fetch(`/orderapi/user/codes`, { method:'POST', credentials:'include', headers:{ 'Authorization': `Bearer ${localStorage.getItem('admin_token')||''}`, 'Content-Type':'application/json' }, body: JSON.stringify({ code: c }) });
    if (!r.ok) throw new Error('绑定失败');
    newCode.value=''; await loadCodes();
  } catch(e){ msg.value = e.message; }
}

async function removeCode(){
  if (!currentCode.value) return;
  try {
    const r = await fetch(`/orderapi/user/codes`, { method:'DELETE', credentials:'include', headers:{ 'Authorization': `Bearer ${localStorage.getItem('admin_token')||''}`, 'Content-Type':'application/json' }, body: JSON.stringify({ code: currentCode.value }) });
    if (!r.ok) throw new Error('解绑失败');
    currentCode.value=''; await loadCodes(); list.value=[];
  } catch(e){ msg.value = e.message; }
}

async function loadOrders(p=1){
  if (!currentCode.value) return;
  page = p; msg.value = '加载中...';
  try {
    const data = await adminApi.listByCode(currentCode.value, { page, page_size: pageSize });
    list.value = data.orders || []; pages = data.pages || 1; page = data.page || 1; msg.value='';
  } catch(e){ msg.value = e.message; }
}
function prevPage(){ if (page>1) loadOrders(page-1); }
function nextPage(){ if (page<pages) loadOrders(page+1); }

onMounted(() => { if (isLoggedIn.value) loadCodes(); });
</script>

<style scoped>
table { width: 100%; border-collapse: collapse; }
thead th { text-align: left; font-weight: 600; color: #aab0bd; padding: 6px 8px; border-bottom: 1px solid rgba(255,255,255,0.06); }
tbody td { padding: 6px 8px; border-bottom: 1px solid rgba(255,255,255,0.04); }
</style>

