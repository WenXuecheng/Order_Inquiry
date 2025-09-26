import json
import os
import random
import string
import tempfile
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import List, Optional

import tornado.ioloop
import tornado.web
from jose import JWTError
from sqlalchemy.exc import IntegrityError

# Support running both as package (python -m backend.server) and as script (python backend/server.py)
try:
    from .auth import authenticate_admin, create_access_token, verify_token, ensure_default_admin, verify_password, get_password_hash
    from .db import SessionLocal, init_db
    from .models import Order, STATUSES, Setting, AnnouncementHistory, AdminUser, UserCode
    from .importer import import_excel
    from openpyxl import Workbook
except Exception:
    import sys, pathlib
    ROOT = pathlib.Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from backend.auth import authenticate_admin, create_access_token, verify_token, ensure_default_admin, verify_password, get_password_hash
    from backend.db import SessionLocal, init_db
    from backend.models import Order, STATUSES, Setting, AnnouncementHistory, AdminUser, UserCode
    from backend.importer import import_excel
    from openpyxl import Workbook


def get_allowed_origins() -> List[str]:
    raw = os.getenv("CORS_ALLOW_ORIGINS", "")
    return [o.strip() for o in raw.split(",") if o.strip()]


def origin_allowed(origin: Optional[str]) -> bool:
    if not origin:
        return False
    allowed = get_allowed_origins()
    if not allowed:
        return False
    # Support wildcard "*": accept any non-empty origin when '*' present
    if "*" in allowed:
        return True
    return origin in allowed


STRICT_ORIGIN = os.getenv("STRICT_ORIGIN", "true").lower() in {"1", "true", "yes"}
FORCE_HTTPS = os.getenv("FORCE_HTTPS", "false").lower() in {"1", "true", "yes"}


