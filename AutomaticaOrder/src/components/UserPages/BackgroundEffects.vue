<template>
  <teleport to="body">
    <div class="bgfx-root">
      <DarkVeil
        :hue-shift="0"
        :noise-intensity="0.06"
        :scanline-intensity="0.08"
        :scanline-frequency="1.0"
        :warp-amount="0.05"
        :speed="0.6"
        :resolution-scale="1"
        :style="{ position: 'absolute', inset: '0', width: '100%', height: '100%' }"
      />
    </div>
  </teleport>
</template>

<script setup>
import DarkVeil from '../vue_bits/Backgrounds/DarkVeil/DarkVeil.vue';
</script>

<style>
.bgfx-root {
  position: fixed;
  inset: 0;
  width: 100vw;
  width: 100dvw; /* cover dynamic viewport width if supported */
  height: 100vh;
  height: 100dvh; /* cover dynamic viewport on mobile */
  z-index: 0;
  pointer-events: none;
  transform: translateZ(0);
  overflow: hidden;
}
</style>
