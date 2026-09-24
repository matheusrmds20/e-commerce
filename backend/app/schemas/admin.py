from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict


class LowStockProduct(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    price: float
    stock_qty: int
    category_name: str | None = None


class WeeklySale(BaseModel):
    label: str
    amount: float
    orders_count: int


class DashboardStatsResponse(BaseModel):
    total_revenue: float
    total_orders: int
    pending_orders: int
    total_products: int
    total_stock: int
    average_ticket: float
    low_stock_products: list[LowStockProduct]
    weekly_sales: list[WeeklySale]


class AdminOrderUser(BaseModel):
    id: int
    full_name: str
    email: str


class AdminOrderItem(BaseModel):
    product_id: int
    product_title: str
    quantity: int
    unit_price: float
    subtotal: float


class AdminOrderResponse(BaseModel):
    id: int
    user_id: int
    user: AdminOrderUser | None = None
    status: str
    subtotal: float
    discount_amount: float
    shipping_cost: float
    total: float
    notes: str | None = None
    items_count: int = 0
    items_summary: str = ""
    created_at: datetime
    updated_at: datetime


class AdminOrderStatusUpdate(BaseModel):
    status: str


class AdminUserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    orders_count: int = 0
    created_at: datetime
