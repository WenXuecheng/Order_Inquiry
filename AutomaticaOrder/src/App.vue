<template>
  <div class="app-shell">
    <BackgroundEffects />
    <NotificationHost />
    <AppHeader />
    <transition :name="pageTransition" mode="out-in">
      <div class="page-layer" :key="routeName">
        <main>
          <div class="app-container">
            <template v-if="isOrderManagement">
              <FadeContent :blur="true" :duration="800" :threshold="0.15">
                <OrderManagement />
              </FadeContent>
            </template>

            <template v-else-if="isUserManagement">
              <GlassSurface
                class-name="card"
                :width="'100%'"
                :height="'auto'"
                :background-opacity="0.12"
                :blur="8"
                :saturation="1.4"
                simple
                :center-content="false"
                :content-padding="8"
              >
                <FadeContent :blur="true" :duration="850" :threshold="0.15" :delay="60">
                  <AdminUsers />
                </FadeContent>
              </GlassSurface>
            </template>

            <template v-else-if="isContentManagement">
              <FadeContent :blur="true" :duration="850" :threshold="0.15" :delay="60">
                <ContentManagement />
              </FadeContent>
            </template>

            <template v-else-if="isRegisterRoute">
              <FadeContent :blur="true" :duration="850" :threshold="0.15" :delay="60">
                <RegisterStepper @logged-in="onLoggedIn" />
              </FadeContent>
            </template>

            <template v-else-if="isLoginRoute">
              <GlassSurface
                class-name="card"
                :width="'100%'"
                :height="'auto'"
                :background-opacity="0.12"
                :blur="8"
                :saturation="1.4"
                simple
                :center-content="false"
                :content-padding="8"
              >
                <FadeContent :blur="true" :duration="850" :threshold="0.15" :delay="60">
                  <UserAuthCard initial-mode="login" :show-switch="false" @logged-in="onLoggedIn" @logged-out="onLoggedOut" />
                </FadeContent>
              </GlassSurface>
            </template>

            <template v-else>
              <GlassSurface
                class-name="card"
                :width="'100%'"
                :height="'auto'"
                :background-opacity="0.12"
                :blur="8"
                :saturation="1.4"
                simple
                :center-content="false"
                :content-padding="8"
              >
                <FadeContent :blur="true" :duration="800" :threshold="0.15">
                  <BulletinCard />
                </FadeContent>
              </GlassSurface>

              <template v-if="isLoggedIn">
                <GlassSurface
                  class-name="card"
                  :width="'100%'"
                  :height="'auto'"
                  :background-opacity="0.12"
                  :blur="8"
                  :saturation="1.4"
                  simple
                  :center-content="false"
                  :content-padding="12"
                  id="my-orders"
                >
                  <FadeContent :blur="true" :duration="860" :threshold="0.15" :delay="70">
                    <MyOrdersCard />
                  </FadeContent>
                </GlassSurface>
                <GlassSurface
                  class-name="card"
                  :width="'100%'"
                  :height="'auto'"
                  :background-opacity="0.12"
                  :blur="8"
                  :saturation="1.4"
                  simple
                  :center-content="false"
                  :content-padding="16"
                >
                  <FadeContent :blur="true" :duration="850" :threshold="0.15" :delay="100">
                    <SearchCard
                      v-model:code="code"
                      :totals="totals"
                      :orders="orders"
                      :loading="loading"
                      @search="onSearch"
                    />
                  </FadeContent>
                </GlassSurface>
              </template>
              <template v-else>
                <GlassSurface
                  class-name="card"
                  :width="'100%'"
                  :height="'auto'"
                  :background-opacity="0.12"
                  :blur="8"
                  :saturation="1.4"
                  simple
                  :center-content="false"
                  :content-padding="16"
                >
                  <FadeContent :blur="true" :duration="850" :threshold="0.15" :delay="60">
                    <SearchCard
                      v-model:code="code"
                      :totals="totals"
                      :orders="orders"
                      :loading="loading"
                      @search="onSearch"
                    />
                  </FadeContent>
                </GlassSurface>
              </template>

              <GlassSurface
                class-name="card"
                :width="'100%'"
                :height="'auto'"
                :background-opacity="0.1"
                :blur="7"
                :saturation="1.3"
                simple
                :center-content="false"
                :content-padding="12"
                id="orders-card"
              >
                <FadeContent :blur="true" :duration="900" :threshold="0.15" :delay="120">
                  <OrdersCard :state="ordersState" />
                </FadeContent>
              </GlassSurface>
            </template>
          </div>
        </main>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { onMounted, computed } from 'vue';
