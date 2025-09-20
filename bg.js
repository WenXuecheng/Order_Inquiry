(() => {
  const prefersReduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d', { alpha: true });
  Object.assign(canvas.style, {
    position: 'fixed',
    inset: '0',
    width: '100%',
    height: '100%',
    zIndex: '0',
    pointerEvents: 'none',
    opacity: '0',
    transition: 'opacity .28s ease',
  });

  let W = 0, H = 0, running = false, raf = 0;
  let resizeRaf = 0, resizeTs = 0;
  const RESIZE_THROTTLE_MS = 220;
  const SIZE_EPS = 20; // ignore tiny address-bar height jitters on mobile

  function applyResize(init = false) {
    const newW = Math.floor(window.innerWidth);
    const newH = Math.floor(window.innerHeight);
    const needReinit = init || Math.abs(newW - W) > SIZE_EPS || Math.abs(newH - H) > SIZE_EPS;
    W = newW; H = newH;
    canvas.width = Math.floor(W * dpr);
    canvas.height = Math.floor(H * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    if (needReinit) initOrbs();
  }

  function cssVar(name, fallback) {
    try { return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback; } catch { return fallback; }
  }

  const colorA = cssVar('--brand', '#67b8ff');
  const colorB = cssVar('--brand-2', '#7ae0b8');

  const MAX_ORBS = window.innerWidth > 1024 ?  NineOrbs() : 6; // noticeably more orbs on large screens
  function NineOrbs(){ return 9; }
  const orbs = [];

  function rnd(a, b) { return a + Math.random() * (b - a); }

  function initOrbs() {
    orbs.length = 0;
    for (let i = 0; i < MAX_ORBS; i++) {
      const r = rnd(220, 420); // much larger radius for bigger coverage
      orbs.push({
        x: rnd(-r, W + r),
        y: rnd(-r, H + r),
        r,
        // much faster motion for more visible change
        vx: rnd(-0.6, 0.6) * (W / 580),
        vy: rnd(-0.5, 0.5) * (H / 580),
        hue: i % 2 === 0 ? colorA : colorB,
      });
    }
  }

  function step() {
    if (!running) return;
    ctx.clearRect(0, 0, W, H);
    ctx.globalCompositeOperation = 'lighter';

    for (const o of orbs) {
      // move
      o.x += o.vx;
      o.y += o.vy;
      // bounce softly outside edges
      const m = 260;
      if (o.x < -m || o.x > W + m) o.vx *= -1;
      if (o.y < -m || o.y > H + m) o.vy *= -1;

      const g = ctx.createRadialGradient(o.x, o.y, 0, o.x, o.y, o.r);
      g.addColorStop(0, `${o.hue}66`); // brighter core
      g.addColorStop(0.35, `${o.hue}33`);
      g.addColorStop(1, '#00000000');
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(o.x, o.y, o.r, 0, Math.PI * 2);
      ctx.fill();
    }

    raf = requestAnimationFrame(step);
  }

  function start() {
    if (running || prefersReduced) return;
    running = true;
    raf = requestAnimationFrame(step);
  }

  function stop() {
    running = false;
    if (raf) cancelAnimationFrame(raf);
  }

  function mount() {
    // Insert as first child to keep behind content
    document.body.insertBefore(canvas, document.body.firstChild || null);
    applyResize(true);
    if (!prefersReduced) start();
  }

  function onResize() {
    const now = performance.now();
    if (now - resizeTs < RESIZE_THROTTLE_MS) {
      if (!resizeRaf) resizeRaf = requestAnimationFrame(() => {
        resizeRaf = 0; resizeTs = performance.now(); applyResize(false);
      });
      return;
    }
    resizeTs = now;
    applyResize(false);
  }
  window.addEventListener('resize', onResize, { passive: true });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) stop(); else start();
  });

  function fadeInOnce() {
    // reveal after first paint to avoid flash during load/refresh
    if (canvas.style.opacity !== '1') canvas.style.opacity = '1';
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => { mount(); requestAnimationFrame(fadeInOnce); });
  } else {
    mount(); requestAnimationFrame(fadeInOnce);
  }
})();
