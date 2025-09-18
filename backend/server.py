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
    return tornado.web.Application([
        (r"/api/health", HealthHandler),
        (r"/api/login", LoginHandler),
        (r"/api/orders", OrdersHandler),
        (r"/api/orders/by-no/([A-Za-z0-9\-_]+)", OrderByNoHandler),
        (r"/api/import/excel", ImportExcelHandler),
    ], debug=os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"})


def main():
    app = make_app()
    port = int(os.getenv("PORT", "8000"))
    app.listen(port, address=os.getenv("HOST", "0.0.0.0"))
    print(f"Tornado server listening on {os.getenv('HOST', '0.0.0.0')}:{port}")
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()

