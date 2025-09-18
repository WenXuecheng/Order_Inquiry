# Automatica 订单查询系统

前端静态站点（GitHub Pages）+ 后端 Tornado（Ubuntu）+ MySQL。

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
- `ADMIN_USERNAME` 与 `ADMIN_PASSWORD_HASH`（推荐，算法：pbkdf2_sha256）或 `ADMIN_PASSWORD`（仅开发环境）
- `RATE_PER_KG`（当订单未设置运费时的计算单价）

3) 启动（开发，Tornado）

```bash
export $(grep -v '^#' .env | xargs -d '\n')
python -m backend.server
```

4) 生产运行（systemd + Nginx + HTTPS）

- 使用 Tornado 原生进程（本项目提供 `python -m backend.server`）或通过 `supervisor/systemd` 管理
- Nginx 反向代理到 `127.0.0.1:8000` 并启用 HTTPS（Let's Encrypt/Certbot）
- 设置 `FORCE_HTTPS=true` 以在应用层强制 HTTPS（依赖 Nginx 传入 `X-Forwarded-Proto`）
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
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

使用 systemd 启动（示例）：

```ini
[Unit]
Description=Automatica Tornado API
After=network.target

[Service]
WorkingDirectory=/home/ubuntu/apps/automatica-backend
EnvironmentFile=/home/ubuntu/apps/automatica-backend/.env
Environment=FORCE_HTTPS=true
ExecStart=/home/ubuntu/apps/automatica-backend/.venv/bin/python -m backend.server
Restart=always
User=www-data

[Install]
WantedBy=multi-user.target
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

## 测试数据

- SQL 版（10 条，非测试标注）：`db/seed_demo_orders.sql`
  - 导入：`mysql -h <host> -u <user> -p automatica < db/seed_demo_orders.sql`

- CSV 版（10 条，带“TEST”标注）：`db/seed_demo_orders_test.csv`
  - 列：`order_no, group_code, weight_kg, status, shipping_fee`
  - 分组值含 `-TEST` 后缀（如 `A666-TEST`），订单号以 `TEST-` 开头，便于与正式数据区分
  - DBeaver 导入：右键表 orders → Import Data → CSV → 选择该文件 → 映射列 → 完成
  - MySQL 命令行导入（需开启 `LOCAL INFILE`）：
    ```sql
    LOAD DATA LOCAL INFILE 'db/seed_demo_orders_test.csv'
    INTO TABLE orders
    FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
    LINES TERMINATED BY '\n'
    IGNORE 1 LINES
    (order_no, group_code, weight_kg, status, shipping_fee);
    ```

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

## 安全与访问控制

- 使用强随机 `JWT_SECRET`
- 生产环境必须使用 `ADMIN_PASSWORD_HASH`（推荐 pbkdf2_sha256）
  - 本项目默认使用 `pbkdf2_sha256`（passlib 内置，无需额外依赖）。生成方式示例：
    ```python
    >>> from passlib.hash import pbkdf2_sha256
    >>> pbkdf2_sha256.hash("your-password")
    'pbkdf2_sha256$...'
    ```
- 仅允许可信静态站点域名通过 CORS
- 在 Nginx 层限制上传大小，开启 HTTPS
- 生产环境启用 `FORCE_HTTPS=true`，并确保 Nginx 设置 `X-Forwarded-Proto`

额外来源限制（后端 Tornado 实现）：
- 设置 `CORS_ALLOW_ORIGINS=https://your-pages-domain` 严格匹配前端域名
- 设置 `STRICT_ORIGIN=true`（默认启用）：除 `/api/health` 外，所有 API 请求必须带 `Origin` 且在白名单内，否则 403
- 结合 CORS 与服务器端 Origin 校验，可有效拒绝无 `Origin` 的直连脚本/curl 请求与跨域来源请求（注意：伪造 Origin 的自定义客户端仍可能绕过，必要时可叠加 WAF/速率限制/验证码）
