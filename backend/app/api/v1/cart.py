from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.schemas.cart import CartItemCreate, CartItemResponse, CartResponse
from app.services.cart_service import CartService
from app.models.user import User 


cart_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
UserDb = Annotated[User, Depends(get_current_user)]




def get_cart_service(db: DbSession) -> CartService:
    return CartService(db)


@cart_router.post(
    "/create",
    response_model=CartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um carrinho para o usuário",
)
def create_cart(user: UserDb, db: DbSession) -> CartResponse:
    return get_cart_service(db).create(user.id)


@cart_router.get(
    "/cart/me",
    response_model=CartResponse,
    summary="Busca o carrinho do usuário",
)
def get_user_cart(user: UserDb, db: DbSession) -> CartResponse:
    return get_cart_service(db).get_by_user_id(user.id)



@cart_router.get(
    "/get/{cart_id}",
    response_model=CartResponse,
    summary="Busca um carrinho pelo ID",
)
def get_cart(cart_id: int, user: UserDb, db: DbSession) -> CartResponse:
    return get_cart_service(db).get_by_id(cart_id, user.id)



@cart_router.get(
    "/items/{cart_id}",
    response_model=list[CartItemResponse],
    summary="Lista os itens de um carrinho",
)
def get_cart_items(cart_id: int, user: UserDb, db: DbSession) -> list:
    return get_cart_service(db).get_with_items(cart_id, user.id)



@cart_router.post(
    "/{cart_id}/items/add",
    response_model=CartItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adiciona um item ao carrinho",
)
def add_cart_item(
    cart_id: int, data: CartItemCreate, user: UserDb, db: DbSession
) -> CartItemResponse:
    return get_cart_service(db).add_item(
        cart_id, user.id, data.product_id, data.quantity
    )


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
    return get_cart_service(db).update_item(cart_id, user.id, item_id, quantity)


@cart_router.patch(
    "/{cart_id}/items/decrease/{item_id}",
    response_model=CartItemResponse,
    summary="Diminui a quantidade de um item",
)
def decrease_cart_item(
    cart_id: int,
    item_id: int,
    user : UserDb,
    db: DbSession,
    quantity: int ,
) -> CartItemResponse:
    return get_cart_service(db).decrease_item(cart_id, user.id, item_id, quantity)


@cart_router.delete(
    "/{cart_id}/items/delete/{item_id}",
    response_model=CartItemResponse,
    summary="Remove um item do carrinho",
)
def remove_cart_item(
    cart_id: int, item_id: int, user: UserDb, db: DbSession
) -> CartItemResponse:
    return get_cart_service(db).remove_item(cart_id, user.id, item_id)


@cart_router.delete(
    "/{cart_id}/items/clear",
    response_model=CartResponse,
    summary="Esvazia um carrinho",
)
def clear_cart(cart_id: int, user: UserDb, db: DbSession) -> CartResponse:
    return get_cart_service(db).clear(cart_id, user.id)



@cart_router.delete(
    "/delete/{cart_id}",
    response_model=CartResponse,
    summary="Exclui um carrinho",
)
def delete_cart(cart_id: int, user: UserDb, db: DbSession) -> CartResponse:
    return get_cart_service(db).delete(cart_id, user.id)