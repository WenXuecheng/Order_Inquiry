import os
import tempfile
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func

from .db import SessionLocal, init_db
from .models import Order, STATUSES
from .schemas import OrdersResponse, OrderOut, OrderUpdate, LoginRequest, LoginResponse
from .auth import authenticate_admin, create_access_token, verify_token
from .importer import import_excel


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


security = HTTPBearer(auto_error=False)


def get_admin_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if not credentials or credentials.scheme.lower() != 'bearer':
        raise HTTPException(status_code=401, detail="未授权")
    subject = verify_token(credentials.credentials)
    if not subject:
        raise HTTPException(status_code=401, detail="令牌无效或过期")
    return subject


app = FastAPI(title="Automatica 订单查询 API")

# CORS for static site on GitHub Pages or custom domain
origins = [
    os.getenv("CORS_ALLOW_ORIGINS", "*")
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/api/health")
def health():
    return {"ok": True, "time": datetime.utcnow().isoformat()}


@app.post("/api/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    if not authenticate_admin(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token(subject=payload.username)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/api/orders", response_model=OrdersResponse)
def get_orders(code: str, db: Session = Depends(get_db)):
    q = db.query(Order)
    # A means unclassified
    if code == "A":
        q = q.filter((Order.group_code == None) | (Order.group_code == ""))
    else:
        q = q.filter(Order.group_code == code)

    orders = q.order_by(Order.updated_at.desc()).all()

    # totals
    total_count = len(orders)
    total_weight = sum([o.weight_kg or 0.0 for o in orders])
    # shipping fee: prefer stored; else compute weight * RATE_PER_KG
    rate = float(os.getenv("RATE_PER_KG", "0"))
    total_fee = 0.0
    for o in orders:
        if o.shipping_fee is not None:
            total_fee += float(o.shipping_fee)
        else:
            total_fee += (o.weight_kg or 0.0) * rate

    return {
        "orders": [OrderOut.model_validate(o).model_dump() for o in orders],
        "totals": {
            "count": total_count,
            "total_weight": round(total_weight, 3),
            "total_shipping_fee": round(total_fee, 2),
        },
    }


@app.get("/api/orders/by-no/{order_no}", response_model=OrderOut)
def get_order_by_no(order_no: str, db: Session = Depends(get_db)):
    o = db.query(Order).filter(Order.order_no == order_no).one_or_none()
    if not o:
        raise HTTPException(status_code=404, detail="订单不存在")
    return OrderOut.model_validate(o)


@app.put("/api/orders/by-no/{order_no}", response_model=OrderOut)
def update_order_by_no(order_no: str, payload: OrderUpdate, db: Session = Depends(get_db), user: str = Depends(get_admin_user)):
    o = db.query(Order).filter(Order.order_no == order_no).one_or_none()
    if not o:
        raise HTTPException(status_code=404, detail="订单不存在")
    if payload.group_code is not None:
        o.group_code = payload.group_code
    if payload.weight_kg is not None:
        o.weight_kg = payload.weight_kg
    if payload.shipping_fee is not None:
        o.shipping_fee = payload.shipping_fee
    if payload.status is not None:
        if payload.status not in STATUSES:
            raise HTTPException(status_code=400, detail="状态非法")
        o.status = payload.status
    o.updated_at = datetime.utcnow()
    db.add(o)
    db.commit()
    db.refresh(o)
    return OrderOut.model_validate(o)


@app.post("/api/import/excel")
def import_orders_excel(file: UploadFile = File(...), db: Session = Depends(get_db), user: str = Depends(get_admin_user)):
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="请上传 .xlsx 文件")
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=True) as tmp:
        content = file.file.read()
        tmp.write(content)
        tmp.flush()
        stats = import_excel(db, tmp.name)
    return stats

