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

4) 生产运行（systemd + Nginx 略）

- 使用 `uvicorn` 或 `gunicorn -k uvicorn.workers.UvicornWorker` 作为服务
- Nginx 反向代理到 `127.0.0.1:8000`
- 确保开启 HTTPS 与 CORS 配置

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

将 `frontend/` 发布到 `gh-pages`：

- 把 `frontend` 目录内容推送到仓库的 `gh-pages` 分支（或设置 Pages 指向根目录）
- 在 `frontend/config.js` 设置：

```js
window.API_BASE_URL = "https://api.example.com"; // 你的后端域名
```

## 安全建议

- 使用强随机 `JWT_SECRET`
- 生产环境必须使用 `ADMIN_PASSWORD_HASH`（bcrypt）
- 仅允许可信静态站点域名通过 CORS
- 在 Nginx 层限制上传大小，开启 HTTPS

