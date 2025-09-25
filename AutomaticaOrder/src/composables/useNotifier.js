import { ref, readonly } from 'vue';

const currentNotice = ref(null);
let timerId = null;
let noticeCounter = 0;

function clearTimer() {
  if (timerId !== null) {
    window.clearTimeout(timerId);
    timerId = null;
  }
}

export function showNotice({ title = '', message = '', type = 'info', duration = 2400 } = {}) {
  clearTimer();
  const id = ++noticeCounter;
  currentNotice.value = {
    id,
    title,
    message,
    type,
  };
  if (duration !== 0) {
    timerId = window.setTimeout(() => hideNotice(id), duration);
  }
  return id;
}

export function hideNotice(id) {
  if (!currentNotice.value || (id && currentNotice.value.id !== id)) return;
  clearTimer();
  currentNotice.value = null;
}

export function useNoticeState() {
  return readonly(currentNotice);
}

export function useNotifier() {
  return { showNotice, hideNotice };
}
