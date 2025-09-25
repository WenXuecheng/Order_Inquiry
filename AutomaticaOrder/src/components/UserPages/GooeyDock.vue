<template>
  <div class="dock-root" ref="containerRef">
    <nav class="dock-nav" :style="{ transform: 'translate3d(0,0,0.01px)' }">
      <ul ref="navRef" class="dock-list">
        <li
          v-for="(item, index) in items"
          :key="item.key || item.label || index"
          :class="['dock-item', { active: activeIndex === index }]"
        >
          <button
            type="button"
            class="dock-button"
            :aria-label="item.ariaLabel || item.label"
            @click="() => handleSelect(index)"
            @keydown="event => handleKeydown(event, index)"
          >
            <span class="dock-label">{{ item.label }}</span>
          </button>
        </li>
      </ul>
    </nav>
    <span class="effect filter" ref="filterRef" />
    <span class="effect text" ref="textRef" />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, useTemplateRef, watch } from 'vue';

interface DockItem {
  key?: string | number;
  label: string;
  ariaLabel?: string;
  action?: () => void;
}

interface DockProps {
  items: DockItem[];
  activeKey?: string | number | null;
  initialActiveIndex?: number;
  animationTime?: number;
  particleCount?: number;
  particleDistances?: [number, number];
  particleR?: number;
  timeVariance?: number;
  colors?: number[];
}

const props = withDefaults(defineProps<DockProps>(), {
  items: () => [],
  activeKey: null,
  initialActiveIndex: 0,
  animationTime: 600,
  particleCount: 14,
  particleDistances: () => [90, 12],
  particleR: 90,
  timeVariance: 320,
  colors: () => [1, 2, 3, 1, 4],
});

const emit = defineEmits<{
  (e: 'select', payload: { index: number; item: DockItem }): void;
}>();

const containerRef = useTemplateRef<HTMLDivElement>('containerRef');
const navRef = useTemplateRef<HTMLUListElement>('navRef');
const filterRef = useTemplateRef<HTMLSpanElement>('filterRef');
const textRef = useTemplateRef<HTMLSpanElement>('textRef');
const activeIndex = ref<number>(props.initialActiveIndex ?? 0);

const items = computed(() => props.items || []);
let resizeObserver: ResizeObserver | null = null;

const noise = (n = 1) => n / 2 - Math.random() * n;

const getXY = (distance: number, pointIndex: number, totalPoints: number): [number, number] => {
  const angle = ((360 + noise(6)) / totalPoints) * pointIndex * (Math.PI / 180);
  return [distance * Math.cos(angle), distance * Math.sin(angle)];
};

const createParticle = (i: number, baseTime: number, distances: [number, number], radius: number) => {
  const rotate = noise(radius / 8);
  return {
    start: getXY(distances[0], props.particleCount - i, props.particleCount),
    end: getXY(distances[1] + noise(6), props.particleCount - i, props.particleCount),
    time: baseTime,
    scale: 1 + noise(0.24),
    color: props.colors[Math.floor(Math.random() * props.colors.length)] ?? 1,
    rotate: rotate > 0 ? (rotate + radius / 20) * 8 : (rotate - radius / 20) * 8,
  };
};

const makeParticles = (element: HTMLElement) => {
  const distances: [number, number] = props.particleDistances;
  const radius = props.particleR;
  const bubbleTime = props.animationTime * 2 + props.timeVariance;
  element.style.setProperty('--time', `${bubbleTime}ms`);
  for (let i = 0; i < props.particleCount; i++) {
    const t = props.animationTime * 2 + noise(props.timeVariance * 2);
    const particle = createParticle(i, t, distances, radius);
    element.classList.remove('active');
    window.setTimeout(() => {
      const wrapper = document.createElement('span');
      const dot = document.createElement('span');
      wrapper.classList.add('particle');
      wrapper.style.setProperty('--start-x', `${particle.start[0]}px`);
      wrapper.style.setProperty('--start-y', `${particle.start[1]}px`);
      wrapper.style.setProperty('--end-x', `${particle.end[0]}px`);
      wrapper.style.setProperty('--end-y', `${particle.end[1]}px`);
      wrapper.style.setProperty('--time', `${particle.time}ms`);
      wrapper.style.setProperty('--scale', `${particle.scale}`);
      wrapper.style.setProperty('--color', `var(--color-${particle.color}, rgba(255,255,255,0.9))`);
      wrapper.style.setProperty('--rotate', `${particle.rotate}deg`);
      dot.classList.add('point');
      wrapper.appendChild(dot);
      element.appendChild(wrapper);
      requestAnimationFrame(() => {
        element.classList.add('active');
      });
      window.setTimeout(() => {
        try {
          element.removeChild(wrapper);
        } catch (error) {
          console.warn(error);
        }
      }, t);
    }, 30);
  }
};

