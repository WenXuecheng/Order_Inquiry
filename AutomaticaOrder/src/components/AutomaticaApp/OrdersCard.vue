<template>
  <section>
    <div>
      <h2>查询结果</h2>
      <div v-if="isLoading">加载中...</div>
    </div>
    <div v-if="errorText">{{ errorText }}</div>
    <div v-if="!isLoading && !errorText && state.orders.length === 0">暂无订单，请尝试其它编号。</div>
    <div>
      <div v-for="o in state.orders" :key="o.id" @click="o.__open = !o.__open" tabindex="0" @keydown.enter.prevent="o.__open = !o.__open" @keydown.space.prevent="o.__open = !o.__open">
        <div>
          <div>订单号</div>
          <div>{{ o.order_no }} （状态：{{ o.status }}）</div>
        </div>

        <template v-if="o.__open">
          <div>编号：{{ o.group_code || '' }}</div>
          <div>重量：{{ (o.weight_kg||0).toFixed(2) }} kg</div>
          <div>是否打木架：{{ o.wooden_crate == null ? '未设置' : (o.wooden_crate ? '是' : '否') }}</div>
          <div>
            订单进度：
            <span v-for="(s,i) in STATUSES" :key="s">
              <span :style="{ fontWeight: i <= statusIndex(o.status) ? '600' : '400' }">{{ s }}</span>
              <span v-if="i < STATUSES.length-1"> → </span>
            </span>
          </div>
          <div>更新：{{ fmtDate(o.updated_at) }}</div>
        </template>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue';
import { STATUSES, statusIndex, fmtDate } from '../../composables/useOrders';
const props = defineProps({ state: { type: Object, required: true } });

const isLoading = computed(() => {
  const l = props.state.loading;
  return typeof l === 'boolean' ? l : !!(l && l.value);
});

const errorText = computed(() => {
  const e = props.state.error;
  if (typeof e === 'string') return e;
  return e && e.value ? String(e.value) : '';
});
</script>
