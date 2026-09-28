from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.coupon import CouponCreate, CouponResponse, CouponUpdate
from app.services.coupon_service import CouponService

coupon_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]


def get_coupon_service(db: DbSession) -> CouponService:
    return CouponService(db)


@coupon_router.post(
    "/create",
    response_model=CouponResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo cupom",
)
def create_coupon(data: CouponCreate, db: DbSession) -> CouponResponse:
    return get_coupon_service(db).create(data)


@coupon_router.get(
    "/list",
    response_model=list[CouponResponse],
    summary="Lista todos os cupons",
)
def list_coupons(db: DbSession) -> list:
    return get_coupon_service(db).get_all()


@coupon_router.patch(
    "/update/{coupon_id}",
    response_model=CouponResponse,
    summary="Atualiza um cupom",
)
def update_coupon(
    coupon_id: int, data: CouponUpdate, db: DbSession
) -> CouponResponse:
    return get_coupon_service(db).update(coupon_id, data)


@coupon_router.delete(
    "/delete/{coupon_id}",
    response_model=CouponResponse,
    summary="Exclui um cupom",
)
def delete_coupon(coupon_id: int, db: DbSession) -> CouponResponse:
    return get_coupon_service(db).delete(coupon_id)

