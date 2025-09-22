<template>
  <section>
    <h3>账号</h3>
    <div class="row" style="gap:8px; align-items:center;">
      <template v-if="isLoggedIn">
        <span class="muted">已登录（角色：{{ role || 'user' }}）</span>
        <button class="btn" @click="onLogout">退出</button>
      </template>
      <template v-else-if="showSwitch">
        <button class="btn" :class="{ active: mode==='login' }" @click="mode='login'">登录</button>
        <button class="btn" :class="{ active: mode==='register' }" @click="mode='register'">注册</button>
      </template>
    </div>

    <form v-if="!isLoggedIn && mode==='login'" class="stack" @submit.prevent="onLogin">
      <div class="stack" style="gap:8px;">
        <input class="input" v-model="username" placeholder="用户名" />
        <input class="input" v-model="password" type="password" placeholder="密码" />
        <button class="btn-gradient-text full-btn" type="submit">登录</button>
      </div>
      <div class="muted">
        没有账号？
        <a :href="registerHref">去注册</a>
      </div>
      <div class="muted">{{ msg }}</div>
    </form>

    <form v-if="!isLoggedIn && mode==='register'" class="stack" @submit.prevent="onRegister">
      <div class="row" style="gap:8px;">
        <input class="input" v-model="username" placeholder="用户名" />
        <input class="input" v-model="password" type="password" placeholder="密码" />
      </div>
      <div class="row" style="gap:8px;">
        <input class="input" v-model="codes" placeholder="绑定编号（逗号分隔，可选）" />
        <button class="btn-gradient-text" type="submit">注册</button>
      </div>
      <div class="muted">
        已有账号？
        <a :href="loginHref">去登录</a>
      </div>
      <div class="muted">{{ msg }}</div>
    </form>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { adminApi, setToken, setRole, getToken, clearToken, clearRole, getRole } from '../../composables/useAdminApi';

const props = defineProps({ initialMode: { type: String, default: 'login' }, showSwitch: { type: Boolean, default: true } });
const emit = defineEmits(['logged-in', 'logged-out']);
const mode = ref(props.initialMode || 'login');
const username = ref('');
const password = ref('');
const codes = ref('');
const msg = ref('');
const role = getRole() || '';
const isLoggedIn = computed(() => !!getToken());
const redirect = computed(() => {
  try { const p = new URLSearchParams(location.search); return p.get('redirect') || '/'; } catch { return '/'; }
});
const registerHref = computed(() => `/register.html?redirect=${encodeURIComponent(redirect.value)}`);
const loginHref = computed(() => `/login.html?redirect=${encodeURIComponent(redirect.value)}`);

async function onLogin(){
  msg.value = '登录中...';
  try {
    const d = await adminApi.login(username.value, password.value);
    setToken(d.access_token); if (d.role) setRole(d.role);
    msg.value = '登录成功';
    try { window.location.href = redirect.value || '/'; } catch {}
    emit('logged-in');
  } catch(e) { msg.value = e.message; }
}

async function onRegister(){
  msg.value = '注册中...';
  try {
    const arr = (codes.value || '').split(',').map(s=>s.trim()).filter(Boolean);
    const d = await adminApi.register(username.value, password.value, arr);
    setToken(d.access_token); if (d.role) setRole(d.role);
    msg.value = '注册成功';
    try { window.location.href = redirect.value || '/'; } catch {}
    emit('logged-in');
  } catch(e) { msg.value = e.message; }
}

function onLogout(){
  clearToken(); clearRole();
  emit('logged-out');
}

onMounted(() => {
  mode.value = props.initialMode || 'login';
  // If already logged in and came to login/register page, auto-redirect to target
  if (getToken()) {
    try { window.location.href = (new URLSearchParams(location.search)).get('redirect') || '/'; } catch { window.location.href = '/'; }
  }
});
</script>

<style scoped>
.btn.active { border-color: #3d82f6; color:#cfe2ff; }
.full-btn { display: block; width: 100%; }
</style>
