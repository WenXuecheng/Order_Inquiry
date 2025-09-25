<template>
  <div class="register-stepper" v-bind="$attrs">
    <div class="stepper-card">
      <div class="stepper-header">
        <template v-for="(_, index) in steps" :key="index + 1">
          <div
            class="step-indicator"
            :class="getStepStatus(index + 1)"
            role="button"
            tabindex="0"
            @click="() => handleStepClick(index + 1)"
          >
            <template v-if="getStepStatus(index + 1) === 'complete'">
              <svg class="checkmark" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <Motion
                  as="path"
                  d="M5 13l4 4L19 7"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  :initial="{ pathLength: 0, opacity: 0 }"
                  :animate="{ pathLength: 1, opacity: 1 }"
                />
              </svg>
            </template>
            <div v-else-if="getStepStatus(index + 1) === 'active'" class="active-dot" />
            <span v-else>{{ index + 1 }}</span>
          </div>
          <div v-if="index < steps.length - 1" class="step-divider">
            <Motion
              as="div"
              class="divider-progress"
              :initial="{ width: 0, backgroundColor: '#52525b' }"
              :animate="currentStep > index + 1 ? { width: '100%', backgroundColor: '#27ff64' } : { width: 0, backgroundColor: '#52525b' }"
              :transition="{ type: 'spring', stiffness: 100, damping: 15, duration: 0.4 }"
            />
          </div>
        </template>
      </div>

      <Motion
        as="div"
        class="content-shell"
        :style="{ overflow: 'hidden', position: 'relative' }"
        :animate="{ height: isCompleted ? `${completedHeight}px` : `${parentHeight + 1}px` }"
        :transition="{ type: 'spring', stiffness: 200, damping: 25, duration: 0.4 }"
      >
        <AnimatePresence :initial="false" mode="sync" :custom="direction">
          <Motion
            v-if="!isCompleted"
            ref="containerRef"
            as="div"
            :key="currentStep"
            class="step-content"
            :initial="getStepContentInitial()"
            :animate="{ x: '0%', opacity: 1 }"
            :exit="getStepContentExit()"
            :transition="{ type: 'tween', stiffness: 300, damping: 30, duration: 0.4 }"
          >
            <div ref="contentRef">
              <div v-if="currentStep === 1" class="step-form">
                <h3>账号信息</h3>
                <p class="muted">请设置用于登录的用户名和密码，并输入管理员提供的邀请码。</p>
                <div class="form-grid">
                  <div class="username-row">
                    <input class="input" v-model="form.username" placeholder="用户名" />
                    <button type="button" class="btn-outline secondary" :disabled="usernameState.generating" @click="generateUsername">
                      {{ usernameState.generating ? '生成中…' : '随机用户名' }}
                    </button>
                  </div>
                  <input class="input" type="password" v-model="form.password" placeholder="密码" />
                  <input class="input" v-model="form.inviteCode" placeholder="邀请码" />
                </div>
                <p v-if="usernameFeedback" class="hint" :class="{ danger: !usernameState.available }">{{ usernameFeedback }}</p>
                <div class="link-row">
                  <span class="muted">已有账号？</span>
                  <button type="button" class="link-btn" @click="goToLogin">去登录</button>
                </div>
              </div>
              <div v-else-if="currentStep === 2" class="step-form">
                <h3>绑定编号（可选）</h3>
                <p class="muted">填写后可直接查看对应编号的订单，可跳过。</p>
                <div class="codes-grid">
                  <div class="code-row" v-for="(code, index) in form.codes" :key="`code-${index}`">
                    <input class="input" v-model="form.codes[index]" placeholder="编号，如 A666" />
                    <button type="button" class="btn-outline remove" @click="removeCode(index)" :disabled="form.codes.length === 1">删除</button>
                  </div>
                </div>
                <button class="btn-outline add-code" type="button" @click="addCode">新增编号</button>
              </div>
              <div v-else class="step-form">
                <h3>提交注册</h3>
                <p class="muted">确认信息后点击完成注册。</p>
                <ul class="summary-list">
                  <li><span>用户名：</span><span>{{ form.username || '—' }}</span></li>
                  <li><span>绑定编号：</span><span>{{ formattedCodes }}</span></li>
                  <li><span>邀请码：</span><span>{{ form.inviteCode || '未填写' }}</span></li>
                </ul>
              </div>
            </div>
          </Motion>
          <Motion
            v-else
            key="completed"
            class="step-content"
            :initial="{ y: 20, opacity: 0 }"
            :animate="{ y: 0, opacity: 1 }"
            :exit="{ y: -20, opacity: 0 }"
            :transition="{ duration: 0.3 }"
          >
            <div class="complete-state">
              <h3>注册成功</h3>
              <p>账号已创建，正在跳转到订单查询页面…</p>
            </div>
          </Motion>
        </AnimatePresence>
      </Motion>

      <div class="step-actions" v-if="!isCompleted">
        <div class="actions-row">
          <button v-if="currentStep !== 1" type="button" class="btn-outline" @click="handleBack">上一步</button>
          <button type="button" class="btn-gradient" @click="handleNext" :disabled="submitting">
            {{ currentStep === steps.length ? (submitting ? '注册中…' : '完成注册') : '下一步' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { AnimatePresence, Motion } from 'motion-v';
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, useTemplateRef, watch } from 'vue';
import { adminApi, setRole, setToken } from '../../composables/useAdminApi';
import { useNotifier } from '../../composables/useNotifier';
import { useCurrentRoute, navigateTo, ROUTES } from '../../router/useSimpleRouter';

const emit = defineEmits(['logged-in']);

const steps = ['账号信息', '绑定编号', '完成'];
const currentStep = ref(1);
const direction = ref(1);
const isCompleted = ref(false);
const submitting = ref(false);
const parentHeight = ref(0);
const completedHeight = 220;
const MIN_CONTENT_HEIGHT = 360;
const containerRef = useTemplateRef<HTMLDivElement>('containerRef');
const contentRef = useTemplateRef<HTMLDivElement>('contentRef');

const form = reactive({
  username: '',
  password: '',
  inviteCode: '',
  codes: [''],
});

const usernameState = reactive({
  checking: false,
  available: true,
  lastChecked: '',
  generating: false,
});

const { showNotice } = useNotifier();
const route = useCurrentRoute();

const formattedCodes = computed(() => {
  const filtered = form.codes.map(code => code.trim()).filter(Boolean);
  return filtered.length ? filtered.join('，') : '未绑定';
});

const redirectRaw = computed(() => {
  let raw = route.value?.query?.redirect as string | undefined;
  if (Array.isArray(raw)) raw = raw[0];
  if (!raw) {
    try {
      const params = new URLSearchParams(window.location.search || '');
      raw = params.get('redirect') || undefined;
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
  return { name: target.name, anchor: anchorPart || '' };
});

const usernameFeedback = computed(() => {
  const name = form.username.trim();
  if (!name) return '';
  if (usernameState.checking) return '正在检测用户名…';
  if (!usernameState.lastChecked) return '';
  if (usernameState.lastChecked === name) {
    return usernameState.available ? '用户名可用' : '用户名已存在，请重新输入';
  }
  return '';
});

function getStepStatus(step: number) {
  if (isCompleted.value || step < currentStep.value) return 'complete';
  if (currentStep.value === step) return 'active';
  return 'inactive';
}

function getStepContentInitial() {
  return {
    x: direction.value >= 0 ? '-100%' : '100%',
    opacity: 0,
  };
}

function getStepContentExit() {
  return {
    x: direction.value >= 0 ? '50%' : '-50%',
    opacity: 0,
  };
}

function handleStepClick(step: number) {
  if (isCompleted.value) return;
  if (step < currentStep.value) {
    direction.value = -1;
    updateStep(step);
  }
}

function updateStep(step: number) {
  currentStep.value = Math.min(Math.max(step, 1), steps.length);
  measureHeight();
}

function handleBack() {
  direction.value = -1;
  updateStep(currentStep.value - 1);
}

function addCode() {
  form.codes.push('');
  measureHeight();
}

function removeCode(index: number) {
  if (form.codes.length === 1) return;
  form.codes.splice(index, 1);
  measureHeight();
}

async function ensureUsernameAvailable() {
  const name = form.username.trim();
  if (!name) return false;
  if (usernameState.lastChecked === name && usernameState.available) return true;
  usernameState.checking = true;
  try {
    const data = await adminApi.checkUsername(name);
    usernameState.available = !!data?.available;
    usernameState.lastChecked = name;
    if (!usernameState.available) {
      showNotice({ type: 'error', message: '用户名已存在，请更换后重试' });
    }
    return usernameState.available;
  } catch (error) {
    const message = (error && (error as Error).message) || '检测用户名失败，请稍后再试';
    showNotice({ type: 'error', message });
    return false;
  } finally {
    usernameState.checking = false;
  }
}

async function validateStep() {
  if (currentStep.value === 1) {
    if (!form.username.trim() || !form.password.trim()) {
      showNotice({ type: 'error', message: '请填写用户名和密码' });
      return false;
    }
    if (!form.inviteCode.trim()) {
      showNotice({ type: 'error', message: '请输入邀请码' });
      return false;
    }
    if (!(await ensureUsernameAvailable())) {
      return false;
    }
  }
  return true;
}

function cleanCodes() {
  return form.codes.map(code => code.trim()).filter(Boolean);
}

function scrollToAnchor(anchor: string) {
  if (!anchor) return;
  window.setTimeout(() => {
    const section = document.getElementById(anchor);
    section?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, 300);
}

function goToLogin() {
  const raw = redirectRaw.value;
  navigateTo('login', raw ? { query: { redirect: raw } } : {});
}

async function submitRegistration() {
  submitting.value = true;
  try {
    const payloadCodes = cleanCodes();
    const data = await adminApi.register(form.username, form.password, payloadCodes, form.inviteCode);
    setToken(data.access_token);
    if (data.role) setRole(data.role);
    showNotice({ type: 'success', title: '注册成功', message: '欢迎加入，正在跳转…', duration: 2600 });
    isCompleted.value = true;
    emit('logged-in');
    const { name, anchor } = redirectTarget.value;
    window.setTimeout(() => {
      navigateTo(name);
      scrollToAnchor(anchor);
    }, 1200);
  } catch (error) {
    const message = (error && (error as Error).message) || '注册失败，请稍后再试';
    showNotice({ type: 'error', title: '注册失败', message });
  } finally {
    submitting.value = false;
  }
}

async function handleNext() {
  if (!(await validateStep())) return;
  if (currentStep.value < steps.length) {
    direction.value = 1;
    updateStep(currentStep.value + 1);
    return;
  }
  await submitRegistration();
}

async function generateUsername() {
  usernameState.generating = true;
  try {
    const prefix = form.username.trim() || 'user';
    const data = await adminApi.randomUsername(prefix);
    if (data?.username) {
      form.username = data.username;
      usernameState.lastChecked = data.username;
      usernameState.available = true;
      measureHeight();
    }
  } catch (error) {
    const message = (error && (error as Error).message) || '生成用户名失败，请稍后再试';
    showNotice({ type: 'error', message });
  } finally {
    usernameState.generating = false;
  }
}

function measureHeight() {
  nextTick(() => {
    if (contentRef.value) {
      const height = contentRef.value.offsetHeight;
      if (height > 0) parentHeight.value = Math.max(height, MIN_CONTENT_HEIGHT);
    }
  });
}

watch(() => form.username, () => {
  usernameState.lastChecked = '';
  usernameState.available = true;
});

const handleResize = () => measureHeight();

watch(usernameFeedback, () => measureHeight());

onMounted(() => {
  measureHeight();
  if (typeof window !== 'undefined') {
    window.setTimeout(() => measureHeight(), 80);
    window.addEventListener('resize', handleResize);
  } else {
    setTimeout(() => measureHeight(), 80);
  }
});

onUnmounted(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', handleResize);
  }
});
</script>

<style scoped>
.register-stepper { display: flex; justify-content: center; padding: 12px; }
.stepper-card {
  width: min(640px, 100%);
  padding: 28px;
  border-radius: 34px;
  border: 1px solid rgba(148, 205, 255, 0.22);
  background: rgba(12, 18, 30, 0.9);
  box-shadow: 0 30px 60px rgba(2, 10, 24, 0.45);
  display: flex;
  flex-direction: column;
  gap: 28px;
}
.stepper-header { display: flex; align-items: center; gap: 12px; }
.step-indicator {
  width: 36px;
  height: 36px;
  border-radius: 999px;
  border: 1px solid rgba(82, 82, 91, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(226, 232, 240, 0.8);
  background: rgba(12, 18, 28, 0.8);
  cursor: pointer;
  transition: border-color 220ms ease, color 220ms ease, background 220ms ease;
}
.step-indicator.complete { background: #27ff64; color: #032012; border-color: transparent; }
.step-indicator.active { background: #27ff64; color: #032012; border-color: transparent; }
.active-dot { width: 10px; height: 10px; border-radius: 999px; background: #032012; }
.step-divider { flex: 1; height: 2px; background: rgba(82, 82, 91, 0.6); border-radius: 2px; position: relative; overflow: hidden; }
.divider-progress { height: 100%; }
.checkmark { width: 18px; height: 18px; color: #032012; }

.content-shell { border-radius: 26px; background: rgba(10, 16, 26, 0.78); padding: 0 0 28px; box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06); }
.step-content { padding: 28px 28px 20px; }
.step-form { display: flex; flex-direction: column; gap: 16px; color: #e5e7eb; }
.muted { color: rgba(203, 213, 225, 0.75); font-size: 0.92rem; }
.form-grid { display: grid; gap: 14px; }
.username-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; align-items: center; }
.btn-outline.secondary { height: 44px; padding: 0 18px; }
.hint { margin: -6px 0 0; font-size: 0.85rem; color: rgba(148, 205, 255, 0.85); }
.hint.danger { color: #fca5a5; }
.codes-grid { display: flex; flex-direction: column; gap: 10px; }
.code-row { display: flex; gap: 8px; }
.code-row .remove { min-width: 72px; }
.add-code { align-self: flex-start; }
.summary-list { list-style: none; padding: 0; margin: 0; display: grid; gap: 6px; }

.link-row { display: flex; gap: 8px; align-items: center; }
.link-btn { background: none; border: none; color: #27ff64; cursor: pointer; font-weight: 600; padding: 0; }
.link-btn:hover { text-decoration: underline; }
.summary-list span:first-child { color: rgba(203, 213, 225, 0.7); margin-right: 6px; }
.complete-state { padding: 24px; text-align: center; color: #e5e7eb; display: flex; flex-direction: column; gap: 8px; }

.step-actions { display: flex; justify-content: flex-end; padding: 0 4px; }
.actions-row { display: flex; gap: 12px; }
.btn-outline { background: rgba(30, 36, 49, 0.6); border: 1px solid rgba(78, 99, 128, 0.6); color: #d1d8e8; border-radius: 12px; padding: 10px 18px; cursor: pointer; transition: background 0.2s ease, border-color 0.2s ease; }
.btn-outline:hover { background: rgba(70, 255, 175, 0.14); border-color: rgba(70, 255, 175, 0.5); color: #bdf4d1; }
.btn-gradient { border: 1px solid rgba(255, 255, 255, 0.16); background: linear-gradient(135deg, rgba(39, 255, 100, 0.82), rgba(126, 243, 255, 0.66)); color: #071218; border-radius: 14px; padding: 10px 22px; font-weight: 600; cursor: pointer; box-shadow: 0 18px 30px rgba(20, 200, 120, 0.22); backdrop-filter: blur(8px); transition: transform 0.18s ease, box-shadow 0.2s ease; }
.btn-gradient:hover { transform: translateY(-1px); box-shadow: 0 20px 36px rgba(20, 200, 120, 0.26); }

@media (max-width: 640px) {
  .stepper-card { padding: 22px; }
  .step-indicator { width: 32px; height: 32px; }
  .code-row { flex-direction: column; }
  .username-row { grid-template-columns: 1fr; }
}
</style>