def parse_date_param(value: str) -> Optional[datetime]:
    """Parse ISO or YYYY-MM-DD strings into naive UTC datetimes."""
    if not value:
        return None
    parsed = value.strip()
    if not parsed:
        return None
    if parsed.endswith("Z"):
        parsed = parsed[:-1] + "+00:00"
    dt = None
    try:
        dt = datetime.fromisoformat(parsed)
    except ValueError:
        try:
            dt = datetime.strptime(parsed, "%Y-%m-%d")
        except ValueError:
            return None
    if dt.tzinfo:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def parse_bool_param(value, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        val = value.strip().lower()
        if val in ("1", "true", "yes", "on"): return True
        if val in ("0", "false", "no", "off", ""):
            return False
    return default


class BaseHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        origin = self.request.headers.get("Origin")
        allowed = get_allowed_origins()
        self.set_header("Vary", "Origin")
        if origin and (origin in allowed or "*" in allowed):
            # When wildcard is configured, reflect the request origin to remain
            # compatible with credentials per CORS spec (cannot use '*' with credentials)
            self.set_header("Access-Control-Allow-Origin", origin)
            self.set_header("Access-Control-Allow-Credentials", "true")
        # A wildcard would help debugging but we intentionally avoid it for security
        self.set_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS,HEAD")
        self.set_header("Access-Control-Allow-Headers", "*, Authorization, Content-Type")

    def check_origin_enforced(self) -> bool:
        # Only enforce for API endpoints; allow HTML like /admin
        if not self.request.path.startswith("/orderapi/"):
            return True
        # Allow health without origin checks
        if self.request.path == "/orderapi/health":
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

    def head(self, *args, **kwargs):
        # Respond 204 to HEAD by default so health checks like `curl -I` succeed
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


def get_current_user(handler: BaseHandler):
    """Return dict with username, role, user_id, is_env_superadmin."""
    sub = require_bearer(handler)
    if not sub:
        return None
    # Try DB lookup
    db = SessionLocal()
    try:
        u = db.query(AdminUser).filter(AdminUser.username == sub).one_or_none()
        if u:
            return {"username": u.username, "role": (u.role or "user"), "user_id": u.id, "is_env_superadmin": False}
    finally:
        db.close()
    # If not in DB, treat env-login as superadmin
    return {"username": sub, "role": "superadmin", "user_id": None, "is_env_superadmin": True}


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
        # Determine role from DB if exists; else superadmin for env-login bootstrap
        db = SessionLocal()
        role = "superadmin"
        try:
            u = db.query(AdminUser).filter(AdminUser.username == username).one_or_none()
            if u:
                if not u.is_active:
                    self.set_status(403); self.finish({"detail": "账户已被禁用，请联系管理员"}); return
                role = u.role or "user"
        finally:
            db.close()
        token = create_access_token(subject=username, role=role)
        self.write({"access_token": token, "token_type": "bearer", "role": role})


class RegisterHandler(BaseHandler):
    def post(self):
        try:
            payload = json.loads(self.request.body or b"{}")
        except Exception:
            self.set_status(400); self.finish({"detail": "Invalid JSON"}); return
        username = (payload.get("username") or "").strip()
        password = payload.get("password") or ""
        invite_code = (payload.get("invite_code") or "").strip()
        codes = payload.get("codes") or []
        if not username or not password:
            self.set_status(400); self.finish({"detail": "缺少用户名或密码"}); return
        if not invite_code:
            self.set_status(400); self.finish({"detail": "缺少邀请码"}); return
        db = SessionLocal()
        try:
            s_invites = db.query(Setting).filter(Setting.key == 'register_invite_codes').one_or_none()
            invites = []
            if s_invites and s_invites.value:
                try:
                    data = json.loads(s_invites.value)
                    if isinstance(data, list):
                        invites = [str(item).strip() for item in data if str(item).strip()]
                except Exception:
                    invites = []
            if not invites or invite_code not in invites:
                self.set_status(403); self.finish({"detail": "邀请码无效"}); return
            exists = db.query(AdminUser).filter(AdminUser.username == username).one_or_none()
            if exists:
                self.set_status(409); self.finish({"detail": "用户名已存在"}); return
            from .auth import get_password_hash
            u = AdminUser(username=username, password_hash=get_password_hash(password), role="user", is_active=True)
            db.add(u); db.flush()
            for c in codes:
                s = str(c or '').strip()
                if s:
                    db.add(UserCode(user_id=u.id, code=s))
            db.commit()
            token = create_access_token(subject=username, role="user")
            self.set_status(201)
            self.write({"access_token": token, "token_type": "bearer", "role": "user"})
        finally:
            db.close()


class UsernameCheckHandler(BaseHandler):
    def get(self):
        username = self.get_query_argument("username", default="").strip()
        if not username:
            self.set_status(400)
            self.finish({"detail": "缺少用户名"})
            return
        db = SessionLocal()
        try:
            exists = db.query(AdminUser).filter(AdminUser.username == username).one_or_none()
            self.write({"available": exists is None})
        finally:
            db.close()


class RandomUsernameHandler(BaseHandler):
    def get(self):
        prefix_raw = self.get_query_argument("prefix", default="user").strip()
        filtered = ''.join(ch for ch in prefix_raw if ch.isalnum())
        prefix = (filtered or 'user').lower()
        db = SessionLocal()
        try:
            for _ in range(80):
                suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
                candidate = f"{prefix}{suffix}"
                exists = db.query(AdminUser).filter(AdminUser.username == candidate).one_or_none()
                if not exists:
                    self.write({"username": candidate})
                    return
            self.set_status(503)
            self.finish({"detail": "暂时无法生成唯一用户名，请稍后再试"})
        finally:
            db.close()


class OrdersHandler(BaseHandler):
    def get(self):
        code = self.get_query_argument("code", default=None)
        status_filter = self.get_query_argument("status", default="").strip()
        start_raw = self.get_query_argument("start_date", default="").strip()
        end_raw = self.get_query_argument("end_date", default="").strip()
        if status_filter and status_filter not in STATUSES:
            self.set_status(400)
            self.finish({"detail": "状态非法"})
            return
        start_dt = parse_date_param(start_raw)
        if start_raw and not start_dt:
            self.set_status(400)
            self.finish({"detail": "开始日期格式不正确"})
            return
        end_dt = parse_date_param(end_raw)
        if end_raw and not end_dt:
            self.set_status(400)
            self.finish({"detail": "结束日期格式不正确"})
            return
        if start_dt and end_dt and start_dt > end_dt:
            self.set_status(400)
            self.finish({"detail": "开始日期不能晚于结束日期"})
            return
        try:
            page = max(1, int(self.get_query_argument("page", default="1")))
            size = int(self.get_query_argument("page_size", default="20"))
            size = 1 if size < 1 else (200 if size > 200 else size)
        except Exception:
            page, size = 1, 20
        db = SessionLocal()
        try:
            q = db.query(Order)
            if code == "A":
                q = q.filter((Order.group_code == None) | (Order.group_code == ""))
            elif code:
                q = q.filter(Order.group_code == code)
            if status_filter:
                q = q.filter(Order.status == status_filter)
            if start_dt:
                q = q.filter(Order.updated_at >= start_dt)
            if end_dt:
                q = q.filter(Order.updated_at < (end_dt + timedelta(days=1)))
            total_count = q.count()
            orders = q.order_by(Order.updated_at.desc()).offset((page-1)*size).limit(size).all()
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
                    "wooden_crate": o.wooden_crate,
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
                "total": total_count,
                "page": page,
                "page_size": size,
                "pages": (total_count + size - 1) // size,
            })
        finally:
            db.close()

    def post(self):
        cu = get_current_user(self)
        if not cu:
            self.set_status(401); self.finish({"detail": "未授权"}); return
        if cu["role"] not in ("admin", "superadmin"):
            self.set_status(403); self.finish({"detail": "无权限"}); return
        try:
            payload = json.loads(self.request.body or b"{}")
        except Exception:
            self.set_status(400); self.finish({"detail": "Invalid JSON"}); return
        order_no = (payload.get("order_no") or "").strip()
        if not order_no:
            self.set_status(400); self.finish({"detail": "缺少字段 order_no"}); return
        status = payload.get("status") or STATUSES[0]
        if status not in STATUSES:
            self.set_status(400); self.finish({"detail": "状态非法"}); return
        group_code = payload.get("group_code")
        weight_kg = payload.get("weight_kg")
        shipping_fee = payload.get("shipping_fee")
        wooden_crate = payload.get("wooden_crate") if "wooden_crate" in payload else None
        if wooden_crate not in (None, True, False):
            if wooden_crate in (0, 1):
                wooden_crate = bool(wooden_crate)
            else:
                wooden_crate = None
        try:
            if weight_kg is not None:
                weight_kg = float(weight_kg)
        except Exception:
            self.set_status(400); self.finish({"detail": "weight_kg 必须为数字"}); return
        try:
            if shipping_fee is not None:
                shipping_fee = float(shipping_fee)
        except Exception:
            self.set_status(400); self.finish({"detail": "shipping_fee 必须为数字"}); return

        db = SessionLocal()
        try:
            exists = db.query(Order).filter(Order.order_no == order_no).one_or_none()
            if exists:
                self.set_status(409); self.finish({"detail": "订单已存在"}); return
            now = datetime.utcnow()
            o = Order(
                order_no=order_no,
                group_code=group_code,
                weight_kg=weight_kg,
                shipping_fee=shipping_fee,
                wooden_crate=wooden_crate,
                status=status,
                created_at=now,
                updated_at=now,
            )
            db.add(o)
            db.commit()
            db.refresh(o)
            self.set_status(201)
            self.write({
                "id": o.id,
                "order_no": o.order_no,
                "group_code": o.group_code,
                "weight_kg": o.weight_kg,
                "shipping_fee": o.shipping_fee,
                "wooden_crate": o.wooden_crate,
                "status": o.status,
                "updated_at": o.updated_at.isoformat() if o.updated_at else None,
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
                "wooden_crate": o.wooden_crate,
                "status": o.status,
                "updated_at": o.updated_at.isoformat() if o.updated_at else None,
            })
        finally:
            db.close()

    def put(self, order_no: str):
        cu = get_current_user(self)
        if not cu:
            self.set_status(401); self.finish({"detail": "未授权"}); return
        if cu["role"] not in ("admin", "superadmin"):
            self.set_status(403); self.finish({"detail": "无权限"}); return
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
            if "wooden_crate" in payload:
                val = payload.get("wooden_crate")
                if isinstance(val, bool):
                    o.wooden_crate = val
                elif val in (0, 1, None):
                    o.wooden_crate = bool(val) if val is not None else None
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

    def delete(self, order_no: str):
        cu = get_current_user(self)
        if not cu:
            self.set_status(401); self.finish({"detail": "未授权"}); return
        if cu["role"] not in ("admin", "superadmin"):
            self.set_status(403); self.finish({"detail": "无权限"}); return
        db = SessionLocal()
        try:
            o = db.query(Order).filter(Order.order_no == order_no).one_or_none()
            if not o:
                self.set_status(404); self.finish({"detail": "订单不存在"}); return
            db.delete(o)
            db.commit()
            self.set_status(204)
            self.finish()
        finally:
            db.close()


