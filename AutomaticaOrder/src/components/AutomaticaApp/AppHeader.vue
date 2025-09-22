<template>
  <header class="site-header">
    <div class="container header-inner">
      <div class="brand">
        <span class="logo-circle" aria-hidden="true"></span>
        <span class="brand-text">订单查询</span>
      </div>
      <nav class="nav">
        <a class="nav-link" href="/admin.html" target="_self">管理员登录</a>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.site-header { position: sticky; top:0; background: rgba(13,16,24,.35); backdrop-filter: blur(12px) saturate(140%); border-bottom: 1px solid rgba(255,255,255,.06); box-shadow: 0 1px 0 rgba(255,255,255,.04) inset, 0 6px 20px rgba(0,0,0,.25); z-index: 2; }
.container { width: min(1100px, 92vw); margin: 0 auto; }
.header-inner { display:flex; align-items:center; justify-content: space-between; padding:14px 0; }
.brand { display:flex; align-items:center; gap:10px; font-weight:600; }
.logo-circle { width:14px; height:14px; border-radius:50%; background: radial-gradient(circle at 30% 30%, #67b8ff, #7ae0b8); box-shadow: 0 0 18px rgba(103,184,255,.5); }
.nav-link { color: #e6e7eb; opacity:.9; text-decoration:none; padding:6px 10px; border-radius:8px; }
.nav-link:hover { background: rgba(26,28,36,.5); }
</style>

