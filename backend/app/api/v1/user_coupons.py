from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_user, get_db
from app.models.user import User
from app.schemas.coupon import CouponResponse
from app.schemas.user_coupon import UserCouponCreate, UserCouponResponse
from app.services.user_coupon_service import UserCouponService

# Rotas de vínculo usuário-cupom.
#
# SEGURANÇA: o `user_id` NUNCA vem do cliente nas rotas de cliente — vem do
# token. Antes, `POST /create` era anônimo e aceitava `user_id` do corpo,
# permitindo a qualquer pessoa atribuir qualquer cupom à própria conta (ou à
# de terceiros); as rotas de listagem/exclusão também eram anônimas. Agora:
#   - `/my`          -> cliente, enxerga apenas os próprios cupons;
#   - `/create`      -> cliente, vincula o cupom ao PRÓPRIO usuário;
#   - `/delete/{id}` -> cliente dono do vínculo (ou admin);
#   - demais rotas   -> somente administrador (visão global).
user_coupon_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
UserDb = Annotated[User, Depends(get_current_user)]
AdminDb = Annotated[User, Depends(get_current_admin)]


def get_user_coupon_service(db: DbSession) -> UserCouponService:
    return UserCouponService(db)


@user_coupon_router.get(
    "/my",
    response_model=list[CouponResponse],
    summary="Lista os cupons atribuídos ao usuário autenticado",
)
def list_my_coupons(
    user: UserDb, db: DbSession
) -> list[CouponResponse]:
    """Usado pelo checkout: devolve os cupons que *possuem* o usuário logado."""
    return get_user_coupon_service(db).list_coupons_by_user(user.id)


@user_coupon_router.post(
    "/create",
    response_model=UserCouponResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Atribui (resgata) um cupom para o próprio usuário autenticado",
)
def create_user_coupon(
    data: UserCouponCreate, user: UserDb, db: DbSession
) -> UserCouponResponse:
    """Vincula um cupom ao usuário do token.

    O `user_id` do corpo é ignorado de propósito: o alvo é sempre o usuário
    autenticado. Atribuir cupons a terceiros é operação administrativa e passa
    por `UserCouponService.create_for_user`.
    """
    return get_user_coupon_service(db).create_for_user(user.id, data.coupon_id)


@user_coupon_router.post(
    "/admin/assign",
    response_model=UserCouponResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Atribui um cupom a qualquer usuário (admin)",
)
def admin_assign_user_coupon(
    data: UserCouponCreate, admin: AdminDb, db: DbSession
) -> UserCouponResponse:
    """Atribuição em lote do painel admin: alvo explícito no corpo.

    Rota administrativa separada de ``POST /create`` (que sempre vincula ao
    usuário do token), para que o painel possa conceder cupons a terceiros sem
    reabrir o IDOR de atribuição arbitrária por clientes.
    """
    return get_user_coupon_service(db).admin_assign(
        data.user_id, data.coupon_id
    )


@user_coupon_router.get(
    "/list",
    response_model=list[UserCouponResponse],
    summary="Lista os vínculos de cupons do usuário (admin)",
)
def list_user_coupons(
    user_id: Annotated[int, Query(ge=1, description="ID do usuário")],
    admin: AdminDb,
    db: DbSession,
) -> list:
    return get_user_coupon_service(db).get_by_user_id(user_id)


@user_coupon_router.get(
    "/all",
    response_model=list[UserCouponResponse],
    summary="Lista todos os vínculos usuário-cupom (admin)",
)
def list_all_user_coupons(admin: AdminDb, db: DbSession) -> list:
    return get_user_coupon_service(db).get_all()


@user_coupon_router.get(
    "/get/{user_coupon_id}",
    response_model=UserCouponResponse,
    summary="Busca um vínculo usuário-cupom pelo ID (dono ou admin)",
)
def get_user_coupon(
    user_coupon_id: int, user: UserDb, db: DbSession
) -> UserCouponResponse:
    return get_user_coupon_service(db).get_for_user(user_coupon_id, user)


@user_coupon_router.get(
    "/user/{user_id}",
    response_model=list[UserCouponResponse],
    summary="Lista os vínculos de cupons de um usuário (admin)",
)
def get_user_coupons_by_user(
    user_id: int, admin: AdminDb, db: DbSession
) -> list:
    return get_user_coupon_service(db).get_by_user_id(user_id)


@user_coupon_router.get(
    "/coupon/{coupon_id}",
    response_model=list[UserCouponResponse],
    summary="Lista os vínculos de um cupom com usuários (admin)",
)
def get_user_coupons_by_coupon(
    coupon_id: int, admin: AdminDb, db: DbSession
) -> list:
    return get_user_coupon_service(db).get_by_coupon_id(coupon_id)


@user_coupon_router.delete(
    "/delete/{user_coupon_id}",
    response_model=UserCouponResponse,
    summary="Remove um vínculo de cupom (dono ou admin)",
)
def delete_user_coupon(
    user_coupon_id: int, user: UserDb, db: DbSession
) -> UserCouponResponse:
    return get_user_coupon_service(db).delete_for_user(user_coupon_id, user)
