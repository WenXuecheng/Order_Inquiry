<template>
  <header :class="['app-header', { scrolled: isScrolled, 'menu-open': isMobile && mobileMenuOpen }]">
    <div class="header-container">
      <div
        v-if="!isMobile"
        class="brand"
        @click="goHome"
        role="button"
        tabindex="0"
        @keydown.enter.prevent="goHome"
      >
        <img class="brand-logo" src="/header-title.svg" alt="WenXC" />
      </div>
      <div class="nav-wrap">
        <div v-if="!isMobile" class="desktop-nav">
          <GooeyDock
            v-if="desktopVisibleDockItems.length"
            :items="desktopVisibleDockItems"
            :active-key="desktopActiveKey"
            @select="onDockSelect"
          />
          <div v-if="hasDesktopOverflow" class="desktop-overflow" ref="desktopOverflowRef">
            <button
              type="button"
              class="desktop-overflow-btn"
              @click="toggleDesktopOverflow"
              :aria-expanded="desktopOverflowOpen"
              aria-haspopup="true"
            >
              <span class="sr-only">更多导航</span>
              <svg viewBox="0 0 24 24" class="overflow-icon" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="5" cy="12" r="1.8" />
                <circle cx="12" cy="12" r="1.8" />
                <circle cx="19" cy="12" r="1.8" />
              </svg>
            </button>
            <transition name="drawer-slide">
              <div v-if="desktopOverflowOpen" class="desktop-overflow-panel">
                <button
                  v-for="item in desktopOverflowItems"
                  :key="item.key || item.label"
                  type="button"
                  class="desktop-overflow-item"
                  @click="selectDesktopOverflowItem(item)"
                >
                  {{ item.label }}
                </button>
              </div>
            </transition>
          </div>
        </div>
        <div v-else :class="['mobile-nav-container', { open: mobileMenuOpen }]" ref="mobileMenuRef">
          <div class="mobile-nav">
            <button
              v-if="primaryItem"
              type="button"
              class="current-pill"
              @click="handlePrimaryClick"
            >
              <span>{{ primaryItem.label }}</span>
            </button>
            <button
              v-if="extraItems.length || contacts.length"
              type="button"
              class="mobile-toggle"
              @click="toggleMobileMenu"
              :aria-expanded="mobileMenuOpen"
              aria-haspopup="true"
            >
              <svg class="toggle-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 7h14" />
                <path d="M5 12h14" />
                <path d="M5 17h14" />
              </svg>
            </button>
          </div>
          <transition name="drawer-slide">
            <div v-if="mobileMenuOpen" class="mobile-menu-panel">
              <div class="mobile-menu-section">
                <button
                  v-for="item in extraItems"
                  :key="item.key || item.label"
                  type="button"
                  class="mobile-menu-item"
                  @click="selectMobileItem(item)"
                >
                  {{ item.label }}
                </button>
              </div>
              <div v-if="contacts.length" class="mobile-menu-section contacts">
                <div class="mobile-menu-subtitle">联系方式</div>
                <ul class="mobile-contact-list">
                  <li v-for="(contact, idx) in contacts" :key="contact.key || idx">
                    <span class="contact-icon">{{ iconMap[contact.icon] || 'ℹ' }}</span>
                    <div class="contact-text">
                      <span class="label">{{ contact.label }}</span>
                      <a
                        v-if="contact.href"
                        :href="contact.href"
                        class="value"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {{ contact.value || contact.href }}
                      </a>
                      <span v-else class="value">{{ contact.value || '—' }}</span>
                    </div>
                  </li>
                </ul>
              </div>
            </div>
          </transition>
        </div>
      </div>
      <div v-if="!isMobile" class="actions">
        <button type="button" class="contact-btn" @click="toggleContacts" :aria-expanded="contactsOpen">
          <span class="dot" />
          <span>联系方式</span>
        </button>
      </div>
    </div>
    <transition name="contact-pop">
      <div v-if="contactsOpen && !isMobile" class="contact-panel" ref="contactPanelRef">
        <ul class="contact-list" role="list">
          <li v-for="(contact, idx) in contacts" :key="contact.key || idx" class="contact-item">
            <span class="contact-icon" aria-hidden="true">{{ iconMap[contact.icon] || 'ℹ' }}</span>
            <div class="contact-text">
              <span class="label">{{ contact.label }}</span>
              <a v-if="contact.href" :href="contact.href" class="value" target="_blank" rel="noopener noreferrer">{{ contact.value || contact.href }}</a>
              <span v-else class="value">{{ contact.value || '—' }}</span>
            </div>
          </li>
        </ul>
      </div>
    </transition>
  </header>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch, useTemplateRef } from 'vue';
