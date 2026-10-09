from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import Page
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderUpdate,
)
from app.services.order_service import OrderService

order_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
UserDb = Annotated[User, Depends(get_current_user)]

PageNumber = Annotated[int, Query(ge=1, description="Página (começa em 1)")]
PerPage = Annotated[
    int, Query(ge=1, le=100, description="Itens por página (max 100)")
]


def get_order_service(db: DbSession) -> OrderService:
    return OrderService(db)


@order_router.post(
    "/create",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo pedido para o usuário autenticado",
)
def create_order(
    data: OrderCreate, user: UserDb, db: DbSession
) -> OrderResponse:
    return get_order_service(db).create(user.id, data)


@order_router.get(
    "/list",
    response_model=Page[OrderResponse],
    summary="Lista os pedidos do usuário autenticado (paginado)",
)
def list_orders(
    user: UserDb,
    db: DbSession,
    page: PageNumber = 1,
    per_page: PerPage = 20,
) -> dict:
    """Pedidos paginados no envelope ``{ data, meta }``.

    Antes retornava a lista completa: uma conta antiga baixava o histórico
    inteiro a cada carregamento. Agora o banco aplica ``offset``/``limit`` e o
    ``meta.total`` reflete o total real.
    """
    return get_order_service(db).get_paginated_by_user_id(
        user.id, page, per_page
    )


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
    return get_order_service(db).update(order_id, user.id, data)


@order_router.delete(
    "/delete/{order_id}",
    response_model=OrderResponse,
    summary="Exclui um pedido",
)
def delete_order(
    order_id: int, user: UserDb, db: DbSession
) -> OrderResponse:
    return get_order_service(db).delete(order_id, user.id)


@order_router.post(
    "/send-confirmation-email",
    summary="Envia um email de confirmação de pedido",
)
async def send_order_confirmation_email(
    order_id: int, user: UserDb, db: DbSession
):

    return get_order_service(db).send_confirmation_email(order_id, user)


@order_router.get(
    "/send-confirmation-email/status/{task_id}",
    summary="Consulta o status de uma tarefa de envio de email de confirmação",
)
async def get_task_status(
    task_id: str,
    user: UserDb,
    db: DbSession,
):

    return await get_order_service(db).get_task_status(task_id)


@order_router.get(
    "/{order_id}/comprovante",
    summary="Baixa o comprovante PDF do pedido (somente o dono)",
    # Sem response_model: devolvemos um FileResponse (arquivo binário).
)
def download_receipt(
    order_id: int,
    user: UserDb,
    db: DbSession,
):
    from fastapi.responses import FileResponse

    path = get_order_service(db).get_receipt_path(order_id, user.id)

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"comprovante_order_{order_id}.pdf",
    )
