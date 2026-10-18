from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.limiter import limiter
from app.models.user import User
from app.schemas.shipping import (
    ShippingApplyRequest,
    ShippingApplyResponse,
    ShippingCalculateResponse,
    ShippingQuoteRequest,
    ShippingQuoteResponse,
)
from app.services.shipping_service import ShippingService

shipping_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
UserDb = Annotated[User, Depends(get_current_user)]


def get_shipping_service(db: DbSession) -> ShippingService:
    return ShippingService(db)


@shipping_router.post(
    "/quote",
    response_model=ShippingQuoteResponse,
    summary="Cota o frete do carrinho do usuário por CEP (sem criar pedido)",
)
@limiter.limit("30/minute")
def quote_shipping(
    request: Request,
    data: ShippingQuoteRequest,
    user: UserDb,
    db: DbSession,
):

    return get_shipping_service(db).quote(user.id, data.postal_code)


@shipping_router.post(
    "/calculate/{order_id}",
    response_model=ShippingCalculateResponse,
    summary="Cota o frete de um pedido via Melhor Envio",
)
def calculate_shipping(order_id: int, user: UserDb, db: DbSession):

    return get_shipping_service(db).calculate(order_id, user.id)


@shipping_router.post(
    "/apply",
    response_model=ShippingApplyResponse,
    summary="Aplica o valor de frete escolhido a um pedido",
)
def apply_shipping(data: ShippingApplyRequest, user: UserDb, db: DbSession):

    return get_shipping_service(db).apply_to_order(
        order_id=data.order_id,
        user_id=user.id,
        price=data.price,
        delivery_time=data.delivery_time,
    )
