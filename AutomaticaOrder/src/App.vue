<template>
  <div>
    <BackgroundEffects />
    <template v-if="isAdmin">
      <div style="position: relative; z-index: 1">
        <AdminHeader />
        <main>
          <div class="app-container">
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
                <component :is="currentAdminComp" @logged-in="onLoggedIn" />
              </FadeContent>
            </GlassSurface>
          </div>
        </main>
      </div>
    </template>
    <template v-else>
      <div style="position: relative; z-index: 1">
        <AppHeader />
        <main>
          <div class="app-container">
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
              <FadeContent :blur="true" :duration="900" :threshold="0.15" :delay="100">
                <OrdersCard :state="ordersState" />
              </FadeContent>
            </GlassSurface>
          </div>
        </main>
      </div>
    </template>
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
import AdminHeader from './components/AdminPages/AdminHeader.vue';
import AdminLogin from './components/AdminPages/AdminLogin.vue';
import AdminDashboard from './components/AdminPages/AdminDashboard.vue';
import { useOrders } from './composables/useOrders';
import { getToken, getRole } from './composables/useAdminApi';

const ordersState = useOrders();
const { code, totals, orders, loading } = ordersState;
const isAdmin = (typeof window !== 'undefined') ? (window.APP_MODE === 'admin' || /\/admin\.html?$/.test(window.location.pathname)) : false;
const isLoggedIn = (typeof window !== 'undefined') ? !!getToken() : false;
const currentAdminComp = computed(() => (isLoggedIn ? AdminDashboard : AdminLogin));
const adminRole = (typeof window !== 'undefined') ? (getRole() || '') : '';

function onLoggedIn(){
  try { window.location.reload(); } catch {}
}
async function onSearch(code){
  if (!code) return;
  try {
    const url = new URL(window.location.href);
    url.searchParams.set('code', code);
    window.history.replaceState(null, '', url.toString());
  } catch {}
  await ordersState.search(code);
  try {
    const el = document.getElementById('orders-card');
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch {}
}

onMounted(() => {
  const p = new URLSearchParams(location.search);
  const init = p.get('code');
  if (init) ordersState.search(init);
});
</script>
