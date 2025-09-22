<template>
  <section>
    <h1>管理员登录</h1>
    <p class="muted">请输入后台账号密码。</p>
    <form class="stack" @submit.prevent="onSubmit">
      <div class="field">
        <label class="label">用户名</label>
        <input class="input" v-model="username" type="text" autocomplete="username" placeholder="输入用户名" />
      </div>
      <div class="field">
        <label class="label">密码</label>
        <input class="input" v-model="password" type="password" autocomplete="current-password" placeholder="输入密码" />
      </div>
      <div class="row" style="align-items:center; gap:8px;">
        <button type="submit" class="btn-gradient-text" :disabled="submitting">{{ submitting ? '登录中...' : '登录' }}</button>
        <span class="muted" v-if="msg">{{ msg }}</span>
      </div>
    </form>
  </section>
  
</template>

<script setup>
import { ref } from 'vue';
import { adminApi, setToken } from '../../composables/useAdminApi';

const emit = defineEmits(['logged-in']);
const username = ref('');
const password = ref('');
const submitting = ref(false);
const msg = ref('');

async function onSubmit(){
  if (!username.value || !password.value) { msg.value = '请输入用户名和密码'; return; }
  submitting.value = true; msg.value = '';
  try {
    const data = await adminApi.login(username.value, password.value);
    if (!data || !data.access_token) throw new Error('登录失败');
    setToken(data.access_token);
    emit('logged-in');
  } catch(e) {
    msg.value = e.message || '登录失败';
  } finally { submitting.value = false; }
}
</script>
