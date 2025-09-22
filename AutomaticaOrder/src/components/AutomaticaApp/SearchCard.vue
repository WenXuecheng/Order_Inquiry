<template>
  <section>
    <h1>查询订单</h1>
    <p>输入编号获取所属订单；输入 <strong>A</strong> 查看未分类订单</p>
    <div>
      <input v-model.trim="code" placeholder="输入编号，如 A666" maxlength="40" @keydown.enter="emitSearch" />
      <button @click="emitSearch">查询</button>
    </div>
    <div v-if="statsVisible">
      <div>总件数：{{ totals.count }}</div>
      <div>总重量：{{ (totals.total_weight||0).toFixed(2) }} kg</div>
      <div>运费：{{ (totals.total_shipping_fee||0).toFixed(2) }}</div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue';
import { useOrders } from '../../composables/useOrders';
const emit = defineEmits(['search']);
const { code, totals, orders } = useOrders();
const statsVisible = computed(() => (totals.count || orders.length) > 0);
function emitSearch(){ emit('search', code.value); }
</script>

<style scoped>
</style>
