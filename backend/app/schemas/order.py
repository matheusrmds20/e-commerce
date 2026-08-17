from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from app.models.order import OrderStatus


class OrderItemCreate(BaseModel):

    product_id: int = Field(description="ID do produto")
    quantity: int = Field(..., ge=1, description="Quantidade")


class OrderItemResponse(BaseModel):
    id: int
    order_id: int
    product_id: int
    quantity: int
    price: float

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):

    address_id: int = Field(description="ID do endereço")
    coupon_id: int | None = Field(None, description="ID do cupom")
    notes: str | None = Field(None, max_length=500, description="Observações")
    items: list[OrderItemCreate] = Field(default_factory=list)


class OrderUpdate(BaseModel):

    address_id: int | None = None
    status: OrderStatus | None = None
    coupon_id: int | None = Field(None, description="ID do cupom")
    notes: str | None = Field(None, max_length=500)
    items: list[OrderItemCreate] | None = None


class OrderResponse(BaseModel):
    
    id: int
    user_id: int
    address_id: int
    coupon_id: int | None
    notes: str | None
    status: OrderStatus
    subtotal: float
    discount_amount: float
    shipping_cost: float
    total: float
    created_at: datetime
    updated_at: datetime
    order_items: list[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)
