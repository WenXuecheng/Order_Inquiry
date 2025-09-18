from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List


class OrderOut(BaseModel):
    id: int
    order_no: str
    group_code: Optional[str]
    weight_kg: Optional[float]
    shipping_fee: Optional[float]
    status: str
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderUpdate(BaseModel):
    group_code: Optional[str | None] = Field(default=None)
    weight_kg: Optional[float | None] = Field(default=None)
    shipping_fee: Optional[float | None] = Field(default=None)
    status: Optional[str | None] = Field(default=None)


class OrdersResponse(BaseModel):
    orders: List[OrderOut]
    totals: dict


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

