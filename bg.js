(() => {
  const prefersReduced = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  let userOverride = null;
  try { userOverride = localStorage.getItem('bg_anim'); } catch {}
  const allowAnim = (userOverride === 'on') || (!prefersReduced && userOverride !== 'off');

  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const canvas = document.createElement('canvas');
  // Use opaque canvas to avoid Safari compositing flashes
  const ctx = canvas.getContext('2d', { alpha: false, desynchronized: true });
  Object.assign(canvas.style, {
    position: 'fixed',
    inset: '0',
    width: '100%',
    height: '100%',
    zIndex: '0',
    pointerEvents: 'none',
    opacity: '0',
    transition: 'opacity .28s ease',
    willChange: 'opacity, transform',
    contain: 'strict',
  });
  // Promote to its own compositor layer on Safari/iOS
  canvas.style.webkitTransform = 'translateZ(0)';

  let W = 0, H = 0, running = false, raf = 0;
  let resizeRaf = 0, resizeTs = 0;
  const RESIZE_THROTTLE_MS = 260;
  const HEIGHT_EPS = 120; // ignore address-bar jitters on iOS Safari
  const WIDTH_EPS = 60;   // resize only on notable width change
  let initialW = 0, initialH = 0;
  let orientationChanged = false;

  function applyResize(init = false) {
    const newW = Math.floor(window.innerWidth);
    const newH = Math.floor(window.innerHeight);
    // Freeze height to initial to avoid flash on top bounce; allow width change/rotation to reinit
    const widthChanged = Math.abs(newW - initialW) > WIDTH_EPS || orientationChanged || init;
    const heightChanged = Math.abs(newH - initialH) > HEIGHT_EPS;
    const needReinit = init || widthChanged || heightChanged;
    W = widthChanged ? newW : initialW;
    H = (heightChanged || init || orientationChanged) ? newH : initialH;
    canvas.width = Math.floor(W * dpr);
    canvas.height = Math.floor(H * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    if (needReinit) initOrbs();
    if (init) { initialW = W; initialH = H; orientationChanged = false; }
  }

  function cssVar(name, fallback) {
    try { return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback; } catch { return fallback; }
  }

  const colorA = cssVar('--brand', '#67b8ff');
  const colorB = cssVar('--brand-2', '#7ae0b8');
  const bgColor = cssVar('--bg', '#0b0c10');
  canvas.style.backgroundColor = bgColor || '#0b0c10';

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
    // Fill instead of clear to avoid transient transparency
    ctx.fillStyle = bgColor || '#0b0c10';
    ctx.fillRect(0, 0, W, H);
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
      g.addColorStop(0, `${o.hue}88`); // brighter core
      g.addColorStop(0.35, `${o.hue}44`);
      g.addColorStop(1, '#00000000');
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(o.x, o.y, o.r, 0, Math.PI * 2);
      ctx.fill();
    }

    raf = requestAnimationFrame(step);
  }

  function startAnim() {
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
    if (allowAnim) startAnim();
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
  window.addEventListener('orientationchange', () => { orientationChanged = true; applyResize(true); }, { passive: true });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) { stop(); }
    else { if (allowAnim) startAnim(); if (canvas.style.opacity !== '1') canvas.style.opacity = '1'; }
  });

  function fadeInOnce() {
    // reveal after first paint to avoid flash during load/refresh
    if (canvas.style.opacity !== '1') canvas.style.opacity = '1';
  }
  // Prefer waiting for full load on Safari to avoid initial layout jumps
  const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
  const boot = () => { mount(); requestAnimationFrame(() => { setTimeout(fadeInOnce, isSafari ? 120 : 0); }); };
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    boot();
  } else {
    const ev = isSafari ? 'load' : 'DOMContentLoaded';
    window.addEventListener(ev, boot, { once: true });
  }
})();