class OrdersBulkDeleteHandler(BaseHandler):
    def delete(self):
        cu = get_current_user(self)
        if not cu:
            self.set_status(401); self.finish({"detail": "未授权"}); return
        if cu["role"] not in ("admin", "superadmin"):
            self.set_status(403); self.finish({"detail": "无权限"}); return
        try:
            payload = json.loads(self.request.body or b"{}")
        except Exception:
            self.set_status(400); self.finish({"detail": "Invalid JSON"}); return
        order_nos_raw = payload.get("order_nos") or []
        if not isinstance(order_nos_raw, list) or not order_nos_raw:
            self.set_status(400); self.finish({"detail": "缺少 order_nos 列表"}); return
        order_nos = []
        for code in order_nos_raw:
            if not isinstance(code, (str, int)):
                continue
            s = str(code).strip()
            if s:
                order_nos.append(s)
        if not order_nos:
            self.set_status(400); self.finish({"detail": "缺少有效的订单号"}); return
        db = SessionLocal()
        try:
            n = db.query(Order).filter(Order.order_no.in_(order_nos)).delete(synchronize_session=False)
            db.commit()
            self.write({"deleted": n})
        finally:
            db.close()


class OrdersExportHandler(BaseHandler):
    def get(self):
        cu = get_current_user(self)
        if not cu:
            self.set_status(401)
            self.finish({"detail": "未授权"})
            return
        if cu["role"] not in ("admin", "superadmin"):
            self.set_status(403)
            self.finish({"detail": "无权限"})
            return
        code = self.get_query_argument("code", default="").strip()
        status_filter = self.get_query_argument("status", default="").strip()
        start_raw = self.get_query_argument("start_date", default="").strip()
        end_raw = self.get_query_argument("end_date", default="").strip()
        if status_filter and status_filter not in STATUSES:
            self.set_status(400)
            self.finish({"detail": "状态非法"})
            return
        start_dt = parse_date_param(start_raw)
        if start_raw and not start_dt:
            self.set_status(400)
            self.finish({"detail": "开始日期格式不正确"})
            return
        end_dt = parse_date_param(end_raw)
        if end_raw and not end_dt:
            self.set_status(400)
            self.finish({"detail": "结束日期格式不正确"})
            return
        if start_dt and end_dt and start_dt > end_dt:
            self.set_status(400)
            self.finish({"detail": "开始日期不能晚于结束日期"})
            return
        db = SessionLocal()
        try:
            query = db.query(Order)
            if code:
                if code == 'A':
                    query = query.filter((Order.group_code == None) | (Order.group_code == ""))
                else:
                    query = query.filter(Order.group_code == code)
            if status_filter:
                query = query.filter(Order.status == status_filter)
            if start_dt:
                query = query.filter(Order.updated_at >= start_dt)
            if end_dt:
                query = query.filter(Order.updated_at < (end_dt + timedelta(days=1)))
            orders = query.order_by(Order.updated_at.desc()).all()
        finally:
            db.close()

        wb = Workbook()
        ws = wb.active
        ws.title = "orders"
        headers = ["订单号", "编号", "重量(kg)", "运费", "状态", "木架", "更新时间"]
        ws.append(headers)
        for order in orders:
            ws.append([
                order.order_no,
                order.group_code or '',
                float(order.weight_kg) if order.weight_kg is not None else '',
                float(order.shipping_fee) if order.shipping_fee is not None else '',
                order.status,
                ("是" if order.wooden_crate is True else ("否" if order.wooden_crate is False else "未设置")),
                order.updated_at.isoformat() if order.updated_at else '',
            ])

        stream = BytesIO()
        wb.save(stream)
        stream.seek(0)
        filename = f"orders-export-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.xlsx"
        self.set_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.set_header("Content-Disposition", f"attachment; filename={filename}")
        self.write(stream.getvalue())
        self.finish()


