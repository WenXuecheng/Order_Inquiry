import os
from urllib.parse import quote
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


class Base(DeclarativeBase):
    pass


def _getenv_clean(*names: str, default: str | None = None) -> str | None:
    """Return the first non-empty env var value among names, with surrounding quotes stripped."""
    for name in names:
        val = os.getenv(name)
        if val is None:
            continue
        s = val.strip()
        if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
            s = s[1:-1].strip()
        if s:
            return s
    return default


def get_database_url() -> str:
    """Build SQLAlchemy URL.

    Priority:
    1) If split credentials provided (username/password/host/port/database), build MySQL URL and URL-encode creds.
    2) Else, use DATABASE_URL as-is if provided.
    3) Else, fallback to a sensible default MySQL URL.
    """
    # Prefer explicit parts if provided
    username = _getenv_clean("username", "DB_USERNAME", "DATABASE_USERNAME")
    password = _getenv_clean("password", "DB_PASSWORD", "DATABASE_PASSWORD")
    host = _getenv_clean("host", "DB_HOST", "DATABASE_HOST")
    port = _getenv_clean("port", "DB_PORT", "DATABASE_PORT")
    database = _getenv_clean("database", "DB_NAME", "DATABASE_NAME")
    driver = _getenv_clean("driver", "DB_DRIVER", default="mysql+pymysql")
    charset = _getenv_clean("charset", "DB_CHARSET", default="utf8mb4")

    if username and host and database:
        user_enc = quote(username, safe="")
        # Password can be empty; still include ':' for clarity when user provided username
        pwd_enc = quote(password or "", safe="")
        host_part = host
        port_part = f":{port}" if port else ":3306"
        return f"{driver}://{user_enc}:{pwd_enc}@{host_part}{port_part}/{database}?charset={charset}"

    # Fallback to DATABASE_URL if present
    url = _getenv_clean("DATABASE_URL")
    if url:
        return url

    # Default placeholder (dev)
    return "mysql+pymysql://user:pass@localhost:3306/automatica"


engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    from .models import Order
    Base.metadata.create_all(bind=engine)
