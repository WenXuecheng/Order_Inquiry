<template>
  <div>
    <LiquidEther
      v-if="showEffects"
      :style="{ position: 'fixed', inset: '0', zIndex: 0 }"
      class-name="w-full h-full"
      :colors="['#5caeff','#6fe7c0','#1a1e2f']"
      :resolution="isMobile ? 0.25 : 0.35"
      :autoDemo="false"
      :cursorSize="isMobile ? 80 : 110"
      :mouseForce="isMobile ? 12 : 16"
    />
    <SplashCursor
      v-if="showEffects"
      :SIM_RESOLUTION="isMobile ? 48 : 64"
      :DYE_RESOLUTION="isMobile ? 512 : 720"
      :CAPTURE_RESOLUTION="256"
      :DENSITY_DISSIPATION="3.0"
      :VELOCITY_DISSIPATION="1.8"
      :SPLAT_RADIUS="isMobile ? 0.16 : 0.14"
      :SPLAT_FORCE="isMobile ? 2200 : 3200"
      :SHADING="true"
      :COLOR_UPDATE_SPEED="8"
      :TRANSPARENT="true"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue';
import LiquidEther from '../vue_bits/Backgrounds/LiquidEther/LiquidEther.vue';
import SplashCursor from '../vue_bits/Animations/SplashCursor/SplashCursor.vue';

const isMobile = computed(() => (typeof window !== 'undefined') ? window.innerWidth <= 768 : false);
const prefersReduced = (typeof window !== 'undefined' && 'matchMedia' in window) ? window.matchMedia('(prefers-reduced-motion: reduce)').matches : false;
const showEffects = ref(!prefersReduced);
function handleVisibility(){
  if (typeof document !== 'undefined') {
    showEffects.value = !prefersReduced && document.visibilityState === 'visible';
  }
}
onMounted(() => { if (typeof document !== 'undefined') document.addEventListener('visibilitychange', handleVisibility, { passive: true }); });
onUnmounted(() => { if (typeof document !== 'undefined') document.removeEventListener('visibilitychange', handleVisibility); });
</script>