class AdminUsersHandler(BaseHandler):
    def get(self):
        cu = get_current_user(self)
        if not cu:
            self.set_status(401); self.finish({"detail": "未授权"}); return
        if cu["role"] != "superadmin":
            self.set_status(403); self.finish({"detail": "无权限"}); return
        qstr = (self.get_query_argument("q", default="").strip())
        role = (self.get_query_argument("role", default="").strip())
        try:
            page = max(1, int(self.get_query_argument("page", default="1")))
            size = int(self.get_query_argument("page_size", default="20"))
            size = 1 if size < 1 else (200 if size > 200 else size)
        except Exception:
            page, size = 1, 20
        db = SessionLocal()
        try:
            q = db.query(AdminUser)
            if qstr:
                q = q.filter(AdminUser.username.like(f"%{qstr}%"))
            if role:
                q = q.filter(AdminUser.role == role)
            total = q.count()
            rows = q.order_by(AdminUser.created_at.desc()).offset((page-1)*size).limit(size).all()
            ids = [r.id for r in rows]
            # fetch codes
            code_map = {}
            if ids:
                codes = db.query(UserCode).filter(UserCode.user_id.in_(ids)).all()
                for c in codes:
                    code_map.setdefault(c.user_id, []).append(c.code)
            def to_dict(u: AdminUser):
                return {"id": u.id, "username": u.username, "role": u.role, "is_active": u.is_active, "created_at": u.created_at.isoformat() if u.created_at else None, "codes": code_map.get(u.id, [])}
            self.write({"items": [to_dict(u) for u in rows], "total": total, "page": page, "page_size": size, "pages": (total + size - 1)//size})
        finally:
            db.close()

    def post(self):
        cu = get_current_user(self)
        if not cu:
            self.set_status(401); self.finish({"detail": "未授权"}); return
        if cu["role"] != "superadmin":
            self.set_status(403); self.finish({"detail": "无权限"}); return
        try:
            payload = json.loads(self.request.body or b"{}")
        except Exception:
            self.set_status(400); self.finish({"detail": "Invalid JSON"}); return
        username = (payload.get("username") or "").strip()
        password = payload.get("password") or ""
        role = (payload.get("role") or "user").strip()
        is_active = parse_bool_param(payload.get("is_active", True), default=True)
        codes = payload.get("codes") or []
        if not username or not password:
            self.set_status(400); self.finish({"detail": "缺少用户名或密码"}); return
        db = SessionLocal()
        try:
            exists = db.query(AdminUser).filter(AdminUser.username == username).one_or_none()
            if exists:
                self.set_status(409); self.finish({"detail": "用户名已存在"}); return
            from .auth import get_password_hash
            u = AdminUser(username=username, password_hash=get_password_hash(password), role=role if role in ("user","admin","superadmin") else "user", is_active=is_active)
            db.add(u); db.flush()
            for c in codes:
                s = str(c or '').strip()
                if s:
                    db.add(UserCode(user_id=u.id, code=s))
            db.commit()
            self.set_status(201); self.write({"id": u.id})
        finally:
            db.close()

    def delete(self):
        cu = get_current_user(self)
        if not cu:
            self.set_status(401); self.finish({"detail": "未授权"}); return
        if cu["role"] != "superadmin":
            self.set_status(403); self.finish({"detail": "无权限"}); return
        try:
            payload = json.loads(self.request.body or b"{}")
        except Exception:
            self.set_status(400); self.finish({"detail": "Invalid JSON"}); return
        ids_raw = payload.get("ids") or []
        if not isinstance(ids_raw, list) or not ids_raw:
            self.set_status(400); self.finish({"detail": "缺少 ids 列表"}); return
        ids = []
        for item in ids_raw:
            try:
                ids.append(int(item))
            except (TypeError, ValueError):
                continue
        if not ids:
            self.set_status(400); self.finish({"detail": "缺少有效的用户 id"}); return
        db = SessionLocal()
        try:
            db.query(UserCode).filter(UserCode.user_id.in_(ids)).delete(synchronize_session=False)
            n = db.query(AdminUser).filter(AdminUser.id.in_(ids)).delete(synchronize_session=False)
            db.commit()
            self.write({"deleted": n})
        finally:
            db.close()


class AdminUserDetailHandler(BaseHandler):
    def put(self, uid: str):
        cu = get_current_user(self)
        if not cu:
            self.set_status(401); self.finish({"detail": "未授权"}); return
        if cu["role"] != "superadmin":
            self.set_status(403); self.finish({"detail": "无权限"}); return
        try:
            payload = json.loads(self.request.body or b"{}")
        except Exception:
            self.set_status(400); self.finish({"detail": "Invalid JSON"}); return
        db = SessionLocal()
        try:
            u = db.query(AdminUser).filter(AdminUser.id == int(uid)).one_or_none()
            if not u:
                self.set_status(404); self.finish({"detail": "用户不存在"}); return
            if "role" in payload:
                r = (payload.get("role") or "").strip()
                if r in ("user","admin","superadmin"):
                    u.role = r
            if "is_active" in payload:
                u.is_active = parse_bool_param(payload.get("is_active"), default=u.is_active)
            if "password" in payload and payload.get("password"):
                from .auth import get_password_hash
                u.password_hash = get_password_hash(payload["password"])
            if "codes" in payload and isinstance(payload.get("codes"), list):
                db.query(UserCode).filter(UserCode.user_id == u.id).delete(synchronize_session=False)
                for c in payload.get("codes"):
                    s = str(c or '').strip()
                    if s:
                        db.add(UserCode(user_id=u.id, code=s))
            db.add(u); db.commit()
            self.write({"ok": True})
        finally:
            db.close()


class MeCodesHandler(BaseHandler):
    def get(self):
        cu = get_current_user(self)
        if not cu:
            self.set_status(401); self.finish({"detail": "未授权"}); return
        db = SessionLocal()
        try:
            codes = [c.code for c in db.query(UserCode).filter(UserCode.user_id == cu["user_id"]).all()]
            self.write({"codes": codes})
        finally:
            db.close()

    def post(self):
        cu = get_current_user(self)
        if not cu:
            self.set_status(401); self.finish({"detail": "未授权"}); return
        try:
            payload = json.loads(self.request.body or b"{}")
        except Exception:
            self.set_status(400); self.finish({"detail": "Invalid JSON"}); return
        code = (payload.get("code") or "").strip()
        if not code:
            self.set_status(400); self.finish({"detail": "缺少 code"}); return
        db = SessionLocal()
        try:
            exists = db.query(UserCode).filter(UserCode.user_id == cu["user_id"], UserCode.code == code).one_or_none()
            if exists:
                self.set_status(409); self.finish({"detail": "编号已绑定"}); return
            other_owner = db.query(UserCode).filter(UserCode.code == code, UserCode.user_id != cu["user_id"]).one_or_none()
            if other_owner:
                self.set_status(409); self.finish({"detail": "编号已被其他账号绑定"}); return
            db.add(UserCode(user_id=cu["user_id"], code=code))
            db.commit()
            self.write({"ok": True})
        except IntegrityError:
            db.rollback()
            self.set_status(409); self.finish({"detail": "编号已被其他账号绑定"}); return
        finally:
            db.close()

    def delete(self):
        cu = get_current_user(self)
        if not cu:
            self.set_status(401); self.finish({"detail": "未授权"}); return
        try:
            payload = json.loads(self.request.body or b"{}")
        except Exception:
            self.set_status(400); self.finish({"detail": "Invalid JSON"}); return
        code = (payload.get("code") or "").strip()
        if not code:
            self.set_status(400); self.finish({"detail": "缺少 code"}); return
        db = SessionLocal()
        try:
            n = db.query(UserCode).filter(UserCode.user_id == cu["user_id"], UserCode.code == code).delete(synchronize_session=False)
            db.commit()
            self.write({"deleted": n})
        finally:
            db.close()


class UserPasswordHandler(BaseHandler):
    def post(self):
        cu = get_current_user(self)
        if not cu:
            self.set_status(401); self.finish({"detail": "未授权"}); return
        try:
            payload = json.loads(self.request.body or b"{}")
        except Exception:
            self.set_status(400); self.finish({"detail": "Invalid JSON"}); return
        old_pwd = (payload.get("old_password") or "").strip()
        new_pwd = (payload.get("new_password") or "").strip()
        if not old_pwd or not new_pwd:
            self.set_status(400); self.finish({"detail": "缺少密码"}); return
        if len(new_pwd) < 6:
            self.set_status(400); self.finish({"detail": "新密码至少 6 位"}); return
        db = SessionLocal()
        try:
            u = db.query(AdminUser).filter(AdminUser.id == cu["user_id"]).one_or_none()
            if not u:
                self.set_status(404); self.finish({"detail": "用户不存在"}); return
            if not verify_password(old_pwd, u.password_hash):
                self.set_status(403); self.finish({"detail": "当前密码不正确"}); return
            u.password_hash = get_password_hash(new_pwd)
            db.add(u)
            db.commit()
            self.write({"ok": True})
        finally:
            db.close()


class ImportExcelHandler(BaseHandler):
    def post(self):
        cu = get_current_user(self)
        if not cu:
            self.set_status(401); self.finish({"detail": "未授权"}); return
        if cu["role"] not in ("admin", "superadmin"):
            self.set_status(403); self.finish({"detail": "无权限"}); return
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


class AnnouncementHandler(BaseHandler):
    def get(self):
        db = SessionLocal()
        try:
            s_html = db.query(Setting).filter(Setting.key == 'bulletin_html').one_or_none()
            s_title = db.query(Setting).filter(Setting.key == 'bulletin_title').one_or_none()
            s_contacts = db.query(Setting).filter(Setting.key == 'admin_contacts').one_or_none()
            s_invites = db.query(Setting).filter(Setting.key == 'register_invite_codes').one_or_none()
            updated = None
            for s in (s_html, s_title):
                if s and s.updated_at:
                    if not updated or s.updated_at > updated:
                        updated = s.updated_at
            contacts = []
            if s_contacts and s_contacts.value:
                try:
                    data = json.loads(s_contacts.value)
                    if isinstance(data, list):
                        for item in data:
                            if not isinstance(item, dict):
                                continue
                            contacts.append({
                                'icon': str(item.get('icon') or ''),
                                'label': str(item.get('label') or ''),
                                'value': str(item.get('value') or ''),
                                'href': str(item.get('href') or ''),
                            })
                except Exception:
                    contacts = []
            invite_codes = []
            if s_invites and s_invites.value:
                try:
                    data = json.loads(s_invites.value)
                    if isinstance(data, list):
                        invite_codes = [str(item).strip() for item in data if str(item).strip()]
                except Exception:
                    invite_codes = []
            self.write({
                "html": s_html.value if s_html else "",
                "title": s_title.value if s_title and s_title.value else "公告栏",
                "updated_at": updated.isoformat() if updated else None,
                "contacts": contacts,
                "invite_codes": invite_codes,
            })
        finally:
            db.close()

    def put(self):
        cu = get_current_user(self)
        if not cu:
            self.set_status(401); self.finish({"detail": "未授权"}); return
        if cu["role"] not in ("admin", "superadmin"):
            self.set_status(403); self.finish({"detail": "无权限"}); return
        try:
            payload = json.loads(self.request.body or b"{}")
        except Exception:
            self.set_status(400); self.finish({"detail": "Invalid JSON"}); return
        html = payload.get("html")
        title = payload.get("title")
        contacts_payload = payload.get("contacts")
        if html is None and title is None:
            if contacts_payload is None:
                self.set_status(400); self.finish({"detail": "缺少更新内容"}); return
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            if html is not None:
                s = db.query(Setting).filter(Setting.key == 'bulletin_html').one_or_none()
                if not s:
                    s = Setting(key='bulletin_html', value=str(html), created_at=now, updated_at=now)
                    db.add(s)
                else:
                    s.value = str(html)
                    s.updated_at = now
                    db.add(s)
            if title is not None:
                st = db.query(Setting).filter(Setting.key == 'bulletin_title').one_or_none()
                if not st:
                    st = Setting(key='bulletin_title', value=str(title), created_at=now, updated_at=now)
                    db.add(st)
                else:
                    st.value = str(title)
                    st.updated_at = now
                    db.add(st)
            if contacts_payload is not None:
                cleaned_contacts = []
                if isinstance(contacts_payload, list):
                    for raw in contacts_payload:
                        if not isinstance(raw, dict):
                            continue
                        label = str(raw.get('label') or '').strip()
                        value = str(raw.get('value') or '').strip()
                        icon = str(raw.get('icon') or '').strip() or 'custom'
                        href = str(raw.get('href') or '').strip()
                        if not label and not value:
                            continue
                        cleaned_contacts.append({
                            "label": label,
                            "value": value,
                            "icon": icon,
                            "href": href,
                        })
                s_contacts = db.query(Setting).filter(Setting.key == 'admin_contacts').one_or_none()
                json_value = json.dumps(cleaned_contacts, ensure_ascii=False)
                if not s_contacts:
                    s_contacts = Setting(key='admin_contacts', value=json_value, created_at=now, updated_at=now)
                    db.add(s_contacts)
                else:
                    s_contacts.value = json_value
                    s_contacts.updated_at = now
                    db.add(s_contacts)
            invite_payload = payload.get("invite_codes")
            if invite_payload is not None:
                cleaned_invites = []
                if isinstance(invite_payload, list):
                    for raw in invite_payload:
                        code = str(raw or '').strip()
                        if code:
                            cleaned_invites.append(code)
                s_invites = db.query(Setting).filter(Setting.key == 'register_invite_codes').one_or_none()
                json_invites = json.dumps(cleaned_invites, ensure_ascii=False)
                if not s_invites:
                    s_invites = Setting(key='register_invite_codes', value=json_invites, created_at=now, updated_at=now)
                    db.add(s_invites)
                else:
                    s_invites.value = json_invites
                    s_invites.updated_at = now
                    db.add(s_invites)
            db.commit()
            # Record history snapshot (after commit so settings exist)
            try:
                s_html = db.query(Setting).filter(Setting.key == 'bulletin_html').one_or_none()
                s_title = db.query(Setting).filter(Setting.key == 'bulletin_title').one_or_none()
                hist = AnnouncementHistory(title=(s_title.value if s_title else None), html=(s_html.value if s_html else None), updated_by=str(cu.get("username")))
                db.add(hist)
                db.commit()
            except Exception:
                db.rollback()
            self.write({"ok": True})
        finally:
            db.close()


class AnnouncementHistoryHandler(BaseHandler):
    def get(self):
        cu = get_current_user(self)
        if not cu:
            self.set_status(401); self.finish({"detail": "未授权"}); return
        if cu["role"] not in ("admin", "superadmin"):
            self.set_status(403); self.finish({"detail": "无权限"}); return
        # optional ?limit=
        try:
            limit = int(self.get_query_argument("limit", default="20"))
        except Exception:
            limit = 20
        limit = max(1, min(100, limit))
        db = SessionLocal()
        try:
            rows = db.query(AnnouncementHistory).order_by(AnnouncementHistory.id.desc()).limit(limit).all()
            def to_dict(r: AnnouncementHistory):
                return {
                    "id": r.id,
                    "title": r.title,
                    "html": r.html,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
            self.write({"items": [to_dict(r) for r in rows]})
        finally:
            db.close()


class AnnouncementRevertHandler(BaseHandler):
    def post(self):
        cu = get_current_user(self)
        if not cu:
            self.set_status(401); self.finish({"detail": "未授权"}); return
        if cu["role"] not in ("admin", "superadmin"):
            self.set_status(403); self.finish({"detail": "无权限"}); return
        try:
            payload = json.loads(self.request.body or b"{}")
        except Exception:
            self.set_status(400); self.finish({"detail": "Invalid JSON"}); return
        hid = payload.get("id")
        if not hid:
            self.set_status(400); self.finish({"detail": "缺少字段 id"}); return
        db = SessionLocal()
        try:
            r = db.query(AnnouncementHistory).filter(AnnouncementHistory.id == hid).one_or_none()
            if not r:
                self.set_status(404); self.finish({"detail": "历史版本不存在"}); return
            now = datetime.utcnow()
            s_html = db.query(Setting).filter(Setting.key == 'bulletin_html').one_or_none()
            if not s_html:
                s_html = Setting(key='bulletin_html', value=r.html or '', created_at=now, updated_at=now)
            else:
                s_html.value = r.html or ''
                s_html.updated_at = now
            db.add(s_html)
            s_title = db.query(Setting).filter(Setting.key == 'bulletin_title').one_or_none()
            if not s_title:
                s_title = Setting(key='bulletin_title', value=r.title or '公告栏', created_at=now, updated_at=now)
            else:
                s_title.value = r.title or '公告栏'
                s_title.updated_at = now
            db.add(s_title)
            db.commit()
            # Add snapshot for the revert action as a new history record
            hist = AnnouncementHistory(title=s_title.value, html=s_html.value, updated_by=str(cu.get("username")))
            db.add(hist)
            db.commit()
            self.write({"ok": True})
        finally:
            db.close()


def make_app():
    init_db()
    settings = {
        "debug": os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"},
        "cookie_secret": os.getenv("COOKIE_SECRET", os.getenv("JWT_SECRET", "dev-cookie-secret-change-me")),
        "xsrf_cookies": False,
    }

    # Bootstrap default admin from env if provided
    try:
        ensure_default_admin()
    except Exception:
        pass

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
    .card {{ background:rgba(13,16,24,.35); border:1px solid rgba(255,255,255,.06); border-radius:14px; padding:14px; -webkit-backdrop-filter: blur(12px) saturate(140%); backdrop-filter: blur(12px) saturate(140%); }}
    .row {{ display:flex; gap:8px; align-items:center; }}
    .btn {{ background:#1a1e27; border:1px solid #232736; color:#e6e7eb; padding:8px 12px; border-radius:10px; cursor:pointer; }}
    .input, select {{ background:#0b0e14; border:1px solid #1a1e27; color:#e6e7eb; border-radius:10px; padding:8px 10px; }}
    table {{ width:100%; border-collapse: collapse; }}
    th, td {{ border-bottom:1px solid #1a1e27; padding:8px; text-align:left; }}
  </style>
  <script type=\"module\">
    import { createApp, ref, onMounted } from 'https://unpkg.com/vue@3/dist/vue.esm-browser.js';
    const STATUSES = __STATUSES__;
    const API_BASE = new URL('/orderapi', window.location.origin).toString().replace(/\/$/, '');
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
              wooden_crate: data.wooden_crate ?? null,
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
              wooden_crate: editing.value.wooden_crate,
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

        onMounted(()=>{
          // Bulletin: load, preview, save
          (async () => {
            try {
              const data = await api('/announcement');
              const ta = document.getElementById('bulletinTxt');
              const ti = document.getElementById('bulletinTitleInput');
              if (ta) ta.value = (data && data.html) || '';
              if (ti) ti.value = (data && data.title) || '公告栏';
              const prev = document.getElementById('bulletinPreview');
              if (prev) {
                const tmp = document.createElement('div'); tmp.innerHTML = ta ? ta.value : '';
                tmp.querySelectorAll('script').forEach(n=>n.remove());
                prev.innerHTML = tmp.innerHTML || '<div style="color:#a3a7b3">暂无内容</div>';
              }
            } catch(_) {}
            const ta = document.getElementById('bulletinTxt');
            const ti = document.getElementById('bulletinTitleInput');
            const prev = document.getElementById('bulletinPreview');
            if (ta) ta.addEventListener('input', () => {
              if (!prev) return;
              const tmp = document.createElement('div'); tmp.innerHTML = ta.value || '';
              tmp.querySelectorAll('script').forEach(n=>n.remove());
              prev.innerHTML = tmp.innerHTML || '<div style="color:#a3a7b3">暂无内容</div>';
            });
            const btn = document.getElementById('saveBulletinBtn');
            if (btn && ta) btn.addEventListener('click', async () => {
              msg.value = '保存公告中...';
              try { await api('/announcement', { method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ html: ta.value || '', title: (ti && ti.value) || undefined }) }); msg.value='公告已保存'; }
              catch(e){ msg.value = e.message; }
            });
          })();
        });
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
              <label>是否打木架
                <select class=\"input\" v-model=\"editing.wooden_crate\">
                  <option :value=\"null\">未设置</option>
                  <option :value=\"true\">是</option>
                  <option :value=\"false\">否</option>
                </select>
              </label>
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

          <div class=\"card\" style=\"margin-top:12px;\">
            <h3>公告栏管理</h3>
            <div class=\"row\" style=\"gap:8px; align-items:center; margin-bottom:8px;\">
              <label style=\"display:grid; gap:6px; width:100%;\">标题
                <input id=\"bulletinTitleInput\" class=\"input\" placeholder=\"如：重要通知\" />
              </label>
            </div>
            <div class=\"row\" style=\"gap:8px; align-items:flex-start;\">
              <textarea id=\"bulletinTxt\" class=\"input\" style=\"width:100%; min-height:160px;\" placeholder=\"支持 HTML 富文本与图片 <img> 标签\"></textarea>
              <button class=\"btn\" id=\"saveBulletinBtn\">保存公告</button>
            </div>
            <div class=\"subtitle tight\" style=\"margin-top:8px;\">预览</div>
            <div id=\"bulletinPreview\" style=\"background:#0b0f16; border:1px solid #182031; border-radius:8px; padding:10px; min-height:40px;\"></div>
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
        (r"/orderapi/health", HealthHandler),
        (r"/orderapi/register/check-username", UsernameCheckHandler),
        (r"/orderapi/register/random-username", RandomUsernameHandler),
        (r"/orderapi/register", RegisterHandler),
        (r"/orderapi/login", LoginHandler),
        (r"/orderapi/orders", OrdersHandler),
        (r"/orderapi/orders/by-no/([A-Za-z0-9\-_]+)", OrderByNoHandler),
        (r"/orderapi/orders/bulk", OrdersBulkDeleteHandler),
        (r"/orderapi/orders/export", OrdersExportHandler),
        (r"/orderapi/import/excel", ImportExcelHandler),
        (r"/orderapi/announcement", AnnouncementHandler),
        (r"/orderapi/announcement/history", AnnouncementHistoryHandler),
        (r"/orderapi/announcement/revert", AnnouncementRevertHandler),
        (r"/orderapi/admin/users", AdminUsersHandler),
        (r"/orderapi/admin/users/([0-9]+)", AdminUserDetailHandler),
        (r"/orderapi/user/codes", MeCodesHandler),
        (r"/orderapi/user/change-password", UserPasswordHandler),
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