const updateEffectPosition = (element: HTMLElement | null) => {
  if (!element || !containerRef.value || !filterRef.value || !textRef.value) return;
  const containerRect = containerRef.value.getBoundingClientRect();
  const rect = element.getBoundingClientRect();
  const styles: Record<string, string> = {
    left: `${rect.x - containerRect.x}px`,
    top: `${rect.y - containerRect.y}px`,
    width: `${rect.width}px`,
    height: `${rect.height}px`,
  };
  Object.assign(filterRef.value.style, styles);
  Object.assign(textRef.value.style, styles);
  textRef.value.innerText = element.innerText;
};

const activateIndex = (index: number) => {
  activeIndex.value = index;
  nextTick(() => {
    const li = navRef.value?.querySelectorAll('li')[index] as HTMLElement | undefined;
    if (!li) return;
    updateEffectPosition(li);
    if (textRef.value) {
      textRef.value.classList.remove('active');
      void textRef.value.offsetWidth;
      textRef.value.classList.add('active');
    }
    if (filterRef.value) {
      const particles = filterRef.value.querySelectorAll('.particle');
      particles.forEach(node => filterRef.value?.removeChild(node));
      makeParticles(filterRef.value);
    }
  });
};

const handleSelect = (index: number) => {
  const item = items.value[index];
  if (!item) return;
  if (activeIndex.value !== index) {
    activateIndex(index);
  }
  try {
    item.action?.();
  } catch (error) {
    console.warn(error);
  }
  emit('select', { index, item });
};

const handleKeydown = (event: KeyboardEvent, index: number) => {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    handleSelect(index);
  }
};

const syncActiveWithKey = () => {
  if (props.activeKey == null) return;
  const idx = items.value.findIndex(item => (item.key ?? item.label) === props.activeKey);
  if (idx >= 0 && idx !== activeIndex.value) {
    activateIndex(idx);
  }
};

watch(items, () => {
  nextTick(() => {
    const count = items.value.length;
    if (count === 0) return;
    if (activeIndex.value >= count) {
      activateIndex(Math.max(0, count - 1));
    } else {
      activateIndex(activeIndex.value);
    }
  });
});

watch(() => props.activeKey, () => syncActiveWithKey());

onMounted(() => {
  nextTick(() => {
    if (props.activeKey != null) {
      syncActiveWithKey();
    } else {
      activateIndex(Math.min(activeIndex.value, Math.max(items.value.length - 1, 0)));
    }
  });
  if (containerRef.value) {
    resizeObserver = new ResizeObserver(() => {
      const li = navRef.value?.querySelectorAll('li')[activeIndex.value] as HTMLElement | undefined;
      if (li) updateEffectPosition(li);
    });
    resizeObserver.observe(containerRef.value);
  }
});

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect();
    resizeObserver = null;
  }
});
</script>

<style scoped>
.dock-root {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 12px;
}

.dock-nav {
  position: relative;
  z-index: 3;
}

.dock-list {
  display: flex;
  gap: 18px;
  list-style: none;
  padding: 0 18px;
  margin: 0;
  color: white;
  text-shadow: 0 1px 1px rgba(22, 32, 46, 0.2);
}

.dock-item {
  position: relative;
  border-radius: 999px;
  cursor: pointer;
  transition: background-color 280ms ease, color 280ms ease, box-shadow 280ms ease;
  box-shadow: 0 0 0.5px 1.5px transparent;
}

.dock-item.active {
  color: #052033;
  text-shadow: none;
}

