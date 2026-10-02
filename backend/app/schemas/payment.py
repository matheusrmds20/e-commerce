from datetime import datetime

from pydantic import BaseModel


class PaymentCreate(BaseModel):
    provider: str
    provider_payment_id: str | None = None
    amount: float
    currency: str
    status: str
    order_id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

class PaymentResponse(BaseModel):
    id: int
    provider: str
    provider_payment_id: str | None = None
    amount: float
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime
    order_id: int

    model_config = {"from_attributes": True}


class PaymentCheckoutResponse(BaseModel):
    id: int
    payment_id: int
    checkout_url: str


class WebhookResponse(BaseModel):
    status: str
