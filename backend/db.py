import os
from urllib.parse import quote
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


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
    """Only read DB config from environment (.env).

    - If `DATABASE_URL` is set, use it as-is.
    - Else, try to build from split fields (username/password/host/port/database; optional driver/charset).
    - Else, raise a clear error without using code defaults.
    """
    env_url = _getenv_clean("DATABASE_URL")
    if env_url:
        return env_url
    built = _build_url_from_env_parts()
    if built:
        return built
    raise RuntimeError(
        "DATABASE_URL is not set and required DB fields are missing. "
        "Set DATABASE_URL, or set username/password/host/port/database (optionally driver, charset) in .env."
    )


engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    from .models import Order
    Base.metadata.create_all(bind=engine)
