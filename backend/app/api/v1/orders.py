from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.exceptions import (
    BadRequestException,
    CouponNotAssignedException,
    ForbiddenException,
    InsufficientStockException,
    InvalidCouponException,
    NotFoundException,
    ProductNotFoundException,
)
from app.models.user import User
from app.schemas.order import (
    OrderCreate,
    OrderItemResponse,
    OrderResponse,
    OrderUpdate,
)
from app.services.order_service import OrderService

order_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
UserDb = Annotated[User, Depends(get_current_user)]


def get_order_service(db: DbSession) -> OrderService:
    return OrderService(db)


def _traduzir_value_error(exc: ValueError) -> BadRequestException:
    """Converte os ``ValueError`` do service no erro HTTP correspondente.

    O ``OrderService`` sinaliza falhas de negócio com ``ValueError`` genérico.
    Sem esta tradução o handler global devolveria 500 para casos que o cliente
    precisa distinguir (404 endereço/produto, 403 dono, 409 estoque, 400 cupom).
    """
    msg = str(exc)

    if "not owned by user" in msg:
        return ForbiddenException(msg)

    if "Insufficient stock" in msg:
        # Formato: "Insufficient stock for 'Título'. Available: N"
        titulo = msg.split("'", 2)[1] if "'" in msg else "produto"
        disponivel = 0
        if "Available:" in msg:
            try:
                disponivel = int(msg.split("Available:")[1].split(",")[0].strip())
            except (IndexError, ValueError):
                disponivel = 0
        return InsufficientStockException(titulo, disponivel)

    if "No product found" in msg or "is not active" in msg:
        return ProductNotFoundException()

    if "not assigned to user" in msg:
        # Cupom válido, porém não resgatado (vinculado) por este usuário.
        # Usa a mensagem padrão em português da exceção, não o texto cru inglês.
        return CouponNotAssignedException()

    if "coupon" in msg.lower():
        return InvalidCouponException(msg)

    if "No order" in msg or "No items" in msg or "No address" in msg:
        return NotFoundException(msg)

    return BadRequestException(msg)


@order_router.post(
    "/create",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo pedido para o usuário autenticado",
)
def create_order(
    data: OrderCreate, user: UserDb, db: DbSession
) -> OrderResponse:
    try:
        return get_order_service(db).create(user.id, data)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@order_router.get(
    "/list",
    response_model=list[OrderResponse],
    summary="Lista todos os pedidos do usuário autenticado",
)
def list_orders(user: UserDb, db: DbSession) -> list:
    try:
        return get_order_service(db).get_by_user_id(user.id)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@order_router.get(
    "/get/{order_id}",
    response_model=OrderResponse,
    summary="Busca um pedido pelo ID",
)
def get_order(order_id: int, user: UserDb, db: DbSession) -> OrderResponse:
    try:
        return get_order_service(db).get_by_id(order_id, user.id)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@order_router.get(
    "/items/{order_id}",
    response_model=list[OrderItemResponse],
    summary="Lista os itens de um pedido",
)
def get_order_items(
    order_id: int, user: UserDb, db: DbSession
) -> list:
    try:
        return get_order_service(db).get_with_items(order_id, user.id)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@order_router.patch(
    "/update/{order_id}",
    response_model=OrderResponse,
    summary="Atualiza um pedido",
)
def update_order(
    order_id: int,
    data: OrderUpdate,
    user: UserDb,
    db: DbSession,
) -> OrderResponse:
    try:
        return get_order_service(db).update(order_id, user.id, data)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@order_router.delete(
    "/delete/{order_id}",
    response_model=OrderResponse,
    summary="Exclui um pedido",
)
def delete_order(
    order_id: int, user: UserDb, db: DbSession
) -> OrderResponse:
    try:
        return get_order_service(db).delete(order_id, user.id)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc
