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
cp backend/.env.example backend/.env
```

数据库配置（默认优先读取 `backend/.env`，若不存在再尝试根目录 `.env`）

后端只从环境变量读取数据库配置，不再读取代码内配置，也不会使用内置默认值。你需要在 `.env` 中设置以下其一：

设置 `backend/.env`（推荐分字段配置，密码自动 URL 编码）：

```env
username="dbauser"
password="JHKDSJrShkjSsdfsd348958234/.$#@54"
host="localhost"      # 改为你的数据库地址
port=3306
database="testdb"
# 可选：driver="mysql+pymysql"  charset="utf8mb4"

# 也可直接使用完整 URL（如已习惯此方式），设置后会覆盖上面的分字段：
# DATABASE_URL=mysql+pymysql://user:password@host:3306/automatica?charset=utf8mb4

# 其他配置
CORS_ALLOW_ORIGINS=https://<username>.github.io
JWT_SECRET=<安全随机值>
JWT_EXPIRE_HOURS=12
ADMIN_USERNAME=admin
# 生产建议使用哈希：
# ADMIN_PASSWORD_HASH=
# 开发可用明文：
ADMIN_PASSWORD=admin123
RATE_PER_KG=0
```

3) 启动（开发，Tornado）

启动方式：使用提供的脚本（自动安全加载 .env）

```bash
bash scripts/run_backend_dev.sh
```

该脚本会：
- 切换到仓库根目录
- 以 set -a; source backend/.env; set +a 的方式加载环境变量（正确处理行尾注释与引号）
- 启动 `python -m backend.server`

4) 生产运行（systemd + Nginx + HTTPS）

- 使用 Tornado 原生进程（本项目提供 `python -m backend.server`）或通过 `supervisor/systemd` 管理
- Nginx 反向代理到 `127.0.0.1:8000` 并启用 HTTPS（Let's Encrypt/Certbot）
- 设置 `FORCE_HTTPS=true` 以在应用层强制 HTTPS（依赖 Nginx 传入 `X-Forwarded-Proto`）
- `CORS_ALLOW_ORIGINS` 建议仅允许你的 HTTPS 前端域名
- 若同一台 Nginx 还承担其他站点或 API，请保留它们的 `server`/`location` 块，仅新增 Automatica API 所需的片段，避免覆盖现有转发。

Nginx 参考配置（片段）：

```nginx
# 80/443 仅展示 Automatica API 的最小配置
# 若有其他服务，请继续保留它们自己的 server/location 设置
server {
  listen 80;
  server_name api.wen-xc.site;
  return 301 https://$host$request_uri;
}

server {
  listen 443 ssl http2;
  server_name api.wen-xc.site;

  ssl_certificate /etc/letsencrypt/live/api.wen-xc.site/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/api.wen-xc.site/privkey.pem;
  add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

  # Automatica API & admin（如共存其他服务，请保留它们自己的 location）
  location /orderapi/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }

  location /admin {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }

  # 其他静态资源或 API 的转发仍可继续在此 server 块中配置
  # location /docs { ... }
}
```

使用 systemd 启动（示例）：

```ini
[Unit]
Description=Automatica Tornado API
After=network.target

[Service]
WorkingDirectory=/home/ubuntu/apps/automatica-backend
EnvironmentFile=/home/ubuntu/apps/automatica-backend/backend/.env
Environment=FORCE_HTTPS=true
ExecStart=/home/ubuntu/apps/automatica-backend/.venv/bin/python -m backend.server
Restart=always
User=www-data

[Install]
WantedBy=multi-user.target
```

### 基于 Conda 环境的 systemd 部署

若后端依赖已安装在 Conda 环境（如 `order-inquiry`），可以使用 `conda run` 保证 systemd 内加载正确的解释器与包：

```ini
[Unit]
Description=Automatica Tornado API (Conda)
After=network.target

[Service]
WorkingDirectory=/home/ubuntu/apps/automatica-backend
EnvironmentFile=/home/ubuntu/apps/automatica-backend/backend/.env
Environment=FORCE_HTTPS=true
# conda.sh 用于初始化 shell 钩子
ExecStart=/bin/bash -lc '/opt/miniconda3/bin/conda run --no-capture-output -n order-inquiry python -m backend.server'
Restart=always
User=www-data

[Install]
WantedBy=multi-user.target
```

说明：
- `/opt/miniconda3/bin/conda` 替换为实际 Conda 安装路径；
- `order-inquiry` 替换为项目使用的环境名；
- 使用 `/bin/bash -lc` 可以让 systemd 先读取 Conda 的初始化脚本（例如 `/opt/miniconda3/etc/profile.d/conda.sh`）；
- 通过 `EnvironmentFile` 继续加载 `backend/.env` 中的数据库、CORS 等配置（若改用根目录 `.env`，同步调整路径）。

保存单元文件后执行：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now automatica-conda.service
```

