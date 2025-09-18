import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


class Base(DeclarativeBase):
    pass


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL", "mysql+pymysql://user:pass@localhost:3306/automatica")
    return url


engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    from .models import Order
    Base.metadata.create_all(bind=engine)

