from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.wishlist import WishlistCreate, WishlistResponse
from app.services.wishlist_service import WishlistService

wishlist_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
AuthUser = Annotated[User, Depends(get_current_user)]


def get_wishlist_service(db: DbSession) -> WishlistService:
    return WishlistService(db)


@wishlist_router.post(
    "/create",
    response_model=WishlistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adiciona um produto à wishlist do usuário autenticado",
)
def create_wishlist_item(
    data: WishlistCreate, current_user: AuthUser, db: DbSession
) -> WishlistResponse:
    return get_wishlist_service(db).create(data, current_user)


@wishlist_router.get(
    "/list",
    response_model=list[WishlistResponse],
    summary="Lista a wishlist do usuário autenticado",
)
def list_wishlist_items(current_user: AuthUser, db: DbSession) -> list:
    return get_wishlist_service(db).get_by_user_id(current_user)


@wishlist_router.get(
    "/all",
    response_model=list[WishlistResponse],
    summary="Lista todos os itens de wishlists (restrito a administradores)",
)
def list_all_wishlist_items(current_user: AuthUser, db: DbSession) -> list:
    return get_wishlist_service(db).get_all(current_user)


@wishlist_router.get(
    "/product/{product_id}",
    response_model=list[WishlistResponse],
    summary="Busca itens da wishlist por produto (comum vê só o próprio)",
)
def get_wishlist_by_product_id(
    product_id: int, current_user: AuthUser, db: DbSession
) -> list:
    return get_wishlist_service(db).get_by_product_id(product_id, current_user)


@wishlist_router.delete(
    "/delete/{wishlist_id}",
    response_model=WishlistResponse,
    summary="Remove um item da wishlist (dono ou admin)",
)
def delete_wishlist_item(
    wishlist_id: int, current_user: AuthUser, db: DbSession
) -> WishlistResponse:
    return get_wishlist_service(db).delete(wishlist_id, current_user)