确认日志：`sudo journalctl -u automatica-conda.service -f`

## 数据库

后端首次启动会自动 `create_all` 同步以下表结构：

- **orders**：订单主数据
  - `id` (PK)、`order_no` (唯一)、`group_code`、`weight_kg`、`shipping_fee`、`wooden_crate`、`status`、`updated_at`、`created_at`
- **admin_users**：后台账号
  - `username` (唯一)、`password_hash`、`role`（user/admin/superadmin）、`is_active`
- **user_codes**：用户与查询编号的绑定关系
  - `user_id`、`code`，一对多
- **settings**：系统配置（公告标题/内容、联系方式、注册邀请码等均存储在此表）
- **announcement_history**：公告历史快照
  - `title`、`html`、`updated_by`、`created_at`

> 注册邀请码存放于 `settings` 表的 `register_invite_codes` 键中（JSON 数组）。内容管理页面会自动写入此字段，同时 `/orderapi/register` 端点会校验邀请码是否在该列表中。

## 测试数据

- SQL 版（12 条，非测试标注）：`db/seed_demo_orders.sql`
  - 新增列 `wooden_crate`（1=打木架，0=不打，NULL=未填写）
  - 导入：`mysql -h <host> -u <user> -p automatica < db/seed_demo_orders.sql`

- CSV 版（12 条，带“TEST”标注）：`db/seed_demo_orders_test.csv`
  - 列：`order_no, group_code, weight_kg, status, shipping_fee`
  - 分组值含 `-TEST` 后缀（如 `A2025-TEST`），订单号以 `TEST-` 开头，便于与正式数据区分
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

- Excel 版（12 条，.xlsx，带“TEST”标注）：`db/seed_demo_orders_test.xlsx`
  - 由 CSV 生成：`python tools/make_seed_xlsx.py`（需要 openpyxl，已在依赖中）
  - 后端管理“批量导入 Excel”接口（/orderapi/import/excel）可直接上传该文件测试

## API 概览

- `POST /orderapi/login` 登录（返回 JWT）
- `GET  /orderapi/orders?code=编号` 查询订单（编号为 `A` 返回未分类）
- `GET  /orderapi/orders/by-no/{order_no}` 根据订单号查询
- `PUT  /orderapi/orders/by-no/{order_no}` 更新订单（需 Bearer Token）
- `POST /orderapi/import/excel` 上传 Excel（需 Bearer Token）
- `GET  /orderapi/announcement` 获取公告（公开接口，返回 `html`, `title`, `contacts`, `invite_codes`, `updated_at`）
- `PUT  /orderapi/announcement` 更新公告（需 Bearer Token，字段：`html`, `title`, `contacts`, `invite_codes`）

Excel 表头（首行）：`order_no, group_code, weight_kg, status, shipping_fee`

前端展示
- 桌面（Chrome）：查询结果按表格列项排列显示（订单号/编号/重量/状态/更新）。
- 移动端：以卡片方式显示，适配小屏。
- 顶部“物流流程”模块使用“阶段 → 阶段 → ...”直观箭头样式。

## 前端部署（GitHub Pages）

前端代码迁移至 `AutomaticaOrder/`（Vue 3 + Vite）。

- 本地开发：
  ```bash
  cd AutomaticaOrder
  npm install
  npm run dev
  ```
- 构建部署：`npm run build`，将 `dist/` 下静态资源上传至 GitHub Pages、S3/OSS 或任意静态服务器。
- 若需自定义后端地址，在最终部署页面中添加：
  ```html
  <script>window.API_BASE_URL = 'https://api.your-domain.com';</script>
  ```
  该脚本需在打包产物加载 `/assets/index-*.js` 之前插入，可放置在 Pages 的自定义 `config.js` 或 HTML `<head>` 中。

默认 CSP 已启用 `upgrade-insecure-requests` 与 `block-all-mixed-content`，可自动升级偶发的 http 资源。

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
- 设置 `STRICT_ORIGIN=true`（默认启用）：除 `/orderapi/health` 外，所有 API 请求必须带 `Origin` 且在白名单内，否则 403
- 结合 CORS 与服务器端 Origin 校验，可有效拒绝无 `Origin` 的直连脚本/curl 请求与跨域来源请求（注意：伪造 Origin 的自定义客户端仍可能绕过，必要时可叠加 WAF/速率限制/验证码）
