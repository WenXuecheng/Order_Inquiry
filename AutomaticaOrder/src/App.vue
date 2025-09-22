<template>
  <div>
    <AppHeader />
    <main>
      <BulletinCard />
      <SearchCard @search="onSearch" />
      <OrdersCard :state="ordersState" />
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import AppHeader from './components/AutomaticaApp/AppHeader.vue';
import BulletinCard from './components/AutomaticaApp/BulletinCard.vue';
import SearchCard from './components/AutomaticaApp/SearchCard.vue';
import OrdersCard from './components/AutomaticaApp/OrdersCard.vue';
import { useOrders } from './composables/useOrders';

const ordersState = useOrders();
function onSearch(code){ ordersState.search(code); }

onMounted(() => {
  const p = new URLSearchParams(location.search);
  const init = p.get('code');
  if (init) ordersState.search(init);
});
</script>

<style scoped>
</style>