import GooeyDock from './GooeyDock.vue';
import { useSiteMeta, fetchSiteMeta } from '../../composables/useSiteMeta';
import { useCurrentRoute, navigateTo } from '../../router/useSimpleRouter';
import { useAuthState } from '../../composables/useAuthState';
import { useNotifier } from '../../composables/useNotifier';

const { showNotice } = useNotifier();
const siteMeta = useSiteMeta();
const route = useCurrentRoute();
const { isLoggedIn, roleName } = useAuthState();
const isScrolled = ref(false);
const contactsOpen = ref(false);
const contactPanelRef = useTemplateRef<HTMLDivElement>('contactPanelRef');
const mobileMenuOpen = ref(false);
const mobileMenuRef = useTemplateRef<HTMLDivElement>('mobileMenuRef');
const desktopOverflowOpen = ref(false);
const desktopOverflowRef = useTemplateRef<HTMLDivElement>('desktopOverflowRef');
const isMobile = ref(false);
let mobileQuery: MediaQueryList | null = null;
const touchState = { active: false, startY: 0, startScroll: 0, triggered: false };
const overscrollTriggerDistance = 64;
const iconMap: Record<string, string> = {
  wechat: 'WX',
  phone: 'PH',
  mail: 'ML',
  custom: '*',
};

const currentRouteName = computed(() => route.value?.name || 'home');
const canManageOrders = computed(() => ['admin', 'superadmin'].includes(roleName.value));
const canManageUsers = computed(() => roleName.value === 'superadmin');
const canManageContent = computed(() => ['admin', 'superadmin'].includes(roleName.value));

const adminMenuItems = computed(() => {
  const items: Array<{ label: string; key: string; action: () => void }> = [];
  if (canManageOrders.value) items.push({ label: '订单管理', key: 'order-management', action: () => navigateTo('order-management') });
  if (canManageUsers.value) items.push({ label: '用户管理', key: 'user-management', action: () => navigateTo('user-management') });
  if (canManageContent.value) items.push({ label: '内容管理', key: 'content-management', action: () => navigateTo('content-management') });
  return items;
});

const goHome = () => {
  navigateTo('home');
};

const scrollToMyOrders = () => {
  nextTick(() => {
    const section = document.getElementById('my-orders') || document.getElementById('orders-card');
    if (section) {
      section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
      showNotice({ type: 'info', message: '暂无我的订单数据' });
    }
  });
};

const routeLabels: Record<string, string> = {
  home: '订单查询',
  login: '登录',
  register: '注册',
  'change-password': '修改密码',
  'order-management': '订单管理',
  'user-management': '用户管理',
  'content-management': '内容管理',
};

const routeActions: Record<string, () => void> = {
  home: () => navigateTo('home'),
  login: () => navigateTo('login'),
  register: () => navigateTo('register'),
  'change-password': () => navigateTo('change-password'),
  'order-management': () => navigateTo('order-management'),
  'user-management': () => navigateTo('user-management'),
  'content-management': () => navigateTo('content-management'),
};

type HeaderMenuItem = { label: string; key?: string | number; ariaLabel?: string; action?: () => void };

