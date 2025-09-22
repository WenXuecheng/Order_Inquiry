<template>
  <section class="card">
    <h2 class="title small">{{ state.bulletin.title || '公告栏' }}</h2>
    <div class="bulletin" v-html="state.bulletin.html"></div>
  </section>
</template>

<script setup>
import { onMounted, reactive } from 'vue';
import { useBulletin } from '../../composables/useBulletin';
const { bulletin, load } = useBulletin();
const state = reactive({ bulletin });
onMounted(() => load());
</script>

<style scoped>
.bulletin img, .bulletin video, .bulletin iframe { max-width:100%; height:auto; border-radius:8px; display:block; margin:8px 0; }
.title.small { font-size: 18px; margin: 4px 0 10px; }
</style>

