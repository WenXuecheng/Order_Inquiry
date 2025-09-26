<template>
  <section>
    <h3>账号</h3>
<div class="row" style="gap:8px; align-items:center; flex-wrap:wrap;">
  <template v-if="isLoggedIn">
    <span class="muted">已登录（角色：{{ roleName || 'user' }}）</span>
    <button class="btn" @click="onLogout">退出</button>
    <button class="btn-outline" type="button" @click="goChangePassword">
      修改密码
    </button>
  </template>
      <template v-else-if="showSwitch">
        <button class="btn" :class="{ active: mode==='login' }" @click="mode='login'">登录</button>
        <button class="btn" :class="{ active: mode==='register' }" @click="mode='register'">注册</button>
      </template>
    </div>

    <form v-if="isLoginView" class="stack" @submit.prevent="onLogin">
      <div class="stack" style="gap:8px;">
        <input class="input" v-model="username" placeholder="用户名" />
        <input class="input" v-model="password" type="password" placeholder="密码" />
        <button class="btn-gradient-text full-btn" type="submit" :disabled="submitting">{{ submitting ? '登录中…' : '登录' }}</button>
      </div>
      <div class="muted link-row">
        <span>没有账号？</span>
        <button class="link-chip" type="button" @click="goToRegister">去注册</button>
      </div>
      <div v-if="msg" class="muted tiny">{{ msg }}</div>
    </form>

    <form v-if="isRegisterView" class="stack" @submit.prevent="onRegister">
      <div class="row" style="gap:8px; align-items:stretch;">
        <input class="input" v-model="username" placeholder="用户名" />
        <input class="input" v-model="password" type="password" placeholder="密码" />
      </div>
      <div class="row" style="gap:8px; align-items:stretch;">
        <input class="input" v-model="inviteCode" placeholder="邀请码" />
        <input class="input" v-model="codes" placeholder="绑定编号（逗号分隔，可选）" />
      </div>
      <div class="row" style="gap:8px; align-items:stretch;">
        <button class="btn-gradient-text" style="flex:1" type="submit" :disabled="submitting">{{ submitting ? '注册中...' : '注册' }}</button>
      </div>
      <div class="muted link-row">
        <span>已有账号？</span>
    <button class="link-chip" type="button" @click="goToLogin">去登录</button>
  </div>
  <div v-if="msg" class="muted tiny">{{ msg }}</div>
</form>

</section>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { adminApi, setToken, setRole, clearToken, clearRole } from '../../composables/useAdminApi';
import { useAuthState } from '../../composables/useAuthState';
import { useNotifier } from '../../composables/useNotifier';
import { useCurrentRoute, navigateTo, ROUTES } from '../../router/useSimpleRouter';

const props = defineProps({ initialMode: { type: String, default: 'login' }, showSwitch: { type: Boolean, default: true } });
const emit = defineEmits(['logged-in', 'logged-out']);

const { isLoggedIn, roleName } = useAuthState();
const route = useCurrentRoute();
const { showNotice } = useNotifier();

const mode = ref(props.initialMode || 'login');
const username = ref('');
const password = ref('');
const codes = ref('');
const inviteCode = ref('');
const msg = ref('');
const submitting = ref(false);
let redirectTimer = null;

const redirectRaw = computed(() => {
  let raw = route.value?.query?.redirect;
  if (Array.isArray(raw)) raw = raw[0];
  if (!raw) {
    try {
      const params = new URLSearchParams(window.location.search || '');
      raw = params.get('redirect');
    } catch {}
  }
  return raw && raw.trim() ? raw.trim() : 'home';
});

