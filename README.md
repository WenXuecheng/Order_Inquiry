# Order Inquiry (Automatica)

前后端分离：前端静态页（仓库根目录），后端 FastAPI（`backend/`）。

- 后端依赖与部署：见 `backend/README.md`
- 前端发布与配置：根目录 `config.js` 中设置 `API_BASE_URL`（必须 https）
- 已加固传输安全：
  - 前端设置 CSP：`upgrade-insecure-requests; block-all-mixed-content`
  - 若页面为 https，会自动将 `API_BASE_URL` 从 http 升级为 https
  - 后端支持 `FORCE_HTTPS=true` 中间件，配合 Nginx/证书启用
