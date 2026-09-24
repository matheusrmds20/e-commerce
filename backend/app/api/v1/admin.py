from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.exceptions import BadRequestException, NotFoundException
from app.schemas.admin import (
    AdminOrderResponse,
    AdminOrderStatusUpdate,
    AdminUserResponse,
    DashboardStatsResponse,
)
from app.services.admin_service import AdminService

admin_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]


def get_admin_service(db: DbSession) -> AdminService:
    return AdminService(db)


@admin_router.get(
    "/dashboard/stats",
    response_model=DashboardStatsResponse,
    summary="Obtém as métricas consolidadas do painel administrativo",
)
def get_dashboard_stats(db: DbSession) -> DashboardStatsResponse:
    return get_admin_service(db).get_dashboard_stats()


@admin_router.get(
    "/orders",
    response_model=list[AdminOrderResponse],
    summary="Lista todos os pedidos de todos os clientes no sistema",
)
def list_all_orders(
    db: DbSession,
    page: Annotated[int, Query(ge=1, description="Página")] = 1,
    per_page: Annotated[int, Query(ge=1, le=100, description="Itens por página")] = 50,
    status_filter: Annotated[
        str | None, Query(alias="status", description="Filtrar por status")
    ] = None,
) -> list[AdminOrderResponse]:
    return get_admin_service(db).list_all_orders(
        page=page, per_page=per_page, status_filter=status_filter
    )


@admin_router.patch(
    "/orders/{order_id}/status",
    response_model=AdminOrderResponse,
    summary="Atualiza o status de entrega/processamento de um pedido",
)
def update_order_status(
    order_id: int,
    data: AdminOrderStatusUpdate,
    db: DbSession,
) -> AdminOrderResponse:
    try:
        return get_admin_service(db).update_order_status(
            order_id=order_id, new_status=data.status
        )
    except ValueError as exc:
        msg = str(exc)
        if "não encontrado" in msg:
            raise NotFoundException(msg)
        raise BadRequestException(msg)


@admin_router.get(
    "/users",
    response_model=list[AdminUserResponse],
    summary="Lista todos os usuários e clientes cadastrados",
)
def list_users(db: DbSession) -> list[AdminUserResponse]:
    return get_admin_service(db).list_users()
