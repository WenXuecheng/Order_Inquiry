import os
from urllib.parse import quote, unquote
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.engine.url import make_url


class Base(DeclarativeBase):
    pass

############################################################
# Database configuration: read from environment (.env)
############################################################
def _getenv_clean(*names: str):
    for n in names:
        v = os.getenv(n)
        if v is None:
            continue
        s = v.strip()
        if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
            s = s[1:-1].strip()
        if s:
            return s
    return None


def _build_url_from_env_parts() -> str | None:
    driver = _getenv_clean("driver", "DB_DRIVER") or "mysql+pymysql"
    username = _getenv_clean("username", "DB_USERNAME", "DATABASE_USERNAME")
    password = _getenv_clean("password", "DB_PASSWORD", "DATABASE_PASSWORD") or ""
    host = _getenv_clean("host", "DB_HOST", "DATABASE_HOST")
    port = _getenv_clean("port", "DB_PORT", "DATABASE_PORT") or "3306"
    database = _getenv_clean("database", "DB_NAME", "DATABASE_NAME")
    charset = _getenv_clean("charset", "DB_CHARSET") or "utf8mb4"
    if username and host and database:
        user_enc = quote(username, safe="")
        pwd_enc = quote(password, safe="")
        return f"{driver}://{user_enc}:{pwd_enc}@{host}:{port}/{database}?charset={charset}"
    return None


def get_database_url() -> str:
    """Build DB URL with sane defaults.

    Priority:
    1) Use `DATABASE_URL` if set.
    2) Else, build from split env fields (username/password/host/port/database; optional driver/charset).
    3) Else, fall back to built‑in DEFAULT_DB config.
    """
    env_url = _getenv_clean("DATABASE_URL")
    if env_url:
        return env_url
    built = _build_url_from_env_parts()
    if built:
        return built
    # Default fallback (dev/local)
    DEFAULT_DB = {
        "driver": "mysql+pymysql",
        "username": "user",
        "password": "pass",
        "host": "localhost",
        "port": "3306",
        "database": "automatica",
        "charset": "utf8mb4",
    }
    user_enc = quote(DEFAULT_DB["username"], safe="")
    pwd_enc = quote(DEFAULT_DB["password"], safe="")
    return (
        f"{DEFAULT_DB['driver']}://{user_enc}:{pwd_enc}@"
        f"{DEFAULT_DB['host']}:{DEFAULT_DB['port']}/"
        f"{DEFAULT_DB['database']}?charset={DEFAULT_DB['charset']}"
    )


def _mask_secret(s: str, reveal: bool = False) -> str:
    if reveal:
        return s
    if not s:
        return ""
    if len(s) <= 4:
        return "*" * len(s)
    return s[:2] + "*" * (len(s) - 4) + s[-2:]


def db_connection_summary(reveal_password: bool = False) -> str:
    """Return a human-friendly summary of the DB connection (password masked by default)."""
    url = get_database_url()
    try:
        u = make_url(url)
        user = unquote(u.username or "")
        pwd = unquote(u.password or "")
        host = u.host or ""
        port = str(u.port or "")
        db = u.database or ""
        driver = u.drivername or ""
        return (
            f"driver={driver} host={host} port={port} db={db} "
            f"user={user} password={_mask_secret(pwd, reveal_password)}"
        )
    except Exception:
        # Fallback to raw url if parsing fails
        return f"url={url}"


# Print DB connection info at startup (masking password unless LOG_DB_CREDS=true)
_reveal = (os.getenv("LOG_DB_CREDS", "false").lower() in {"1", "true", "yes"})
print("[db] " + db_connection_summary(reveal_password=_reveal))

engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    from .models import Order
    Base.metadata.create_all(bind=engine)
