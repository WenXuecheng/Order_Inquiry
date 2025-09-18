# Automatica 订单查询系统

前端静态站点（GitHub Pages）+ 后端 FastAPI（Ubuntu）+ MySQL。

## 功能概述

- 订单查询：输入编号，返回该编号全部订单（订单号、重量、更新日期、状态）
- 特殊编号：输入 A 返回未分类订单（`group_code` 为空或空串）
- 统计信息：总件数、总重量、运费（优先使用每单 `shipping_fee`；否则按 `RATE_PER_KG * weight_kg` 计算）
- 物流流程：7 个固定状态的可视化步进
- 管理员：登录、编辑订单、修改所属编号、批量 Excel 导入

## 后端部署（Ubuntu）

1) 系统依赖

```bash
sudo apt update && sudo apt install -y python3-pip python3-venv
```

2) 代码与环境

```bash
cd ~/apps/automatica-backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example .env
```

设置 `.env`：

- `DATABASE_URL=mysql+pymysql://user:pass@host:3306/automatica`
- `CORS_ALLOW_ORIGINS=https://<username>.github.io`（或你的静态站点域名）
- `JWT_SECRET=<安全随机值>`
- `ADMIN_USERNAME` 与 `ADMIN_PASSWORD_HASH`（推荐）或 `ADMIN_PASSWORD`（仅开发环境）
- `RATE_PER_KG`（当订单未设置运费时的计算单价）

3) 启动（开发）

```bash
export $(grep -v '^#' .env | xargs -d '\n')
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --proxy-headers
```

4) 生产运行（systemd + Nginx + HTTPS）

- 使用 `uvicorn` 或 `gunicorn -k uvicorn.workers.UvicornWorker` 作为服务
- Nginx 反向代理到 `127.0.0.1:8000` 并启用 HTTPS（Let's Encrypt/Certbot）
- 设置 `FORCE_HTTPS=true` 以在应用层强制 HTTPS（需配合 `--proxy-headers`）
- `CORS_ALLOW_ORIGINS` 建议仅允许你的 HTTPS 前端域名

Nginx 参考配置（片段）：

```nginx
server {
  listen 80;
  server_name api.example.com;
  return 301 https://$host$request_uri;
}

server {
  listen 443 ssl http2;
  server_name api.example.com;

  ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;
  add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

使用 systemd 启动（示例）：

```ini
[Service]
Environment=FORCE_HTTPS=true
EnvironmentFile=/home/ubuntu/apps/automatica-backend/.env
ExecStart=/home/ubuntu/apps/automatica-backend/.venv/bin/uvicorn backend.main:app \
          --host 127.0.0.1 --port 8000 --proxy-headers
```

## 数据库

初次运行会自动 `create_all` 创建表 `orders`。

表结构（简要）：

- id: int PK
- order_no: str 唯一
- group_code: str 可空（编号）
- weight_kg: float 可空
- shipping_fee: float 可空
- status: str（限定 7 种状态）
- updated_at/created_at: datetime

## API 概览

- `POST /api/login` 登录（返回 JWT）
- `GET  /api/orders?code=编号` 查询订单（编号为 `A` 返回未分类）
- `GET  /api/orders/by-no/{order_no}` 根据订单号查询
- `PUT  /api/orders/by-no/{order_no}` 更新订单（需 Bearer Token）
- `POST /api/import/excel` 上传 Excel（需 Bearer Token）

Excel 表头（首行）：`order_no, group_code, weight_kg, status, shipping_fee`

## 前端部署（GitHub Pages）

本仓库已将前端静态文件放在仓库根目录（`index.html`, `admin.html`, `styles.css`, `config.js`, `app.js`, `admin.js`）。

- 若使用 Pages 指向仓库根目录，直接启用即可。
- 或者将根目录内容推送到 `gh-pages` 分支。
- 在 `config.js` 设置：

```js
window.API_BASE_URL = "https://api.example.com"; // 你的后端域名（必须 https）
```

并在页面默认 CSP 中已启用 `upgrade-insecure-requests` 和 `block-all-mixed-content`，可自动升级偶发的 http 资源。

## 安全建议

- 使用强随机 `JWT_SECRET`
- 生产环境必须使用 `ADMIN_PASSWORD_HASH`（bcrypt）
- 仅允许可信静态站点域名通过 CORS
- 在 Nginx 层限制上传大小，开启 HTTPS
- 生产环境启用 `FORCE_HTTPS=true`，并确保 Nginx 设置 `X-Forwarded-Proto`
