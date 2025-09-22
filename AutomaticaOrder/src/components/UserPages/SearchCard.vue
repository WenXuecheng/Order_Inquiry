<template>
  <section>
    <div class="title-wrap">
      <span class="title-fallback">查询订单</span>
    </div>
    <p>输入编号获取所属订单；输入 <strong>A</strong> 查看未分类订单</p>
    <div class="stack">
      <input
        class="input"
        :value="code"
        @input="onInput"
        placeholder="输入编号，如 A666"
        maxlength="40"
        @keydown.enter="emitSearch"
      />
      <button class="btn-gradient-text" :disabled="loading" @click="emitSearch">{{ loading ? '查询中…' : '查询' }}</button>
    </div>
    
  </section>
  
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  code: { type: String, default: '' },
  totals: { type: Object, default: () => ({}) },
  orders: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
});

const emit = defineEmits(['search', 'update:code']);

const statsVisible = computed(() => ((props.totals?.count || 0) > 0) || (props.orders?.length || 0) > 0);

function onInput(e){
  emit('update:code', (e?.target?.value || '').trim());
}
function emitSearch(){ emit('search', props.code?.trim?.() || ''); }
</script>

<style>
.title-wrap { margin: 0 0 4px; }
.title-fallback { font-size: 20px; font-weight: 800; letter-spacing: 0.5px; color: var(--text); }


</style>
