from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ProductNotFoundException,
    UserNotFoundException,
)
from app.models.user import User
from app.schemas.cart import CartItemCreate, CartItemResponse, CartResponse
from app.services.cart_service import CartService

cart_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
UserDb = Annotated[User, Depends(get_current_user)]


def get_cart_service(db: DbSession) -> CartService:
    return CartService(db)


def _traduzir_value_error(exc: ValueError):
    """Converte os ``ValueError`` do service em erros HTTP (senão viram 500).

    Mesmo padrão já usado em `products.py`, `addresses.py`, `orders.py` e
    `categories.py`.

    Sem esta tradução, `GET /cart/me` de um usuário que ainda não tem carrinho
    responderia 500 com traceback no log — o front trata o erro e cria o
    carrinho em seguida (handshake da primeira compra), mas o 500 poluía o log
    e era semanticamente errado (não é falha de servidor).
    """
    msg = str(exc)

    if "No user found" in msg:
        return UserNotFoundException()

    if "No cart found" in msg:
        return NotFoundException(msg, code="CART_NOT_FOUND")

    if "No cart item found" in msg:
        return NotFoundException(msg, code="CART_ITEM_NOT_FOUND")

    if "No product found" in msg:
        return ProductNotFoundException()

    if "not owned by user" in msg:
        return ForbiddenException(msg)

    if "already has a cart" in msg:
        return ConflictException(msg, code="CART_ALREADY_EXISTS")

    if "Insufficient stock" in msg:
        return ConflictException(msg, code="INSUFFICIENT_STOCK")

    return BadRequestException(msg)


@cart_router.post(
    "/create",
    response_model=CartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um carrinho para o usuário",
)
def create_cart(user: UserDb, db: DbSession) -> CartResponse:
    try:
        return get_cart_service(db).create(user.id)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@cart_router.get(
    "/cart/me",
    response_model=CartResponse,
    summary="Busca o carrinho do usuário",
)
def get_user_cart(user: UserDb, db: DbSession) -> CartResponse:
    try:
        return get_cart_service(db).get_by_user_id(user.id)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@cart_router.post(
    "/{cart_id}/items/add",
    response_model=CartItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adiciona um item ao carrinho",
)
def add_cart_item(
    cart_id: int, data: CartItemCreate, user: UserDb, db: DbSession
) -> CartItemResponse:
    try:
        return get_cart_service(db).add_item(
            cart_id, user.id, data.product_id, data.quantity
        )
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@cart_router.patch(
    "/{cart_id}/items/update/{item_id}",
    response_model=CartItemResponse,
    summary="Atualiza a quantidade de um item",
)
def update_cart_item(
    cart_id: int,
    item_id: int,
    quantity: int,
    user: UserDb,
    db: DbSession,
) -> CartItemResponse:
    try:
        return get_cart_service(db).update_item(cart_id, user.id, item_id, quantity)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@cart_router.delete(
    "/{cart_id}/items/delete/{item_id}",
    response_model=CartItemResponse,
    summary="Remove um item do carrinho",
)
def remove_cart_item(
    cart_id: int, item_id: int, user: UserDb, db: DbSession
) -> CartItemResponse:
    try:
        return get_cart_service(db).remove_item(cart_id, user.id, item_id)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@cart_router.delete(
    "/{cart_id}/items/clear",
    response_model=CartResponse,
    summary="Esvazia um carrinho",
)
def clear_cart(cart_id: int, user: UserDb, db: DbSession) -> CartResponse:
    try:
        return get_cart_service(db).clear(cart_id, user.id)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc
