from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.exceptions import (
    ConflictException,
    CouponNotAssignedException,
    NotFoundException,
)
from app.models.user import User
from app.schemas.coupon import CouponResponse
from app.schemas.user_coupon import UserCouponCreate, UserCouponResponse
from app.services.user_coupon_service import UserCouponService

user_coupon_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
UserDb = Annotated[User, Depends(get_current_user)]
UserId = Annotated[int, Query(description="ID do usuário dono do cupom")]


def get_user_coupon_service(db: DbSession) -> UserCouponService:
    return UserCouponService(db)


def _traduzir_value_error(exc: ValueError):
    """Traduz os ``ValueError`` do service em erros HTTP (senão viram 500)."""
    msg = str(exc)

    if "not owned by user" in msg:
        # Vínculo existente, mas pertence a outro usuário.
        return CouponNotAssignedException(msg)

    if "already has coupon" in msg:
        return ConflictException(msg, code="USER_COUPON_DUPLICATE")

    return NotFoundException(msg, code="USER_COUPON_NOT_FOUND")


@user_coupon_router.get(
    "/my",
    response_model=list[CouponResponse],
    summary="Lista os cupons atribuídos ao usuário autenticado",
)
def list_my_coupons(
    user: UserDb, db: DbSession
) -> list[CouponResponse]:
    """Usado pelo checkout: devolve os cupons que *possuem* o usuário logado."""
    try:
        return get_user_coupon_service(db).list_coupons_by_user(user.id)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@user_coupon_router.post(
    "/create",
    response_model=UserCouponResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Atribui (resgata) um cupom para um usuário",
)
def create_user_coupon(
    data: UserCouponCreate, db: DbSession
) -> UserCouponResponse:
    try:
        return get_user_coupon_service(db).create(data)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@user_coupon_router.get(
    "/list",
    response_model=list[UserCouponResponse],
    summary="Lista os vínculos de cupons do usuário",
)
def list_user_coupons(user_id: UserId, db: DbSession) -> list:
    try:
        return get_user_coupon_service(db).get_by_user_id(user_id)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@user_coupon_router.get(
    "/all",
    response_model=list[UserCouponResponse],
    summary="Lista todos os vínculos usuário-cupom",
)
def list_all_user_coupons(db: DbSession) -> list:
    return get_user_coupon_service(db).get_all()


@user_coupon_router.get(
    "/get/{user_coupon_id}",
    response_model=UserCouponResponse,
    summary="Busca um vínculo usuário-cupom pelo ID",
)
def get_user_coupon(
    user_coupon_id: int, user_id: UserId, db: DbSession
) -> UserCouponResponse:
    try:
        return get_user_coupon_service(db).get_by_id(user_coupon_id, user_id)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@user_coupon_router.get(
    "/user/{user_id}",
    response_model=list[UserCouponResponse],
    summary="Lista os vínculos de cupons de um usuário",
)
def get_user_coupons_by_user(user_id: int, db: DbSession) -> list:
    try:
        return get_user_coupon_service(db).get_by_user_id(user_id)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@user_coupon_router.get(
    "/coupon/{coupon_id}",
    response_model=list[UserCouponResponse],
    summary="Lista os vínculos de um cupom com usuários",
)
def get_user_coupons_by_coupon(coupon_id: int, db: DbSession) -> list:
    try:
        return get_user_coupon_service(db).get_by_coupon_id(coupon_id)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@user_coupon_router.delete(
    "/delete/{user_coupon_id}",
    response_model=UserCouponResponse,
    summary="Remove o vínculo de um cupom com um usuário",
)
def delete_user_coupon(
    user_coupon_id: int, user_id: UserId, db: DbSession
) -> UserCouponResponse:
    try:
        return get_user_coupon_service(db).delete(user_coupon_id, user_id)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc
