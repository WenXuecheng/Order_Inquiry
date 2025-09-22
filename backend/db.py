import os
from urllib.parse import quote
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.engine.url import make_url


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
    "database": "automatica",            # <- set your DB name
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


def _candidate_urls():
    urls = []
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        urls.append(("env", env_url))
    try:
        if DB_CONFIG.get("database") and DB_CONFIG.get("username") and DB_CONFIG.get("host"):
            urls.append(("config", _build_url_from_config(DB_CONFIG)))
    except Exception:
        pass
    urls.append(("default", "mysql+pymysql://user:pass@localhost:3306/automatica"))
    return urls


def _url_brief(url: str) -> str:
    try:
        u = make_url(url)
        host = u.host or ""
        port = f":{u.port}" if u.port else ""
        db = u.database or ""
        return f"{u.drivername}://{host}{port}/{db}"
    except Exception:
        return url


def _create_engine_with_fallback():
    last_err = None
    for source, url in _candidate_urls():
        try:
            engine = create_engine(url, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"[db] using {source} -> {_url_brief(url)}")
            return engine
        except Exception as e:
            last_err = e
            print(f"[db] failed {source} -> {_url_brief(url)}: {e}")
            continue
    raise last_err  # type: ignore[misc]


engine = _create_engine_with_fallback()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    from .models import Order
    Base.metadata.create_all(bind=engine)