const MAX_DESKTOP_MENU_ITEMS = 5;
const desktopMaxItems = ref(MAX_DESKTOP_MENU_ITEMS);

const rawMenuItems = computed(() => {
  const items: Array<{ label: string; key: string; action: () => void }> = [];
  const seen = new Set<string>();
  const push = (item: { label: string; key: string; action: () => void } | null | undefined) => {
    if (!item || seen.has(item.key)) return;
    seen.add(item.key);
    items.push(item);
  };

  const current = currentRouteName.value;
  const currentKey = routeKeyMap[current] || current;
  if (routeLabels[currentKey]) {
    push({ label: routeLabels[currentKey], key: currentKey, action: routeActions[currentKey] || (() => {}) });
  }

  const orderQuery = { label: '订单查询', key: 'home', action: () => navigateTo('home') };
  const loginItem = { label: '登录', key: 'login', action: () => navigateTo('login') };
  const registerItem = { label: '注册', key: 'register', action: () => navigateTo('register') };
  const changePasswordItem = { label: '修改密码', key: 'change-password', action: () => navigateTo('change-password') };
  const logoutItem = { label: '退出登录', key: 'logout', action: () => { window.location.href = '/logout.html'; } };
  const adminLinks = adminMenuItems.value;

  if (current !== 'home') push(orderQuery);

  if (current === 'home') {
    if (isLoggedIn.value) {
      push({ label: '我的订单', key: 'my-orders', action: scrollToMyOrders });
      adminLinks.forEach(push);
    } else {
      push(loginItem);
      push(registerItem);
    }
  } else if (current === 'login') {
    push(registerItem);
  } else if (current === 'register') {
    push(loginItem);
  } else if (['order-management', 'user-management', 'content-management'].includes(current)) {
    push(orderQuery);
    adminLinks.forEach(push);
  } else if (current === 'change-password') {
    push(orderQuery);
    adminLinks.forEach(push);
  } else if (isLoggedIn.value) {
    adminLinks.forEach(push);
  }

  if (isLoggedIn.value) {
    push(changePasswordItem);
    push(logoutItem);
  }

  return items;
});

const dockItems = computed(() => rawMenuItems.value.map(item => ({
  label: item.label,
  key: item.key,
  ariaLabel: item.label,
  action: item.action,
})));

const primaryItem = computed(() => dockItems.value[0] ?? null);
const extraItems = computed(() => dockItems.value.slice(1));

const desktopVisibleDockItems = computed(() => {
  if (isMobile.value) return [];
  const items = dockItems.value;
  if (!items.length) return [];
  const limit = Math.max(0, desktopMaxItems.value || 0);
  return limit > 0 ? items.slice(0, limit) : [];
});

const desktopOverflowItems = computed(() => {
  if (isMobile.value) return [];
  const items = dockItems.value;
  const limit = Math.max(0, desktopMaxItems.value || 0);
  if (limit === 0 || items.length <= limit) return [];
  return items.slice(limit);
});

const hasDesktopOverflow = computed(() => desktopOverflowItems.value.length > 0);

const desktopActiveKey = computed(() => {
  const activeKey = activeNavKey.value;
  if (desktopVisibleDockItems.value.some(item => (item.key ?? item.label) === activeKey)) {
    return activeKey;
  }
  return desktopVisibleDockItems.value[0]?.key ?? activeKey;
});

const routeKeyMap: Record<string, string> = {
  home: 'home',
  login: 'login',
  register: 'register',
  'change-password': 'change-password',
  'order-management': 'order-management',
  'user-management': 'user-management',
  'content-management': 'content-management',
};

const activeNavKey = computed(() => routeKeyMap[currentRouteName.value] || 'home');

const contacts = computed(() => siteMeta.contacts.map((contact, index) => ({ ...contact, key: contact.label || String(index) })));

const closeContacts = () => {
  contactsOpen.value = false;
};

