from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Float, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


STATUSES = [
    "打包发出",
    "在我国海岸等待检查",
    "已发往俄罗斯",
    "等待俄罗斯关口检查",
    "转运到彼得堡（1-3天）",
    "已到达彼得堡",
    "已结算",
]


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    group_code: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    weight_kg: Mapped[float | None] = mapped_column(Float(asdecimal=False), nullable=True)
    shipping_fee: Mapped[float | None] = mapped_column(Float(asdecimal=False), nullable=True)
    status: Mapped[str] = mapped_column(String(64), default=STATUSES[0])
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
