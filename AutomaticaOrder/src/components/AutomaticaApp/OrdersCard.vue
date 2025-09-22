<template>
  <section class="card">
    <div class="results-header">
      <h2 class="title small">查询结果</h2>
      <div class="loading" v-if="state.loading">加载中...</div>
    </div>
    <div class="error" v-if="state.error">{{ state.error }}</div>
    <div class="empty" v-if="!state.loading && !state.error && state.orders.length === 0">暂无订单，请尝试其它编号。</div>
    <div class="orders">
      <div class="order" v-for="o in state.orders" :key="o.id" @click="o.__open = !o.__open" tabindex="0" @keydown.enter.prevent="o.__open = !o.__open" @keydown.space.prevent="o.__open = !o.__open">
        <div class="row">
          <div>
            <div class="muted">订单号</div>
            <div style="font-weight:600">{{ o.order_no }}</div>
          </div>
          <div class="chip" :class="{ ok: o.status === STATUSES[STATUSES.length-1] }">{{ o.status }}</div>
        </div>

        <template v-if="o.__open">
          <div class="row"><div class="muted">编号</div><div>{{ o.group_code || '' }}</div></div>
          <div class="row"><div class="muted">重量</div><div>{{ (o.weight_kg||0).toFixed(2) }} kg</div></div>
          <div class="row"><div class="muted">是否打木架</div><div>{{ o.wooden_crate == null ? '未设置' : (o.wooden_crate ? '是' : '否') }}</div></div>
          <div class="flow" aria-label="订单进度">
            <div v-for="(s,i) in STATUSES" :key="s" class="step" :class="{ active: i <= statusIndex(o.status) }"><div class="dot"></div><div class="label">{{ s }}</div></div>
          </div>
          <div class="row"><div class="muted">更新</div><div>{{ fmtDate(o.updated_at) }}</div></div>
        </template>
      </div>
    </div>
  </section>
</template>

<script setup>
import { STATUSES, statusIndex, fmtDate } from '../../composables/useOrders';
defineProps({ state: { type: Object, required: true } });
</script>

<style scoped>
.results-header { display:flex; align-items:center; justify-content: space-between; }
.orders { display:grid; grid-template-columns: 1fr; gap:12px; }
.order { display:grid; gap:8px; padding:14px; border-radius:12px; background:#0b0f16; border:1px solid #182031; }
.order:hover { border-color:#24314a; }
.row { display:flex; align-items:center; justify-content: space-between; gap:8px; }
.chip { padding:4px 8px; border-radius:999px; border:1px solid #26324a; color:#a3a7b3; font-size:12px; }
.chip.ok { border-color:#194530; color:#a2f5c4; }
.muted { color:#a3a7b3; font-size:13px; }
.error { background:#160b0b; border:1px solid #3a1717; color:#ffb9b9; border-radius:10px; padding:10px; }
.empty { color:#a3a7b3; text-align:center; padding:20px; }
.loading { color:#a3a7b3; }
.flow { display:grid; gap:10px; grid-template-columns: repeat(7, minmax(90px, 1fr)); align-items: stretch; }
.step { position:relative; padding:10px; background:#0b0f16; border:1px solid #182031; border-radius:12px; text-align:center; display:flex; flex-direction:column; justify-content:center; }
.step .dot { width:10px; height:10px; border-radius:50%; margin:0 auto 6px; background:#26324a; box-shadow:0 0 0 2px #182031; }
.step.active .dot { background:#7ae0b8; box-shadow:0 0 0 4px rgba(122,224,184,.2), 0 0 20px rgba(122,224,184,.4); }
.step .label { font-size:12px; color:#a3a7b3; white-space:normal; word-break:break-word; }
</style>

