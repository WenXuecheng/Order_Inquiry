<template>
  <section class="change-pass-page">
    <h2 class="page-title">修改密码</h2>
    <p class="muted">出于安全考虑，请填写当前密码并设置一个至少 6 位的新密码。</p>

    <form class="form-card" @submit.prevent="submit">
      <label class="field">当前密码
        <input class="input" type="password" v-model="form.old" autocomplete="current-password" placeholder="请输入当前密码" />
      </label>
      <label class="field">新密码
        <input class="input" type="password" v-model="form.new" autocomplete="new-password" placeholder="不少于 6 位" />
      </label>
      <label class="field">确认新密码
        <input class="input" type="password" v-model="form.confirm" autocomplete="new-password" placeholder="再次输入新密码" />
      </label>
      <div class="actions">
        <button class="btn-gradient-text" type="submit" :disabled="form.loading">{{ form.loading ? '修改中…' : '确认修改' }}</button>
        <button class="btn-outline" type="button" @click="reset" :disabled="form.loading">清空</button>
      </div>
      <p v-if="form.message" class="message" :class="{ error: form.error }">{{ form.message }}</p>
    </form>
  </section>
</template>

<script setup>
import { reactive } from 'vue';
import { adminApi } from '../../composables/useAdminApi';
import { useNotifier } from '../../composables/useNotifier';

const { showNotice } = useNotifier();
const form = reactive({ old: '', new: '', confirm: '', loading: false, message: '', error: false });

function reset() {
  form.old = '';
  form.new = '';
  form.confirm = '';
  form.message = '';
  form.error = false;
}

async function submit() {
  if (form.loading) return;
  form.message = '';
  form.error = false;
  const oldPwd = form.old.trim();
  const newPwd = form.new.trim();
  const confirmPwd = form.confirm.trim();
  if (!oldPwd || !newPwd) {
    form.message = '请输入当前密码与新密码';
    form.error = true;
    showNotice({ type: 'error', message: form.message });
    return;
  }
  if (newPwd.length < 6) {
    form.message = '新密码至少 6 位';
    form.error = true;
    showNotice({ type: 'error', message: form.message });
    return;
  }
  if (newPwd !== confirmPwd) {
    form.message = '两次输入的新密码不一致';
    form.error = true;
    showNotice({ type: 'error', message: form.message });
    return;
  }
  form.loading = true;
  try {
    await adminApi.changePassword({ old_password: oldPwd, new_password: newPwd });
    form.message = '密码已更新，请妥善保管。';
    form.error = false;
    showNotice({ type: 'success', message: form.message });
    reset();
  } catch (error) {
    const detail = error?.message || '修改密码失败，请稍后重试';
    form.message = detail;
    form.error = true;
    showNotice({ type: 'error', message: detail });
  } finally {
    form.loading = false;
  }
}
</script>

<style scoped>
.change-pass-page {
  max-width: 420px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-title { font-size: 1.4rem; font-weight: 700; color: #f0f4ff; letter-spacing: 0.4px; margin: 0; }
.muted { color: rgba(203, 213, 225, 0.78); margin: 0 0 6px; }

.form-card {
  background: rgba(13, 20, 34, 0.55);
  border: 1px solid rgba(148, 205, 255, 0.28);
  border-radius: 18px;
  padding: 20px 22px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  box-shadow: 0 18px 36px rgba(5, 12, 24, 0.32);
}

.field { display: grid; gap: 6px; color: rgba(203, 213, 225, 0.92); font-weight: 600; }

.actions { display: flex; gap: 10px; justify-content: flex-end; }
.actions .btn-gradient-text,
.actions .btn-outline { min-width: 120px; height: 40px; border-radius: 12px; }

.message { margin: 0; font-size: 0.88rem; color: rgba(148, 205, 255, 0.86); }
.message.error { color: #fecaca; }

@media (max-width: 640px) {
  .change-pass-page { max-width: 100%; }
  .actions { flex-direction: column; align-items: stretch; }
  .actions .btn-gradient-text,
  .actions .btn-outline { width: 100%; }
}
</style>
