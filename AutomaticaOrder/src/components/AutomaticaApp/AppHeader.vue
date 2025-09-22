<template>
  <header>
    <div>
      <div>
        <ShinyText text="订单查询" :speed="5" class-name="header-title" />
      </div>
      <nav>
        <a href="/admin.html" target="_self">管理员登录</a>
      </nav>
    </div>
  </header>
</template>

<script setup>
import ShinyText from '../vue_bits/TextAnimations/ShinyText/ShinyText.vue';
</script>

<style>
.header-title { font-size: 22px; font-weight: 800; letter-spacing: .5px; color: transparent; -webkit-text-fill-color: transparent; }
</style>
