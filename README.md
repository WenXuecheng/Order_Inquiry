# Order Inquiry

**Quick Start（Conda + Python 3.11）**
- 创建与激活环境:
  - `conda create -n order-inquiry python=3.11 -y`
  - `conda activate order-inquiry`
- 安装依赖（与项目固定版本一致，二选一）:
  - conda-forge: `conda install -c conda-forge tornado=6.5.2 sqlalchemy=2.0.43 pymysql=1.1.2 python-jose=3.5.0 passlib=1.7.4 openpyxl=3.1.5 -y`
  - pip: `python -m pip install --upgrade pip && pip install -r backend/requirements.txt`
- 配置环境变量（`.env` 在项目根目录）:
  - `cp backend/.env.example .env`
  - 关键项：
    - `DATABASE_URL=mysql+pymysql://user:pass@host:3306/automatica`
    - `CORS_ALLOW_ORIGINS=https://wenxuecheng.github.io,https://order.wen-xc.site`
    - `JWT_SECRET=<强随机值>`
    - `ADMIN_USERNAME=admin`
    - `ADMIN_PASSWORD_HASH=pbkdf2_sha256$...`（生成见下）
    - `FORCE_HTTPS=true`，`STRICT_ORIGIN=true`
- 生成管理员密码哈希（pbkdf2_sha256）:
  - `python -c "from passlib.hash import pbkdf2_sha256 as h; print(h.hash('你的密码'))"`
- 运行后端（Tornado）:
  - `export $(grep -v '^#' .env | xargs -d '\n')`
  - `python -m backend.server`
- 验证:
  - `curl https://47.108.186.39/api/health` 应为 200
  - 前端 Pages 已配置 `window.API_BASE_URL = "https://47.108.186.39"`

——

前后端分离：前端静态页（仓库根目录），后端 Tornado（`backend/`）。

- 后端依赖与部署：见 `backend/README.md`
- 前端发布与配置：根目录 `config.js` 中设置 `API_BASE_URL`（必须 https）
- 已加固传输安全：
  - 前端设置 CSP：`upgrade-insecure-requests; block-all-mixed-content`
  - 若页面为 https，会自动将 `API_BASE_URL` 从 http 升级为 https
  - 后端支持 `FORCE_HTTPS=true` 与严格 Origin 白名单（`STRICT_ORIGIN=true`）
