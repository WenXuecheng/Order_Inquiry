import { ref, computed } from 'vue';
import { getToken, getRole } from './useAdminApi';

const tokenRef = ref('');
const roleRef = ref('');
let initialised = false;

function syncAuthState() {
  try { tokenRef.value = getToken() || ''; } catch { tokenRef.value = ''; }
  try { roleRef.value = getRole() || ''; } catch { roleRef.value = ''; }
}

function handleStorage(event) {
  if (!event || (event.key !== 'admin_token' && event.key !== 'admin_role')) return;
  syncAuthState();
}

function handleVisibility() {
  if (!document.hidden) syncAuthState();
}

function handleFocus() {
  syncAuthState();
}

function init() {
  if (initialised || typeof window === 'undefined') return;
  initialised = true;
  syncAuthState();
  window.addEventListener('admin-auth-changed', syncAuthState);
  window.addEventListener('storage', handleStorage);
  document.addEventListener('visibilitychange', handleVisibility);
  window.addEventListener('focus', handleFocus);
}

export function useAuthState() {
  init();
  return {
    token: tokenRef,
    role: roleRef,
    isLoggedIn: computed(() => !!tokenRef.value),
    roleName: computed(() => roleRef.value || ''),
    sync: syncAuthState,
  };
}
