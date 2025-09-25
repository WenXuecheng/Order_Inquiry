import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  base: '/',   // 仓库名，注意大小写
  plugins: [vue()],
})