const computeDesktopMenuLimit = (width: number) => {
  if (width >= 1500) return 7;
  if (width >= 1320) return 6;
  if (width >= 1120) return 5;
  if (width >= 940) return 4;
  return 3;
};

const updateLayoutMode = () => {
  let width = 1280;
  if (typeof window !== 'undefined') {
    width = window.innerWidth || width;
  }
  if (mobileQuery) {
    isMobile.value = mobileQuery.matches;
  } else if (typeof window !== 'undefined') {
    isMobile.value = width <= 720;
  } else {
    isMobile.value = false;
  }
  if (isMobile.value) {
    desktopMaxItems.value = 0;
  } else {
    desktopMaxItems.value = computeDesktopMenuLimit(width);
  }
};

const handlePrimaryClick = () => {
  const item = primaryItem.value;
  if (item?.action) {
    try {
      item.action();
    } catch (error) {
      console.warn(error);
    }
  }
  mobileMenuOpen.value = false;
};

const toggleMobileMenu = () => {
  if (!extraItems.value.length && !contacts.value.length) return;
  mobileMenuOpen.value = !mobileMenuOpen.value;
  if (mobileMenuOpen.value) {
    contactsOpen.value = false;
    desktopOverflowOpen.value = false;
  }
};

const handleTouchStart = (event: TouchEvent) => {
  if (!isMobile.value || event.touches.length !== 1 || mobileMenuOpen.value) {
    touchState.active = false;
    return;
  }
  touchState.active = true;
  touchState.triggered = false;
  touchState.startY = event.touches[0].clientY;
  touchState.startScroll = typeof window !== 'undefined' ? (window.scrollY || document.documentElement.scrollTop || 0) : 0;
};

const handleTouchMove = (event: TouchEvent) => {
  if (!touchState.active || touchState.triggered || !isMobile.value || mobileMenuOpen.value) return;
  if (event.touches.length !== 1) return;
  const currentY = event.touches[0].clientY;
  const delta = currentY - touchState.startY;
  const scrollTop = typeof window !== 'undefined' ? (window.scrollY || document.documentElement.scrollTop || 0) : 0;
  if (scrollTop <= 2 && touchState.startScroll <= 2 && delta >= overscrollTriggerDistance) {
    if (extraItems.value.length || contacts.value.length) {
      mobileMenuOpen.value = true;
      contactsOpen.value = false;
      desktopOverflowOpen.value = false;
      touchState.triggered = true;
      touchState.active = false;
    }
  }
};

const handleTouchEnd = () => {
  touchState.active = false;
};

const selectMobileItem = (item: HeaderMenuItem) => {
  mobileMenuOpen.value = false;
  try {
    item.action?.();
  } catch (error) {
    console.warn(error);
  }
};

const toggleDesktopOverflow = () => {
  if (!desktopOverflowItems.value.length) return;
  desktopOverflowOpen.value = !desktopOverflowOpen.value;
  if (desktopOverflowOpen.value) {
    contactsOpen.value = false;
    mobileMenuOpen.value = false;
  }
};

const selectDesktopOverflowItem = (item: HeaderMenuItem) => {
  desktopOverflowOpen.value = false;
  try {
    item.action?.();
  } catch (error) {
    console.warn(error);
  }
};

const handleGlobalPointer = (event: Event) => {
  const target = event.target as Node | null;

  if (contactsOpen.value) {
    const panel = contactPanelRef.value;
    if (!(panel && (target === panel || (target && panel.contains(target))))) {
      contactsOpen.value = false;
    }
  }

  if (mobileMenuOpen.value) {
    const menu = mobileMenuRef.value;
    if (!(menu && (target === menu || (target && menu.contains(target))))) {
      mobileMenuOpen.value = false;
    }
  }

  if (desktopOverflowOpen.value) {
    const overflow = desktopOverflowRef.value;
    if (!(overflow && (target === overflow || (target && overflow.contains(target))))) {
      desktopOverflowOpen.value = false;
    }
  }
};