.dock-item::before,
.dock-item::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 999px;
  opacity: 0;
  transform: scale(0.7);
  transition: all 260ms ease;
  z-index: -2;
}
.dock-item::before {
  background: linear-gradient(135deg, rgba(32, 123, 255, 0.32), rgba(39, 255, 160, 0.28));
  box-shadow: 0 18px 36px rgba(12, 68, 138, 0.32);
  transform: scale(0.6) translateY(8px);
}
.dock-item::after {
  background: rgba(96, 210, 255, 0.28);
  z-index: -1;
}

.dock-item.active::before {
  opacity: 1;
  transform: scale(1) translateY(0);
}
.dock-item.active::after {
  opacity: 1;
  transform: scale(1);
}

.dock-button {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: inherit;
  font: inherit;
  padding: 0.65em 1.15em;
  border-radius: 999px;
  cursor: pointer;
  transition: transform 200ms ease, color 200ms ease;
  outline: none;
  -webkit-tap-highlight-color: transparent;
}

.dock-button:focus-visible {
  box-shadow: 0 0 0 2px rgba(39, 255, 100, 0.35);
}

.dock-item:not(.active):hover .dock-button {
  color: rgba(255, 255, 255, 0.8);
  transform: translateY(-1px);
}

.effect {
  position: absolute;
  pointer-events: none;
  display: grid;
  place-items: center;
  z-index: 2;
}

.effect.text {
  color: white;
  transition: color 0.28s ease;
}

.effect.text.active {
  color: #041016;
  text-shadow: none;
}

.effect.filter {
  filter: blur(12px) saturate(1.2);
  mix-blend-mode: screen;
}

.effect.filter::before {
  content: '';
  position: absolute;
  inset: -18px;
  z-index: -2;
  border-radius: 9999px;
  background: radial-gradient(circle at 50% 40%, rgba(20, 44, 68, 0.55), rgba(12, 28, 48, 0));
  box-shadow: 0 24px 48px rgba(2, 12, 24, 0.35);
}

.effect.filter::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(120deg, rgba(102, 212, 255, 0.55), rgba(39, 255, 160, 0.4));
  transform: scale(0.45);
  opacity: 0;
  z-index: -1;
  border-radius: 9999px;
}

.effect.active::after {
  animation: pill 320ms ease both;
}

@keyframes pill {
  to {
    transform: scale(1);
    opacity: 1;
  }
}

.particle,
.point {
  display: block;
  opacity: 0;
  width: 18px;
  height: 18px;
  border-radius: 9999px;
  transform-origin: center;
}

.particle {
  --time: 5s;
  position: absolute;
  top: calc(50% - 9px);
  left: calc(50% - 9px);
  animation: particle calc(var(--time)) ease 1 -350ms;
}

.point {
  background: var(--color);
  opacity: 1;
  animation: point calc(var(--time)) ease 1 -350ms;
}

@keyframes particle {
  0% {
    transform: rotate(0deg) translate(calc(var(--start-x)), calc(var(--start-y)));
    opacity: 1;
    animation-timing-function: cubic-bezier(0.55, 0, 1, 0.45);
  }
  70% {
    transform: rotate(calc(var(--rotate) * 0.5)) translate(calc(var(--end-x) * 1.2), calc(var(--end-y) * 1.2));
    opacity: 1;
    animation-timing-function: ease;
  }
  85% {
    transform: rotate(calc(var(--rotate) * 0.66)) translate(calc(var(--end-x)), calc(var(--end-y)));
    opacity: 1;
  }
  100% {
    transform: rotate(calc(var(--rotate) * 1.2)) translate(calc(var(--end-x) * 0.5), calc(var(--end-y) * 0.5));
    opacity: 1;
  }
}

@keyframes point {
  0% {
    transform: scale(0);
    opacity: 0;
    animation-timing-function: cubic-bezier(0.55, 0, 1, 0.45);
  }
  28% {
    transform: scale(calc(var(--scale) * 0.25));
  }
  40% {
    opacity: 1;
  }
  65% {
    transform: scale(var(--scale));
    opacity: 1;
    animation-timing-function: ease;
  }
  85% {
    transform: scale(var(--scale));
    opacity: 1;
  }
  100% {
    transform: scale(0);
    opacity: 0;
  }
}

@media (max-width: 720px) {
  .dock-list {
    gap: 12px;
    padding: 0 8px;
  }
  .dock-button {
    padding: 0.55em 0.8em;
    font-size: 0.92rem;
  }
}
</style>
