<template>
  <div :class="['sticky-header', { scrolled: isScrolled }]" style="position: sticky; top: 0; z-index: 20; height: 64px; width: 100%">
    <div class="header-container">
      <StaggeredMenu
        :items="menuItems"
        :socialItems="socials"
        :colors="['transparent', 'transparent']"
        :menuButtonColor="'#fff'"
        :openMenuButtonColor="'#fff'"
        :accentColor="'#27FF64'"
        :displaySocials="false"
        :logoUrl="logoUrl"
        class-name="w-full h-16"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue';
import StaggeredMenu from '../vue_bits/Components/StaggeredMenu/StaggeredMenu.vue';
import { getToken, getRole } from '../../composables/useAdminApi';

const isLoggedIn = computed(() => { try { return !!getToken(); } catch { return false; } });
const role = computed(() => { try { return getRole() || ''; } catch { return ''; } });
const isAdminPage = computed(() => { try { return (window.APP_MODE === 'admin') || /\/admin\.html$/.test(window.location.pathname || ''); } catch { return true; } });

const menuItems = computed(() => {
  const items = [];
  // 避免重复：在后台页面不显示“后台登录/后台管理”入口
  if (!isAdminPage.value && (role.value === 'admin' || role.value === 'superadmin')) {
    items.push({ label: '后台管理', ariaLabel: '后台管理', link: '/admin.html' });
  }
  items.push({ label: '返回用户端', ariaLabel: '返回用户端', link: '/' });
  if (isLoggedIn.value) {
    items.push({ label: '退出登录', ariaLabel: '退出登录', link: '/logout.html' });
  } else if (!isAdminPage.value) {
    items.push({ label: '登录', ariaLabel: '登录', link: '/login.html?redirect=/' });
  }
  return items;
});

const socials = [];
const logoUrl = '/src/assets/header-title.svg';

const isScrolled = ref(false);
function onScroll(){
  try { isScrolled.value = (window.scrollY || window.pageYOffset || 0) > 20; } catch { isScrolled.value = false; }
}
onMounted(() => {
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });
});
onUnmounted(() => window.removeEventListener('scroll', onScroll));
</script>

<style>
/* 半透明背景 + 玻璃模糊 + 阴影，增强层次 */
.sticky-header {
  background: rgba(5, 5, 8, 0.38);
  backdrop-filter: blur(10px) saturate(1.3);
  -webkit-backdrop-filter: blur(10px) saturate(1.3);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
}
.sticky-header.scrolled {
  background: rgba(5, 5, 8, 0.58);
  backdrop-filter: blur(12px) saturate(1.5);
  -webkit-backdrop-filter: blur(12px) saturate(1.5);
  border-bottom-color: rgba(255, 255, 255, 0.12);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35);
}
/* 顶栏容器：居中且左右留白 */
.header-container { height: 100%; max-width: 1200px; margin: 0 auto; padding: 0 24px; position: relative; }

/* 让抽屉面板占满视口，避免只占 64px 导致显示不完整 */
.sm-scope .staggered-menu-panel {
  position: fixed !important;
  top: 0 !important;
  right: 0 !important;
  height: 100vh !important;
  width: min(420px, 90vw) !important;
  left: auto !important;
  box-sizing: border-box !important;
  z-index: 100 !important;
  /* Glass (frosted) effect — match other glass surfaces */
  background: rgba(255, 255, 255, 0.08) !important;
  backdrop-filter: blur(10px) saturate(1.6) brightness(1.1) !important;
  -webkit-backdrop-filter: blur(10px) saturate(1.6) brightness(1.1) !important;
  border: 1px solid rgba(255, 255, 255, 0.20) !important;
  box-shadow:
    inset 0 1px 0 0 rgba(255, 255, 255, 0.20),
    inset 0 -1px 0 0 rgba(255, 255, 255, 0.10),
    0 8px 24px rgba(0,0,0,0.28);
}

/* 预渲染彩层固定在右侧，与面板同高同宽，不覆盖全屏 */
.sm-scope .sm-prelayers {
  position: fixed !important;
  top: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  width: min(420px, 90vw) !important;
  pointer-events: none !important;
  z-index: 95 !important;
}
.sm-scope .sm-prelayer { position: absolute !important; inset: 0 !important; }

/* 顶栏内边距/高度微调，使用外层容器控制左右留白 */
.sm-scope .staggered-menu-header {
  padding: 0 !important;
  height: 64px !important;
  align-items: center !important;
  z-index: 150 !important; /* ensure over prelayers */
}

/* 给右侧按钮留出缓冲，防止靠边看起来被裁切 */
.sm-scope .sm-toggle { padding: 6px 8px !important; margin-right: 0 !important; }

/* ensure good contrast on glass panel */
.sm-scope .sm-panel-item { color: #ffffff !important; }
.sm-scope .sm-socials-title { color: #7ef6b1 !important; }
.sm-scope .sm-socials-link { color: #e5e7eb !important; }

/* 小屏下适当收紧边距，避免拥挤 */
@media (max-width: 640px) {
  .header-container { padding: 0 16px; }
  .sm-scope .staggered-menu-header { padding: 0 !important; }
  .sm-scope .sm-toggle { margin-right: 0 !important; }
}

/* 防止打开菜单时左侧 Logo 被强制反色（来自组件内部样式） */
.sm-scope .staggered-menu-wrapper[data-open] .sm-logo-img { filter: none !important; }
</style>
