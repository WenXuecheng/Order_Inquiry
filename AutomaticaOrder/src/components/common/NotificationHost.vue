<template>
  <teleport to="body">
    <transition name="notice-fade" appear>
      <div v-if="notice" class="notice-overlay" role="alertdialog" aria-live="assertive">
        <div class="notice-card" :class="`notice-${notice.type}`">
          <div class="notice-content">
            <h3 v-if="notice.title" class="notice-title">{{ notice.title }}</h3>
            <p v-if="notice.message" class="notice-message">{{ notice.message }}</p>
          </div>
          <button type="button" class="notice-close" @click="close(notice.id)" aria-label="关闭通知">
            ×
          </button>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup>
import { computed } from 'vue';
import { hideNotice, useNoticeState } from '../../composables/useNotifier';

const state = useNoticeState();
const notice = computed(() => state.value);
const close = (id) => hideNotice(id);
</script>

<style scoped>
.notice-fade-enter-active,
.notice-fade-leave-active {
  transition: opacity 220ms ease, transform 220ms ease;
}

.notice-fade-enter-from,
.notice-fade-leave-to {
  opacity: 0;
  transform: translateY(12px) scale(0.98);
}

.notice-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  z-index: 9999;
  pointer-events: none;
}

.notice-card {
  pointer-events: auto;
  min-width: min(360px, 90vw);
  max-width: min(420px, 92vw);
  border-radius: 22px;
  border: 1px solid rgba(255, 255, 255, 0.28);
  background: linear-gradient(135deg, rgba(12, 18, 28, 0.52), rgba(12, 18, 28, 0.68));
  backdrop-filter: blur(22px) saturate(1.45);
  -webkit-backdrop-filter: blur(22px) saturate(1.45);
  box-shadow:
    0 28px 46px rgba(3, 12, 20, 0.55),
    inset 0 1px 0 rgba(255, 255, 255, 0.18),
    inset 0 -1px 0 rgba(39, 255, 100, 0.08);
  color: #f7fafc;
  position: relative;
  padding: 26px 28px 22px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.notice-card.notice-success {
  border-color: rgba(46, 204, 113, 0.55);
  box-shadow:
    0 28px 56px rgba(15, 111, 58, 0.45),
    inset 0 1px 0 rgba(255, 255, 255, 0.18);
}

.notice-card.notice-error {
  border-color: rgba(240, 71, 71, 0.6);
  box-shadow:
    0 28px 56px rgba(140, 30, 30, 0.45),
    inset 0 1px 0 rgba(255, 255, 255, 0.18);
}

.notice-card::before {
  content: '';
  position: absolute;
  inset: 1px;
  border-radius: inherit;
  background: radial-gradient(circle at 20% 20%, rgba(126, 246, 177, 0.18), transparent 55%), radial-gradient(circle at 80% 10%, rgba(125, 211, 252, 0.14), transparent 50%);
  opacity: 0.9;
  pointer-events: none;
}

.notice-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.notice-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  letter-spacing: 0.4px;
}

.notice-message {
  margin: 0;
  font-size: 0.95rem;
  color: rgba(226, 231, 241, 0.92);
  line-height: 1.5;
}

.notice-close {
  position: absolute;
  top: 14px;
  right: 16px;
  border: none;
  background: transparent;
  color: rgba(245, 249, 255, 0.68);
  font-size: 1.4rem;
  line-height: 1;
  cursor: pointer;
  transition: color 0.18s ease;
}

.notice-close:hover,
.notice-close:focus-visible {
  color: #ffffff;
  outline: none;
}

@media (max-width: 640px) {
  .notice-card {
    padding: 20px 22px 18px;
    border-radius: 18px;
  }
}
</style>
