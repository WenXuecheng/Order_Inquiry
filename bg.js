(() => {
  const prefersReduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d', { alpha: true });
  Object.assign(canvas.style, {
    position: 'fixed', inset: '0', width: '100%', height: '100%',
    zIndex: '0', pointerEvents: 'none'
  });

  let W = 0, H = 0, running = false, raf = 0;

  function resize() {
    W = Math.floor(window.innerWidth);
    H = Math.floor(window.innerHeight);
    canvas.width = Math.floor(W * dpr);
    canvas.height = Math.floor(H * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function cssVar(name, fallback) {
    try { return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback; } catch { return fallback; }
  }

  function hexToRgba(hex, a) {
    const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    if (!m) return `rgba(103,184,255,${a||0.3})`;
    const r = parseInt(m[1],16), g = parseInt(m[2],16), b = parseInt(m[3],16);
    return `rgba(${r},${g},${b},${a==null?0.3:a})`;
  }

  const colorA = cssVar('--brand', '#67b8ff');
  const colorB = cssVar('--brand-2', '#7ae0b8');

  const waves = [];
  function initWaves() {
    waves.length = 0;
    const n = W > 1024 ? 4 : 3;
    for (let i = 0; i < n; i++) {
      waves.push({
        amp: 20 + i*8 + Math.random()*12,              // 振幅
        freq: 1.5 + i*0.35,                            // 频率（每屏宽波峰数）
        phase: Math.random()*Math.PI*2,                // 初始相位
        speed: 0.4 + i*0.12,                           // 相位速度（秒）
        baseY: H*(0.25 + i*0.18),                      // 基线高度
        width: 36 + i*10,                              // 光带厚度（使用阴影模拟）
        color: i%2===0 ? colorA : colorB,
        alpha: 0.22 - i*0.03,
        blur: 40 + i*12,
      });
    }
  }

  function yAt(wv, x, t) {
    const k = (x / W) * (Math.PI*2) * wv.freq + (t * wv.speed) + wv.phase;
    return wv.baseY + Math.sin(k) * wv.amp;
  }

  let t0 = 0;
  function step(ts) {
    if (!running) return;
    if (!t0) t0 = ts; const t = (ts - t0)/1000;

    ctx.clearRect(0, 0, W, H);
    ctx.globalCompositeOperation = 'lighter';

    for (const wv of waves) {
      ctx.save();
      ctx.lineWidth = wv.width;
      ctx.strokeStyle = hexToRgba(wv.color, wv.alpha);
      ctx.shadowColor = hexToRgba(wv.color, Math.min(wv.alpha*1.6, 0.5));
      ctx.shadowBlur = wv.blur;

      const stepX = Math.max(6, Math.min(14, Math.round(W/120)));
      ctx.beginPath();
      ctx.moveTo(0, yAt(wv, 0, t));
      for (let x=stepX; x<=W; x+=stepX) {
        ctx.lineTo(x, yAt(wv, x, t));
      }
      ctx.stroke();
      ctx.restore();
    }

    raf = requestAnimationFrame(step);
  }

  function start() { if (running || prefersReduced) return; running = true; raf = requestAnimationFrame(step); }
  function stop() { running = false; if (raf) cancelAnimationFrame(raf); }

  function mount() {
    document.body.insertBefore(canvas, document.body.firstChild || null);
    resize();
    initWaves();
    if (!prefersReduced) start();
  }

  window.addEventListener('resize', () => { resize(); initWaves(); });
  document.addEventListener('visibilitychange', () => { if (document.hidden) stop(); else start(); });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
})();
