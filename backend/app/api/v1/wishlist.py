from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.schemas.wishlist import WishlistCreate, WishlistResponse, WishlistUpdate
from app.services.wishlist_service import WishlistService

wishlist_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
UserId = Annotated[int, Query(description="ID do usuário dono da wishlist")]


def get_wishlist_service(db: DbSession) -> WishlistService:
    return WishlistService(db)


def _traduzir_value_error(exc: ValueError):
    """Traduz os ``ValueError`` do service em erros HTTP (senão viram 500)."""
    msg = str(exc)

    if "not owned by user" in msg:
        return ForbiddenException(msg)

    if "already has product" in msg:
        return ConflictException(msg, code="WISHLIST_DUPLICATE")

    return NotFoundException(msg, code="WISHLIST_NOT_FOUND")


@wishlist_router.post(
    "/create",
    response_model=WishlistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adiciona um produto à wishlist do usuário",
)
def create_wishlist_item(
    data: WishlistCreate, user_id: UserId, db: DbSession
) -> WishlistResponse:
    try:
        return get_wishlist_service(db).create(user_id, data)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@wishlist_router.get(
    "/list",
    response_model=list[WishlistResponse],
    summary="Lista os itens da wishlist do usuário",
)
def list_wishlist_items(user_id: UserId, db: DbSession) -> list:
    try:
        return get_wishlist_service(db).get_by_user_id(user_id)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@wishlist_router.get(
    "/get/{wishlist_id}",
    response_model=WishlistResponse,
    summary="Busca um item da wishlist pelo ID",
)
def get_wishlist_item(
    wishlist_id: int, user_id: UserId, db: DbSession
) -> WishlistResponse:
    try:
        return get_wishlist_service(db).get_by_id(wishlist_id, user_id)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@wishlist_router.get(
    "/all",
    response_model=list[WishlistResponse],
    summary="Lista todos os itens de wishlists",
)
def list_all_wishlist_items(db: DbSession) -> list:
    try:
        return get_wishlist_service(db).get_all()
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@wishlist_router.get(
    "/product/{product_id}",
    response_model=list[WishlistResponse],
    summary="Busca itens da wishlist por produto",
)
def get_wishlist_by_product_id(
    product_id: int, db: DbSession
) -> list:
    try:
        return get_wishlist_service(db).get_by_product_id(product_id)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@wishlist_router.patch(
    "/update/{wishlist_id}",
    response_model=WishlistResponse,
    summary="Atualiza um item da wishlist",
)
def update_wishlist_item(
    wishlist_id: int,
    data: WishlistUpdate,
    user_id: UserId,
    db: DbSession,
) -> WishlistResponse:
    try:
        return get_wishlist_service(db).update(wishlist_id, user_id, data)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@wishlist_router.delete(
    "/delete/{wishlist_id}",
    response_model=WishlistResponse,
    summary="Remove um item da wishlist",
)
def delete_wishlist_item(
    wishlist_id: int, user_id: UserId, db: DbSession
) -> WishlistResponse:
    try:
        return get_wishlist_service(db).delete(wishlist_id, user_id)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc
