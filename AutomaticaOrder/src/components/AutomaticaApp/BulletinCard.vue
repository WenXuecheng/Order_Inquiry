<template>
  <section>
    <h2>{{ state.bulletin.title || '公告栏' }}</h2>
    <div v-html="state.bulletin.html"></div>
  </section>
</template>

<script setup>
import { onMounted, reactive } from 'vue';
import { useBulletin } from '../../composables/useBulletin';
const { bulletin, load } = useBulletin();
const state = reactive({ bulletin });
onMounted(() => load());
</script>

