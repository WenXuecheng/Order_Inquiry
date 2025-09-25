<template>
  <teleport to="body">
    <div class="bgfx-root">
      <div class="bgfx-gradient" />
      <div class="bgfx-overlay" />
      <LightRaysBackground class-name="absolute inset-0" :raysColor="'#46ffaf'" :lightSpread="1.2" :rayLength="2.4" :noiseAmount="0.08" :saturation="1.15" :mouseInfluence="0.15" />
    </div>
  </teleport>
</template>

<script setup>
import LightRaysBackground from './LightRaysBackground.vue';
</script>

<style>
.bgfx-root {
  position: fixed;
  inset: 0;
  width: 100vw;
  width: 100dvw;
  height: 100vh;
  height: 100dvh;
  z-index: 0;
  pointer-events: none;
  transform: translateZ(0);
  overflow: hidden;
}

.bgfx-gradient {
  position: absolute;
  inset: -12%;
  background:
    radial-gradient(circle at 15% 18%, rgba(59, 130, 246, 0.32) 0%, rgba(59, 130, 246, 0) 60%),
    radial-gradient(circle at 82% 22%, rgba(39, 255, 160, 0.26) 0%, rgba(39, 255, 160, 0) 58%),
    radial-gradient(circle at 44% 88%, rgba(139, 92, 246, 0.2) 0%, rgba(139, 92, 246, 0) 60%),
    radial-gradient(circle at 66% 68%, rgba(14, 165, 233, 0.22) 0%, rgba(14, 165, 233, 0) 62%);
  filter: blur(160px);
  animation: gradient-shift 32s ease-in-out infinite alternate;
}

.bgfx-overlay {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 48% -12%, rgba(102, 212, 255, 0.2), transparent 62%),
    radial-gradient(circle at 20% 110%, rgba(39, 255, 160, 0.16), transparent 60%),
    linear-gradient(200deg, rgba(5, 10, 16, 0.78), rgba(5, 11, 20, 0.72));
  mix-blend-mode: normal;
  opacity: 0.78;
  animation: overlay-pulse 26s ease-in-out infinite alternate;
}

.bgfx-overlay::after {
  content: '';
  position: absolute;
  inset: 0;
  background:
    linear-gradient(
      to bottom,
      rgba(4, 9, 15, 0) 0%,
      rgba(4, 9, 15, 0.2) 45%,
      rgba(4, 9, 15, 0.55) 70%,
      rgba(4, 9, 15, 0.82) 100%
    );
  pointer-events: none;
}

@keyframes gradient-shift {
  0% {
    transform: scale(1) translate3d(0, 0, 0);
  }
  50% {
    transform: scale(1.1) translate3d(-2%, -1%, 0);
  }
  100% {
    transform: scale(1.15) translate3d(2%, 1%, 0);
  }
}

@keyframes overlay-pulse {
  0% {
    opacity: 0.55;
  }
  50% {
    opacity: 0.7;
  }
  100% {
    opacity: 0.6;
  }
}
</style>
