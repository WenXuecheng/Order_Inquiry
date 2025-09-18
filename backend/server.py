import json
import os
import tempfile
from datetime import datetime
from typing import List, Optional

import tornado.ioloop
import tornado.web
from jose import JWTError

from .auth import authenticate_admin, create_access_token, verify_token
from .db import SessionLocal, init_db
from .models import Order, STATUSES
from .importer import import_excel


def get_allowed_origins() -> List[str]:
    raw = os.getenv("CORS_ALLOW_ORIGINS", "")
    return [o.strip() for o in raw.split(",") if o.strip()]


def origin_allowed(origin: Optional[str]) -> bool:
    if not origin:
        return False
    allowed = get_allowed_origins()
    if not allowed:
        return False
    return origin in allowed


STRICT_ORIGIN = os.getenv("STRICT_ORIGIN", "true").lower() in {"1", "true", "yes"}
FORCE_HTTPS = os.getenv("FORCE_HTTPS", "false").lower() in {"1", "true", "yes"}


class BaseHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        origin = self.request.headers.get("Origin")
        allowed = get_allowed_origins()
        self.set_header("Vary", "Origin")
        if origin and origin in allowed:
            self.set_header("Access-Control-Allow-Origin", origin)
            self.set_header("Access-Control-Allow-Credentials", "true")
        # A wildcard would help debugging but we intentionally avoid it for security
        self.set_header("Access-Control-Allow-Methods", "GET,POST,PUT,OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "*, Authorization, Content-Type")

    def check_origin_enforced(self) -> bool:
        # Only enforce for API endpoints; allow HTML like /admin
        if not self.request.path.startswith("/api/"):
            return True
        # Allow health without origin checks
        if self.request.path == "/api/health":
            return True
        if not STRICT_ORIGIN:
            return True
        origin = self.request.headers.get("Origin")
        if not origin or not origin_allowed(origin):
            self.set_status(403)
            self.finish({"detail": "Forbidden: origin not allowed"})
            return False
        return True

    def prepare(self):
        # HTTPS redirect if enabled
        if FORCE_HTTPS:
            # Tornado behind a proxy will see http; trust X-Forwarded-Proto
            xf_proto = self.request.headers.get("X-Forwarded-Proto")
            scheme = xf_proto or self.request.protocol
            if scheme != "https":
                # Only redirect on safe methods
                if self.request.method in ("GET", "HEAD"):
                    url = self.request.full_url().replace("http://", "https://", 1)
                    self.redirect(url, permanent=True)
                    return
                else:
                    self.set_status(400)
                    self.finish({"detail": "HTTPS required"})
                    return

        # Enforce origin if configured
        if not self.check_origin_enforced():
            return

    def options(self, *args, **kwargs):
        # CORS preflight
        self.set_status(204)
        self.finish()


def require_bearer(handler: BaseHandler) -> Optional[str]:
    auth = handler.request.headers.get("Authorization", "")
    parts = auth.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        try:
            sub = verify_token(parts[1])
            return sub
        except JWTError:
            return None
    # Fallback: read JWT from signed secure cookie (admin console)
    try:
        token_bytes = handler.get_secure_cookie("admin_token")
        if token_bytes:
            token = token_bytes.decode("utf-8", errors="ignore")
            sub = verify_token(token)
            return sub
    except Exception:
        return None
    return None


class HealthHandler(BaseHandler):
    def get(self):
        self.write({"ok": True, "time": datetime.utcnow().isoformat()})


class LoginHandler(BaseHandler):
    def post(self):
        try:
            payload = json.loads(self.request.body or b"{}")
        except Exception:
            self.set_status(400); self.finish({"detail": "Invalid JSON"}); return
        username = (payload.get("username") or "").strip()
        password = payload.get("password") or ""
        if not authenticate_admin(username, password):
            self.set_status(401); self.finish({"detail": "用户名或密码错误"}); return
        token = create_access_token(subject=username)
        self.write({"access_token": token, "token_type": "bearer"})


class OrdersHandler(BaseHandler):
    def get(self):
        code = self.get_query_argument("code", default=None)
        if not code:
            self.set_status(400); self.finish({"detail": "缺少参数 code"}); return
        db = SessionLocal()
        try:
            q = db.query(Order)
            if code == "A":
                q = q.filter((Order.group_code == None) | (Order.group_code == ""))
            else:
                q = q.filter(Order.group_code == code)
            orders = q.order_by(Order.updated_at.desc()).all()
            total_count = len(orders)
            total_weight = sum([o.weight_kg or 0.0 for o in orders])
            rate = float(os.getenv("RATE_PER_KG", "0"))
            total_fee = 0.0
            for o in orders:
                if o.shipping_fee is not None:
                    total_fee += float(o.shipping_fee)
                else:
                    total_fee += (o.weight_kg or 0.0) * rate

            def to_dict(o: Order):
                return {
                    "id": o.id,
                    "order_no": o.order_no,
                    "group_code": o.group_code,
                    "weight_kg": o.weight_kg,
                    "shipping_fee": o.shipping_fee,
                    "status": o.status,
                    "updated_at": o.updated_at.isoformat() if o.updated_at else None,
                }

            self.write({
                "orders": [to_dict(o) for o in orders],
                "totals": {
                    "count": total_count,
                    "total_weight": round(total_weight, 3),
                    "total_shipping_fee": round(total_fee, 2),
                },
            })
        finally:
            db.close()


class OrderByNoHandler(BaseHandler):
    def get(self, order_no: str):
        db = SessionLocal()
        try:
            o = db.query(Order).filter(Order.order_no == order_no).one_or_none()
            if not o:
                self.set_status(404); self.finish({"detail": "订单不存在"}); return
            self.write({
                "id": o.id,
                "order_no": o.order_no,
                "group_code": o.group_code,
                "weight_kg": o.weight_kg,
                "shipping_fee": o.shipping_fee,
                "status": o.status,
                "updated_at": o.updated_at.isoformat() if o.updated_at else None,
            })
        finally:
            db.close()

    def put(self, order_no: str):
        user = require_bearer(self)
        if not user:
            self.set_status(401); self.finish({"detail": "未授权"}); return
        try:
            payload = json.loads(self.request.body or b"{}")
        except Exception:
            self.set_status(400); self.finish({"detail": "Invalid JSON"}); return
        db = SessionLocal()
        try:
            o = db.query(Order).filter(Order.order_no == order_no).one_or_none()
            if not o:
                self.set_status(404); self.finish({"detail": "订单不存在"}); return
            if "group_code" in payload:
                o.group_code = payload.get("group_code")
            if "weight_kg" in payload:
                o.weight_kg = payload.get("weight_kg")
            if "shipping_fee" in payload:
                o.shipping_fee = payload.get("shipping_fee")
            if "status" in payload:
                status = payload.get("status")
                if status not in STATUSES:
                    self.set_status(400); self.finish({"detail": "状态非法"}); return
                o.status = status
            o.updated_at = datetime.utcnow()
            db.add(o)
            db.commit()
            db.refresh(o)
            self.write({
                "id": o.id,
                "order_no": o.order_no,
                "group_code": o.group_code,
                "weight_kg": o.weight_kg,
                "shipping_fee": o.shipping_fee,
                "status": o.status,
                "updated_at": o.updated_at.isoformat() if o.updated_at else None,
            })
        finally:
            db.close()


class ImportExcelHandler(BaseHandler):
    def post(self):
        user = require_bearer(self)
        if not user:
            self.set_status(401); self.finish({"detail": "未授权"}); return
        if not self.request.files or "file" not in self.request.files:
            self.set_status(400); self.finish({"detail": "请上传 .xlsx 文件"}); return
        fileinfo = self.request.files["file"][0]
        filename = fileinfo.filename or ""
        if not filename.endswith(".xlsx"):
            self.set_status(400); self.finish({"detail": "请上传 .xlsx 文件"}); return
        # Save to temp and import
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=True) as tmp:
            tmp.write(fileinfo.body)
            tmp.flush()
            db = SessionLocal()
            try:
                stats = import_excel(db, tmp.name)
            finally:
                db.close()
        self.write(stats)


