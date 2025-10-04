import os
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext


SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "12"))

# Use pbkdf2_sha256 to avoid external bcrypt dependency
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def _db_authenticate(username: str, password: str) -> bool:
    try:
        from .db import SessionLocal
        from .models import AdminUser
        db = SessionLocal()
        try:
            u = db.query(AdminUser).filter(AdminUser.username == username).one_or_none()
            if not u:
                return False
            return verify_password(password, u.password_hash)
        finally:
            db.close()
    except Exception:
        return False


def authenticate_admin(username: str, password: str) -> bool:
    # Prefer DB auth when table/record exists; fall back to env for bootstrap
    if _db_authenticate(username, password):
        return True
    admin_user = os.getenv("ADMIN_USERNAME", "admin")
    hashed = os.getenv("ADMIN_PASSWORD_HASH")
    plain = os.getenv("ADMIN_PASSWORD")
    if username != admin_user:
        return False
    if hashed:
        return verify_password(password, hashed)
    if plain:
        return password == plain
    # fallback demo-only password (change in prod)
    return password == "admin123"


def ensure_default_admin():
    """Ensure a default admin user exists in DB when ADMIN_PASSWORD or ADMIN_PASSWORD_HASH set.

    Will not overwrite existing users.
    """
    try:
        admin_user = os.getenv("ADMIN_USERNAME", "admin")
        hashed_env = os.getenv("ADMIN_PASSWORD_HASH")
        plain_env = os.getenv("ADMIN_PASSWORD")
        if not (hashed_env or plain_env):
            return
        from .db import SessionLocal
        from .models import AdminUser
        db = SessionLocal()
        try:
            existing = db.query(AdminUser).filter(AdminUser.username == admin_user).one_or_none()
            if existing:
                changed = False
                if existing.role != "superadmin":
                    existing.role = "superadmin"
                    changed = True
                if hasattr(existing, "is_active") and existing.is_active is False:
                    existing.is_active = True
                    changed = True
                if hashed_env:
                    if existing.password_hash != hashed_env:
                        existing.password_hash = hashed_env
                        changed = True
                elif plain_env:
                    try:
                        if not verify_password(plain_env, existing.password_hash):
                            existing.password_hash = get_password_hash(plain_env)
                            changed = True
                    except Exception:
                        existing.password_hash = get_password_hash(plain_env)
                        changed = True
                if changed:
                    db.add(existing)
                    db.commit()
                return
            pwd_hash = hashed_env or get_password_hash(plain_env)
            db.add(AdminUser(username=admin_user, password_hash=pwd_hash, role="superadmin", is_active=True))
            db.commit()
        finally:
            db.close()
    except Exception:
        # best-effort; do not crash startup
        return


def create_access_token(subject: str, role: Optional[str] = None, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode = {"sub": subject, "exp": datetime.utcnow() + expires_delta}
    if role:
        to_encode["role"] = role
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