const redirectTarget = computed(() => {
  let raw = redirectRaw.value || 'home';
  raw = raw.replace(/^#/, '');
  if (raw.startsWith('/')) raw = raw.slice(1);
  const [pathPart, anchorPart] = raw.split('#');
  const target = ROUTES.find(r => r.path === pathPart)
    || ROUTES.find(r => r.name === pathPart)
    || ROUTES[0];
  return { name: target.name, path: target.path, anchor: anchorPart || '' };
});

const isLoginView = computed(() => !isLoggedIn.value && mode.value === 'login');
const isRegisterView = computed(() => !isLoggedIn.value && mode.value === 'register');

function scheduleRedirect() {
  if (redirectTimer) window.clearTimeout(redirectTimer);
  const { name, anchor } = redirectTarget.value;
  const go = () => {
    navigateTo(name);
    if (anchor) {
      window.setTimeout(() => {
        const section = document.getElementById(anchor);
        section?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 220);
    }
  };
  redirectTimer = window.setTimeout(go, 360);
}

async function onLogin() {
  if (submitting.value) return;
  msg.value = '';
  submitting.value = true;
  try {
    const data = await adminApi.login(username.value, password.value);
    setToken(data.access_token);
    if (data.role) setRole(data.role);
    showNotice({ type: 'success', title: '登录成功', message: '欢迎回来，正在跳转…', duration: 2400 });
    emit('logged-in');
    scheduleRedirect();
    username.value = '';
    password.value = '';
  } catch (error) {
    const detail = error?.message || '登录失败，请稍后重试';
    msg.value = detail;
    showNotice({ type: 'error', title: '登录失败', message: detail, duration: 2800 });
  } finally {
    submitting.value = false;
  }
}

async function onRegister() {
  if (submitting.value) return;
  msg.value = '';
  submitting.value = true;
  try {
    const list = (codes.value || '').split(',').map(s => s.trim()).filter(Boolean);
    if (!inviteCode.value.trim()) {
      msg.value = '请输入邀请码';
      submitting.value = false;
      showNotice({ type: 'error', message: '请输入邀请码' });
      return;
    }
    const data = await adminApi.register(username.value, password.value, list, inviteCode.value.trim());
    setToken(data.access_token);
    if (data.role) setRole(data.role);
    showNotice({ type: 'success', title: '注册完成', message: '账号已创建，正在为你跳转…', duration: 2600 });
    emit('logged-in');
    scheduleRedirect();
    username.value = '';
    password.value = '';
    codes.value = '';
    inviteCode.value = '';
  } catch (error) {
    const detail = error?.message || '注册失败，请稍后重试';
    msg.value = detail;
    showNotice({ type: 'error', title: '注册失败', message: detail, duration: 3000 });
  } finally {
    submitting.value = false;
  }
}

function onLogout() {
  clearToken();
  clearRole();
  showNotice({ type: 'info', title: '已退出登录', message: '期待下次再见。', duration: 2200 });
  emit('logged-out');
  navigateTo('login');
}

function goChangePassword() {
  navigateTo('change-password');
}

const goToRegister = () => {
  const raw = redirectRaw.value;
  navigateTo('register', raw ? { query: { redirect: raw } } : {});
};

const goToLogin = () => {
  const raw = redirectRaw.value;
  navigateTo('login', raw ? { query: { redirect: raw } } : {});
};

watch(
  () => route.value?.name,
  (name) => {
    if (!props.showSwitch) {
      mode.value = name === 'register' ? 'register' : 'login';
    }
  },
  { immediate: true }
);

watch(
  () => props.initialMode,
  (value) => {
    if (!props.showSwitch) {
      mode.value = value || 'login';
    }
  }
);

watch(isLoggedIn, loggedIn => {
  if (!loggedIn && redirectTimer) {
    window.clearTimeout(redirectTimer);
    redirectTimer = null;
  }
});

onMounted(() => {
  if (isLoggedIn.value) {
    showNotice({ type: 'info', title: '已登录', message: '正在跳转…', duration: 2000 });
    scheduleRedirect();
  }
});

onUnmounted(() => {
  if (redirectTimer) window.clearTimeout(redirectTimer);
});
</script>

<style scoped>
.btn.active { border-color: #3d82f6; color:#cfe2ff; }
.full-btn { display: block; width: 100%; }
.full-btn:disabled { opacity: 0.75; cursor: wait; }
.link-row { display:flex; align-items:center; justify-content: space-between; gap:12px; margin-top:6px; }
.link-chip {
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.08);
  color: #9debba;
  border-radius: 999px;
  padding: 6px 16px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease;
  white-space: nowrap;
}
.link-chip:hover,
.link-chip:focus-visible {
  background: rgba(39, 255, 100, 0.2);
  border-color: rgba(39, 255, 100, 0.48);
  color: #1cff79;
  outline: none;
}
.tiny { font-size: 0.82rem; color: rgba(226, 235, 244, 0.78); margin-top: 4px; }
.btn-outline {
  border: 1px solid rgba(148, 205, 255, 0.32);
  background: rgba(10, 20, 36, 0.55);
  color: rgba(224, 235, 255, 0.86);
  padding: 6px 16px;
  border-radius: 10px;
  cursor: pointer;
  transition: transform 160ms ease, border-color 200ms ease, background 200ms ease;
}
.btn-outline:hover,
.btn-outline:focus-visible {
  border-color: rgba(102, 212, 255, 0.58);
  background: rgba(18, 32, 54, 0.72);
  transform: translateY(-1px);
  outline: none;
}

</style>
