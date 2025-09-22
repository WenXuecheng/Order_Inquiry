<template>
  <section class="bulletin-wrap">
    <div class="bulletin-title title-wrap">
      <span class="title-fallback">{{ state.bulletin.title || '公告栏' }}</span>
    </div>
    <div class="bulletin-html" v-html="state.bulletin.html"></div>
  </section>
  
</template>

<script setup>
import { onMounted, reactive } from 'vue';
import { useBulletin } from '../../composables/useBulletin';
const { bulletin, load } = useBulletin();
const state = reactive({ bulletin });
onMounted(() => load());
</script>
<style>
.bulletin-wrap { width: 100%; box-sizing: border-box; overflow-x: hidden; }
.bulletin-title { margin: 0 0 4px; padding-left: 8px; }
.title-fallback { font-size: 20px; font-weight: 800; letter-spacing: 0.5px; color: var(--text); }
.bulletin-html { color: #d1d5db; font-size: 14px; line-height: 1.7; }
.bulletin-html a { color: #7ef6b1; text-decoration: none; }
.bulletin-html a:hover { text-decoration: underline; }
</style>
