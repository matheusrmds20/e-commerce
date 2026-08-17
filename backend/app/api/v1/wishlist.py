from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.wishlist import WishlistCreate, WishlistResponse, WishlistUpdate
from app.services.wishlist_service import WishlistService

wishlist_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
UserId = Annotated[int, Query(description="ID do usuário dono da wishlist")]


def get_wishlist_service(db: DbSession) -> WishlistService:
    return WishlistService(db)


@wishlist_router.post(
    "/create",
    response_model=WishlistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adiciona um produto à wishlist do usuário",
)
def create_wishlist_item(
    data: WishlistCreate, user_id: UserId, db: DbSession
) -> WishlistResponse:
    return get_wishlist_service(db).create(user_id, data)


@wishlist_router.get(
    "/list",
    response_model=list[WishlistResponse],
    summary="Lista os itens da wishlist do usuário",
)
def list_wishlist_items(user_id: UserId, db: DbSession) -> list:
    return get_wishlist_service(db).get_by_user_id(user_id)


@wishlist_router.get(
    "/get/{wishlist_id}",
    response_model=WishlistResponse,
    summary="Busca um item da wishlist pelo ID",
)
def get_wishlist_item(
    wishlist_id: int, user_id: UserId, db: DbSession
) -> WishlistResponse:
    return get_wishlist_service(db).get_by_id(wishlist_id, user_id)


@wishlist_router.get(
    "/all",
    response_model=list[WishlistResponse],
    summary="Lista todos os itens de wishlists",
)
def list_all_wishlist_items(db: DbSession) -> list:
    return get_wishlist_service(db).get_all()


@wishlist_router.get(
    "/product/{product_id}",
    response_model=list[WishlistResponse],
    summary="Busca itens da wishlist por produto",
)
def get_wishlist_by_product_id(
    product_id: int, db: DbSession
) -> list:
    return get_wishlist_service(db).get_by_product_id(product_id)


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
    return get_wishlist_service(db).update(wishlist_id, user_id, data)


@wishlist_router.delete(
    "/delete/{wishlist_id}",
    response_model=WishlistResponse,
    summary="Remove um item da wishlist",
)
def delete_wishlist_item(
    wishlist_id: int, user_id: UserId, db: DbSession
) -> WishlistResponse:
    return get_wishlist_service(db).delete(wishlist_id, user_id)