import AppHeader from './components/UserPages/AppHeader.vue';
import BulletinCard from './components/UserPages/BulletinCard.vue';
import SearchCard from './components/UserPages/SearchCard.vue';
import OrdersCard from './components/UserPages/OrdersCard.vue';
import BackgroundEffects from './components/UserPages/BackgroundEffects.vue';
import GlassSurface from './components/vue_bits/Components/GlassSurface/GlassSurface.vue';
import FadeContent from './components/vue_bits/Animations/FadeContent/FadeContent.vue';
import UserAuthCard from './components/UserPages/UserAuthCard.vue';
import RegisterStepper from './components/UserPages/RegisterStepper.vue';
import MyOrdersCard from './components/UserPages/MyOrdersCard.vue';
import OrderManagement from './components/AdminPages/OrderManagement.vue';
import ContentManagement from './components/AdminPages/ContentManagement.vue';
import NotificationHost from './components/common/NotificationHost.vue';
import AdminUsers from './components/AdminPages/AdminUsers.vue';
import { useOrders } from './composables/useOrders';
import { useAuthState } from './composables/useAuthState';
import { useCurrentRoute } from './router/useSimpleRouter';

const ordersState = useOrders();
const { code, totals, orders, loading } = ordersState;
const route = useCurrentRoute();
const routeName = computed(() => route.value?.name || 'home');
const isOrderManagement = computed(() => routeName.value === 'order-management');
const isUserManagement = computed(() => routeName.value === 'user-management');
const isContentManagement = computed(() => routeName.value === 'content-management');
const isRegisterRoute = computed(() => routeName.value === 'register');
const isLoginRoute = computed(() => routeName.value === 'login');
const { isLoggedIn } = useAuthState();

const pageTransition = computed(() => {
  if (isOrderManagement.value || isUserManagement.value || isContentManagement.value) return 'page-slide';
  if (isLoginRoute.value || isRegisterRoute.value) return 'page-zoom';
  return 'page-fade';
});

function onLoggedIn() {
  try {
    if (code.value) {
      ordersState.search(code.value);
    }
  } catch {}
}

function onLoggedOut() {
  try {
    orders.splice(0, orders.length);
    Object.assign(totals, { count: 0, total_weight: 0, total_shipping_fee: 0 });
  } catch {}
}

async function onSearch(searchCode) {
  if (!searchCode) return;
  try {
    const url = new URL(window.location.href);
    url.searchParams.set('code', searchCode);
    window.history.replaceState(null, '', url.toString());
  } catch {}
  await ordersState.search(searchCode);
  try {
    const el = document.getElementById('orders-card');
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch {}
}

onMounted(() => {
  const params = new URLSearchParams(location.search);
  const init = params.get('code');
  if (init) ordersState.search(init);
});
</script>

<style>
.app-shell {
  position: relative;
  min-height: 100vh;
  color: var(--text);
}

.page-layer {
  position: relative;
  z-index: 1;
}

.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 260ms ease, transform 260ms ease;
}

.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
  transform: translateY(16px) scale(0.97);
}

.page-slide-enter-active,
.page-slide-leave-active {
  transition: opacity 280ms ease, transform 320ms ease;
}

.page-slide-enter-from,
.page-slide-leave-to {
  opacity: 0;
  transform: translateY(24px);
}

.page-zoom-enter-active,
.page-zoom-leave-active {
  transition: opacity 280ms ease, transform 300ms ease;
}

.page-zoom-enter-from,
.page-zoom-leave-to {
  opacity: 0;
  transform: scale(0.96);
}

</style>
