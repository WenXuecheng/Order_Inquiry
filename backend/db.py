import os
from urllib.parse import quote
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


class Base(DeclarativeBase):
    pass

############################################################
# Direct DB configuration (edit here)
############################################################
# You can configure DB credentials directly below. These values
# will be used to construct the SQLAlchemy URL automatically
# with proper URL-encoding for username/password.
DB_CONFIG = {
    "driver": "mysql+pymysql",        # e.g. "mysql+pymysql" or "postgresql+psycopg2"
    "username": "dbauser",           # <- set your DB username
    "password": "JHKDSJrShkjSsdfsd348958234/.$#@54",  # <- set your DB password
    "host": "localhost",             # <- set your DB host/IP
    "port": 3306,                     # <- set your DB port (int)
    "database": "testdb",            # <- set your DB name
    "charset": "utf8mb4",            # optional (for MySQL-family)
}


def _build_url_from_config(conf: dict) -> str:
    driver = (conf.get("driver") or "mysql+pymysql").strip()
    username = str(conf.get("username") or "")
    password = str(conf.get("password") or "")
    host = (conf.get("host") or "localhost").strip()
    port = int(conf.get("port") or 3306)
    database = (conf.get("database") or "").strip()
    charset = (conf.get("charset") or "utf8mb4").strip()
    user_enc = quote(username, safe="")
    pwd_enc = quote(password, safe="")
    return f"{driver}://{user_enc}:{pwd_enc}@{host}:{port}/{database}?charset={charset}"


def get_database_url() -> str:
    """Return SQLAlchemy URL built from DB_CONFIG.

    If DB_CONFIG is incomplete (e.g., no database), fall back to
    DATABASE_URL env var, then to a local default.
    """
    try:
        if DB_CONFIG.get("database") and DB_CONFIG.get("username") and DB_CONFIG.get("host"):
            return _build_url_from_config(DB_CONFIG)
    except Exception:
        pass

    # Fallbacks
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    return "mysql+pymysql://user:pass@localhost:3306/automatica"


engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    from .models import Order
    Base.metadata.create_all(bind=engine)
