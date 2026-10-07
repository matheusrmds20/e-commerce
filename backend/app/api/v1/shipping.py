from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.shipping import (
    ShippingApplyRequest,
    ShippingApplyResponse,
    ShippingCalculateResponse,
)
from app.services.shipping_service import ShippingService

shipping_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
UserDb = Annotated[User, Depends(get_current_user)]


def get_shipping_service(db: DbSession) -> ShippingService:
    return ShippingService(db)


@shipping_router.post(
    "/calculate/{order_id}",
    response_model=ShippingCalculateResponse,
    summary="Cota o frete de um pedido via Melhor Envio",
)
def calculate_shipping(order_id: int, user: UserDb, db: DbSession):
    """Calcula as opções de frete para um pedido do usuário autenticado."""
    return get_shipping_service(db).calculate(order_id, user.id)


@shipping_router.post(
    "/apply",
    response_model=ShippingApplyResponse,
    summary="Aplica o valor de frete escolhido a um pedido",
)
def apply_shipping(data: ShippingApplyRequest, user: UserDb, db: DbSession):
    """Grava o ``shipping_cost`` de um pedido e recalcula o total.

    ``status`` opcional permite, quando informado, avançar o pedido no fluxo de
    envio (ex.: ``processing``) no mesmo momento da aplicação do frete.
    """
    # Demonstração do contrato: o status de envio pode ser controlado pelo
    # endpoint admin existente (/admin/orders/{id}/status) ou aqui ao aplicar.
    return get_shipping_service(db).apply_to_order(
        order_id=data.order_id,
        user_id=user.id,
        price=data.price,
        delivery_time=data.delivery_time,
    )