const toggleContacts = () => {
  contactsOpen.value = !contactsOpen.value;
  if (contactsOpen.value) {
    mobileMenuOpen.value = false;
    desktopOverflowOpen.value = false;
  }
};

const onDockSelect = (payload: { index: number }) => {
  // highlight handled internally; nothing else required yet
};

const onScroll = () => {
  try {
    isScrolled.value = (window.scrollY || window.pageYOffset || 0) > 12;
  } catch {
    isScrolled.value = false;
  }
};

watch([contactsOpen, mobileMenuOpen, desktopOverflowOpen], ([contacts, menu, overflow]) => {
  const shouldListen = contacts || menu || overflow;
  if (shouldListen) {
    document.addEventListener('pointerdown', handleGlobalPointer);
  } else {
    document.removeEventListener('pointerdown', handleGlobalPointer);
  }
});

watch(isMobile, value => {
  if (!value) {
    mobileMenuOpen.value = false;
  } else {
    contactsOpen.value = false;
  }
  if (value) {
    desktopOverflowOpen.value = false;
  }
});

watch(extraItems, items => {
  if (!items.length) mobileMenuOpen.value = false;
});

watch(desktopOverflowItems, items => {
  if (!items.length) desktopOverflowOpen.value = false;
});

watch(() => route.value?.name, () => {
  mobileMenuOpen.value = false;
  desktopOverflowOpen.value = false;
});

onMounted(() => {
  if (!siteMeta.loaded) {
    fetchSiteMeta().catch(() => {});
  }
  onScroll();
  if (typeof window !== 'undefined') {
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', updateLayoutMode);
    window.addEventListener('touchstart', handleTouchStart, { passive: true });
    window.addEventListener('touchmove', handleTouchMove, { passive: true });
    window.addEventListener('touchend', handleTouchEnd, { passive: true });
    window.addEventListener('touchcancel', handleTouchEnd, { passive: true });
    mobileQuery = window.matchMedia('(max-width: 720px)');
    if (mobileQuery.addEventListener) mobileQuery.addEventListener('change', updateLayoutMode);
    else mobileQuery.addListener(updateLayoutMode);
    updateLayoutMode();
  } else {
    updateLayoutMode();
  }
});

onUnmounted(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('scroll', onScroll);
    window.removeEventListener('resize', updateLayoutMode);
    window.removeEventListener('touchstart', handleTouchStart);
    window.removeEventListener('touchmove', handleTouchMove);
    window.removeEventListener('touchend', handleTouchEnd);
    window.removeEventListener('touchcancel', handleTouchEnd);
  }
  document.removeEventListener('pointerdown', handleGlobalPointer);
  if (mobileQuery) {
    if (mobileQuery.removeEventListener) mobileQuery.removeEventListener('change', updateLayoutMode);
    else mobileQuery.removeListener(updateLayoutMode);
    mobileQuery = null;
  }
});
</script>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 40;
  backdrop-filter: blur(18px) saturate(1.35);
  -webkit-backdrop-filter: blur(18px) saturate(1.35);
  background: rgba(7, 11, 19, 0.55);
  border-bottom: 1px solid rgba(255, 255, 255, 0.14);
  box-shadow: 0 14px 28px rgba(0, 0, 0, 0.32);
  transition: background 220ms ease, border-color 220ms ease, box-shadow 220ms ease;
}

.app-header.scrolled {
  background: rgba(7, 11, 19, 0.78);
  border-bottom-color: rgba(255, 255, 255, 0.2);
  box-shadow: 0 18px 38px rgba(0, 0, 0, 0.42);
}

.app-header.menu-open {
  background: rgba(7, 11, 19, 0.82);
  box-shadow: 0 22px 44px rgba(0, 0, 0, 0.46);
}