def make_app():
    init_db()
    settings = {
        "debug": os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"},
        "cookie_secret": os.getenv("COOKIE_SECRET", os.getenv("JWT_SECRET", "dev-cookie-secret-change-me")),
        "xsrf_cookies": False,
    }

    class AdminIndexHandler(BaseHandler):
        def get(self):
            token = self.get_query_argument("token", default=None)
            if token:
                # Validate token then set secure cookie and redirect to clean URL
                sub = verify_token(token)
                if not sub:
                    self.set_status(401); self.finish({"detail": "无效或过期的令牌"}); return
                # Store raw JWT in secure cookie (HttpOnly, Secure suggested at TLS layer)
                self.set_secure_cookie("admin_token", token, httponly=True, secure=FORCE_HTTPS)
                self.redirect("/admin", permanent=False)
                return
            # No token in query; require valid cookie
            user = require_bearer(self)
            if not user:
                self.set_status(401); self.finish("未授权，请从管理入口登录后跳转访问。")
                return
            # Serve a minimal Vue3 admin shell (CDN based)
            statuses_json = json.dumps(STATUSES, ensure_ascii=False)
            admin_html = """
<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>订单后台管理</title>
  <link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap\" rel=\"stylesheet\">
  <style>
    body {{ margin:0; font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; background:#0b0c10; color:#e6e7eb; }}
    header, main {{ max-width: 1100px; margin: 0 auto; padding: 14px; }}
    .card {{ background:#101219; border:1px solid #1a1e27; border-radius:14px; padding:14px; }}
    .row {{ display:flex; gap:8px; align-items:center; }}
    .btn {{ background:#1a1e27; border:1px solid #232736; color:#e6e7eb; padding:8px 12px; border-radius:10px; cursor:pointer; }}
    .input, select {{ background:#0b0e14; border:1px solid #1a1e27; color:#e6e7eb; border-radius:10px; padding:8px 10px; }}
    table {{ width:100%; border-collapse: collapse; }}
    th, td {{ border-bottom:1px solid #1a1e27; padding:8px; text-align:left; }}
  </style>
  <script type=\"module\">
    import { createApp, ref, onMounted } from 'https://unpkg.com/vue@3/dist/vue.esm-browser.js';
    const STATUSES = __STATUSES__;
    const API_BASE = new URL('/api', window.location.origin).toString().replace(/\/$/, '');
    const app = {
      setup() {
        const orderNo = ref('');
        const editing = ref(null);
        const msg = ref('');
        const uploading = ref(false);
        const file = ref(null);
        const listCode = ref('');
        const list = ref([]);
        const totals = ref({});

        async function api(path, init={}) {
          const resp = await fetch(`${API_BASE}${path}`, { credentials: 'include', ...init });
          let data = null; try { data = await resp.json(); } catch {}
          if (!resp.ok) throw new Error((data && data.detail) || `请求失败 ${resp.status}`);
          return data;
        }

        async function loadByNo() {
          if (!orderNo.value) { msg.value = '请输入订单号'; return; }
          msg.value = '加载中...';
          try {
            const data = await api(`/orders/by-no/${encodeURIComponent(orderNo.value)}`);
            editing.value = {
              order_no: data.order_no,
              group_code: data.group_code || '',
              weight_kg: data.weight_kg ?? '',
              status: data.status,
              shipping_fee: data.shipping_fee ?? '',
            };
            msg.value = '已加载';
          } catch(e) { msg.value = e.message; }
        }

        async function save() {
          if (!editing.value) return;
          msg.value = '保存中...';
          try {
            const payload = {
              group_code: editing.value.group_code || null,
              weight_kg: editing.value.weight_kg !== '' ? parseFloat(editing.value.weight_kg) : null,
              status: editing.value.status,
              shipping_fee: editing.value.shipping_fee !== '' ? parseFloat(editing.value.shipping_fee) : null,
            };
            await api(`/orders/by-no/${encodeURIComponent(editing.value.order_no)}`, { method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
            msg.value = '保存成功';
          } catch(e) { msg.value = e.message; }
        }

        async function importExcel(ev) {
          const f = ev.target.files && ev.target.files[0];
          if (!f) return;
          uploading.value = true; msg.value = '上传中...';
          try {
            const fd = new FormData(); fd.append('file', f);
            await api('/import/excel', { method:'POST', body: fd });
            msg.value = '导入成功';
          } catch(e) { msg.value = e.message; }
          finally { uploading.value = false; ev.target.value=''; }
        }

        async function queryList() {
          if (!listCode.value) { msg.value = '请输入编号'; return; }
          msg.value = '查询中...';
          try {
            const data = await api(`/orders?code=${encodeURIComponent(listCode.value)}`);
            list.value = data.orders || []; totals.value = data.totals || {};
            msg.value = '';
          } catch(e) { msg.value = e.message; }
        }

        function logout() {
          // clear cookie by setting expired cookie
          document.cookie = 'admin_token=; Max-Age=0; path=/;';
          window.location.href = '/';
        }

        onMounted(()=>{});
        return { orderNo, editing, msg, uploading, file, loadByNo, save, importExcel, STATUSES, listCode, list, queryList, totals, logout };
      },
      template: `
        <header class=\"row\" style=\"justify-content: space-between;\"> 
          <h2>订单后台管理</h2>
          <button class=\"btn\" @click=\"logout\">退出</button>
        </header>
        <main>
          <div class=\"card\" style=\"margin-bottom:12px;\">
            <h3>编辑订单</h3>
            <div class=\"row\">
              <input class=\"input\" v-model=\"orderNo\" placeholder=\"订单号\" />
              <button class=\"btn\" @click=\"loadByNo\">加载</button>
            </div>
            <div v-if=\"editing\" style=\"margin-top:8px; display:grid; grid-template-columns: repeat(2, 1fr); gap:8px;\">
              <label>所属编号 <input class=\"input\" v-model=\"editing.group_code\" /></label>
              <label>重量(kg) <input class=\"input\" type=\"number\" step=\"0.01\" v-model=\"editing.weight_kg\" /></label>
              <label>状态 <select class=\"input\" v-model=\"editing.status\"><option v-for=\"s in STATUSES\" :key=\"s\" :value=\"s\">{{'{{'}}s{{'}}'}}</option></select></label>
              <label>运费 <input class=\"input\" type=\"number\" step=\"0.01\" v-model=\"editing.shipping_fee\" /></label>
              <div><button class=\"btn\" @click=\"save\">保存</button></div>
            </div>
          </div>

          <div class=\"card\" style=\"margin-bottom:12px;\">
            <h3>批量导入（.xlsx）</h3>
            <input type=\"file\" accept=\".xlsx\" @change=\"importExcel\" :disabled=\"uploading\"/>
          </div>

          <div class=\"card\">
            <h3>查询列表</h3>
            <div class=\"row\">
              <input class=\"input\" v-model=\"listCode\" placeholder=\"编号，如 2025-01 或 A\" />
              <button class=\"btn\" @click=\"queryList\">查询</button>
            </div>
            <div style=\"overflow:auto; margin-top:8px;\">
              <table>
                <thead><tr><th>订单号</th><th>编号</th><th>重量</th><th>状态</th><th>更新</th></tr></thead>
                <tbody>
                  <tr v-for=\"o in list\" :key=\"o.id\">
                    <td>{{'{{'}}o.order_no{{'}}'}}</td>
                    <td>{{'{{'}}o.group_code||''{{'}}'}}</td>
                    <td>{{'{{'}}(o.weight_kg??0).toFixed(2){{'}}'}} kg</td>
                    <td>{{'{{'}}o.status{{'}}'}}</td>
                    <td>{{'{{'}}o.updated_at{{'}}'}}</td>
                  </tr>
                </tbody>
              </table>
              <div style=\"opacity:.8; font-size:12px;\">合计：件数 {{'{{'}}totals.count||0{{'}}'}} | 重量 {{'{{'}}(totals.total_weight||0).toFixed(2){{'}}'}} kg | 运费 {{'{{'}}(totals.total_shipping_fee||0).toFixed(2){{'}}'}}</div>
            </div>
          </div>

          <div style=\"margin-top:8px; color:#a3a7b3;\">{{'{{'}}msg{{'}}'}}</div>
        </main>
      `
    };
    createApp(app).mount(document.body);
  </script>
</head>
<body></body>
</html>
"""
            admin_html = admin_html.replace("__STATUSES__", statuses_json)
            self.set_header("Content-Type", "text/html; charset=utf-8")
            self.write(admin_html)

    return tornado.web.Application([
        (r"/api/health", HealthHandler),
        (r"/api/login", LoginHandler),
        (r"/api/orders", OrdersHandler),
        (r"/api/orders/by-no/([A-Za-z0-9\-_]+)", OrderByNoHandler),
        (r"/api/import/excel", ImportExcelHandler),
        (r"/admin", AdminIndexHandler),
    ], **settings)


def main():
    app = make_app()
    port = int(os.getenv("PORT", "8000"))
    app.listen(port, address=os.getenv("HOST", "0.0.0.0"))
    print(f"Tornado server listening on {os.getenv('HOST', '0.0.0.0')}:{port}")
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
