# Automatica Order 前端

基于 Vue 3 + Vite 的查询与管理员后台界面。默认主题与交互动效已配置完成，可直接与 `backend/` 提供的 Tornado API 协作。

## 开发环境

- Node.js 18 或更高版本
- npm 9+

### 启动本地调试

```bash
cd AutomaticaOrder
npm install
npm run dev -- --host
```

开发服务器默认指向 `https://api.wen-xc.site`。如需指向本地/测试后端，可在 `index.html` 中添加：

```html
<script>window.API_BASE_URL = 'https://api.example.com';</script>
```

请确保该脚本位于 `<script type="module" src="/src/main.js"></script>` 之前，以便在运行时覆盖默认地址。

### 构建静态资源

```bash
npm run build
```

构建产物输出至 `dist/`，可部署到任意静态托管服务。项目内置 `npm run deploy`（使用 `gh-pages`）用于发布到 GitHub Pages。

### 生产部署要点

- 发布前根据环境设置 `window.API_BASE_URL` 指向你的 HTTPS API 域名。
- 建议在静态托管中单独提供一个 `config.js` 或变体 `<script>`，方便在不同环境下覆盖 API 地址。
- 若与其他站点共用 Nginx，请保留各自的 `server`/`location`，将本应用构建的静态文件托管在独立路径或子域。
