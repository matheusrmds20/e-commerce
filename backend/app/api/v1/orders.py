from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.order import (
    OrderCreate,
    OrderItemResponse,
    OrderResponse,
    OrderUpdate,
)
from app.services.order_service import OrderService

order_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
UserId = Annotated[int, Query(description="ID do usuário dono do pedido")]


def get_order_service(db: DbSession) -> OrderService:
    return OrderService(db)


@order_router.post(
    "/create",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo pedido para o usuário",
)
def create_order(
    data: OrderCreate, user_id: UserId, db: DbSession
) -> OrderResponse:
    return get_order_service(db).create(user_id, data)


@order_router.get(
    "/list",
    response_model=list[OrderResponse],
    summary="Lista todos os pedidos do usuário",
)
def list_orders(user_id: UserId, db: DbSession) -> list:
    return get_order_service(db).get_by_user_id(user_id)


@order_router.get(
    "/get/{order_id}",
    response_model=OrderResponse,
    summary="Busca um pedido pelo ID",
)
def get_order(order_id: int, user_id: UserId, db: DbSession) -> OrderResponse:
    return get_order_service(db).get_by_id(order_id, user_id)


@order_router.get(
    "/items/{order_id}",
    response_model=list[OrderItemResponse],
    summary="Lista os itens de um pedido",
)
def get_order_items(
    order_id: int, user_id: UserId, db: DbSession
) -> list:
    return get_order_service(db).get_with_items(order_id, user_id)


@order_router.patch(
    "/update/{order_id}",
    response_model=OrderResponse,
    summary="Atualiza um pedido",
)
def update_order(
    order_id: int,
    data: OrderUpdate,
    user_id: UserId,
    db: DbSession,
) -> OrderResponse:
    return get_order_service(db).update(order_id, user_id, data)


@order_router.delete(
    "/delete/{order_id}",
    response_model=OrderResponse,
    summary="Exclui um pedido",
)
def delete_order(
    order_id: int, user_id: UserId, db: DbSession
) -> OrderResponse:
    return get_order_service(db).delete(order_id, user_id)