.header-container {
  max-width: 1200px;
  margin: 0 auto;
  height: 64px;
  padding: 0 24px;
  display: grid;
  grid-template-columns: 150px 1fr 140px;
  align-items: center;
  gap: 12px;
  box-sizing: border-box;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.brand:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px rgba(39, 255, 100, 0.45);
  border-radius: 12px;
}

.brand-logo {
  height: 34px;
  width: auto;
  object-fit: contain;
}

.nav-wrap {
  display: flex;
  justify-content: center;
}

.desktop-nav {
  display: flex;
  align-items: center;
  gap: 12px;
}

.desktop-overflow {
  position: relative;
  display: flex;
  align-items: center;
}

.desktop-overflow-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 12px;
  border: 1px solid rgba(148, 205, 255, 0.35);
  background: rgba(10, 18, 30, 0.62);
  color: #e4ecf7;
  cursor: pointer;
  transition: transform 180ms ease, border-color 200ms ease, background 200ms ease;
}

.desktop-overflow-btn:hover,
.desktop-overflow-btn:focus-visible,
.desktop-overflow-btn[aria-expanded='true'] {
  transform: translateY(-1px);
  border-color: rgba(102, 212, 255, 0.62);
  background: rgba(16, 28, 46, 0.8);
  outline: none;
}

.overflow-icon {
  width: 20px;
  height: 20px;
}

.desktop-overflow-panel {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  min-width: 160px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  border-radius: 14px;
  border: 1px solid rgba(102, 212, 255, 0.26);
  background: rgba(10, 20, 34, 0.92);
  box-shadow: 0 16px 38px rgba(6, 18, 38, 0.42);
  z-index: 30;
}

.desktop-overflow-item {
  text-align: left;
  border: 1px solid transparent;
  border-radius: 10px;
  padding: 8px 12px;
  background: transparent;
  color: #e6f3ff;
  font-weight: 600;
  letter-spacing: 0.32px;
  cursor: pointer;
  transition: background 200ms ease, border-color 200ms ease, transform 160ms ease;
}

.desktop-overflow-item:hover,
.desktop-overflow-item:focus-visible {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.28), rgba(37, 211, 164, 0.24));
  border-color: rgba(102, 212, 255, 0.5);
  transform: translateY(-1px);
  outline: none;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.mobile-nav-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-height: 60px;
  overflow: hidden;
  transition: max-height 240ms ease, padding 240ms ease;
}

.mobile-nav-container.open {
  max-height: calc(100vh - 40px);
  padding-bottom: 12px;
}

.mobile-nav {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  justify-content: space-between;
}

.current-pill {
  min-width: 120px;
  padding: 9px 18px;
  border-radius: 999px;
  border: 1px solid rgba(102, 212, 255, 0.35);
  background: linear-gradient(135deg, rgba(32, 123, 255, 0.38), rgba(39, 255, 160, 0.28));
  box-shadow: 0 16px 32px rgba(12, 68, 138, 0.3);
  color: #f4fbff;
  font-weight: 700;
  letter-spacing: 0.4px;
  cursor: pointer;
  transition: transform 180ms ease, box-shadow 220ms ease;
  margin-right: auto;
}

.current-pill:hover,
.current-pill:focus-visible {
  transform: translateY(-1px);
  box-shadow: 0 20px 40px rgba(12, 68, 138, 0.38);
  outline: none;
}

.mobile-toggle {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 999px;
  border: 1px solid rgba(148, 205, 255, 0.4);
  background: rgba(10, 18, 30, 0.65);
  color: #e5f2ff;
  cursor: pointer;
  transition: transform 180ms ease, border-color 200ms ease, background 200ms ease;
}

.mobile-toggle:hover,
.mobile-toggle:focus-visible,
.mobile-toggle[aria-expanded='true'] {
  transform: translateY(-1px);
  border-color: rgba(102, 212, 255, 0.65);
  background: rgba(16, 30, 48, 0.78);
  outline: none;
}

.toggle-icon {
  width: 20px;
  height: 20px;
}

.mobile-menu-panel {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-top: 4px;
}

.mobile-menu-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.mobile-menu-section.contacts {
  border-top: 1px solid rgba(148, 205, 255, 0.12);
  padding-top: 12px;
}

.mobile-menu-subtitle {
  font-size: 0.82rem;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  color: rgba(203, 223, 255, 0.75);
}

.mobile-menu-item {
  width: 100%;
  text-align: left;
  border: 1px solid rgba(102, 212, 255, 0.24);
  border-radius: 12px;
  padding: 10px 14px;
  background: rgba(12, 24, 40, 0.68);
  color: #e6f2ff;
  font-weight: 600;
  letter-spacing: 0.35px;
  cursor: pointer;
  transition: background 200ms ease, border-color 200ms ease, transform 160ms ease;
}

.mobile-menu-item:hover,
.mobile-menu-item:focus-visible {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.32), rgba(37, 211, 164, 0.26));
  border-color: rgba(102, 212, 255, 0.6);
  transform: translateY(-1px);
  outline: none;
}

.mobile-contact-list {
  list-style: none;
  margin: 0;
  padding: 4px 0 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mobile-contact-list li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  color: #e4ecf7;
}

.drawer-slide-enter-active,
.drawer-slide-leave-active {
  transform-origin: top;
  transition: transform 220ms ease, opacity 200ms ease;
}

.drawer-slide-enter-from,
.drawer-slide-leave-to {
  transform: scaleY(0.85);
  opacity: 0;
}

.actions {
  display: flex;
  justify-content: flex-end;
}

.contact-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(10, 18, 28, 0.55);
  color: #e5f2ff;
  cursor: pointer;
  font-weight: 600;
  letter-spacing: 0.3px;
  transition: border-color 200ms ease, background 200ms ease, transform 200ms ease;
}

.contact-btn .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #27ff64;
  box-shadow: 0 0 9px rgba(39, 255, 100, 0.6);
}

.contact-btn:hover,
.contact-btn:focus-visible {
  border-color: rgba(39, 255, 100, 0.65);
  background: rgba(12, 22, 34, 0.72);
  outline: none;
}

.contact-panel {
  position: absolute;
  right: 24px;
  top: 72px;
  width: min(320px, 80vw);
  background: rgba(10, 15, 24, 0.88);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 18px;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.42);
  backdrop-filter: blur(22px) saturate(1.4);
  -webkit-backdrop-filter: blur(22px) saturate(1.4);
  padding: 18px 20px;
  z-index: 60;
}

.contact-pop-enter-active,
.contact-pop-leave-active {
  transition: opacity 200ms ease, transform 220ms ease;
}

.contact-pop-enter-from,
.contact-pop-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.98);
}

.contact-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.contact-item {
  display: flex;
  gap: 12px;
  align-items: center;
  color: #e4ecf7;
}

.contact-icon {
  font-size: 1.2rem;
}

.contact-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.contact-text .label {
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  color: rgba(180, 196, 215, 0.9);
}

.contact-text .value {
  font-size: 0.95rem;
  color: #f6f9ff;
  text-decoration: none;
}

.contact-text .value:hover {
  text-decoration: underline;
}

@media (max-width: 860px) {
  .header-container {
    grid-template-columns: 140px 1fr;
    grid-template-rows: auto auto;
    height: auto;
    padding: 12px 18px;
  }
  .actions {
    grid-column: 1 / -1;
    justify-content: flex-end;
    margin-top: 12px;
  }
}

@media (max-width: 640px) {
  .header-container {
    grid-template-columns: 1fr;
    row-gap: 14px;
    text-align: center;
  }
  .brand {
    justify-content: center;
  }
  .nav-wrap {
    justify-content: center;
  }
  .mobile-nav-container { align-items: stretch; }
  .mobile-nav { justify-content: space-between; }
  .actions {
    justify-content: center;
  }
  .contact-panel {
    right: 50%;
    transform: translateX(50%);
  }
}
</style>
