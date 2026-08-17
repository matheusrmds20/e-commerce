from datetime import datetime
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


@coupon_router.get(
    "/get/{coupon_id}",
    response_model=CouponResponse,
    summary="Busca um cupom pelo ID",
)
def get_coupon(coupon_id: int, db: DbSession) -> CouponResponse:
    return get_coupon_service(db).get_by_id(coupon_id)


@coupon_router.get(
    "/code/{code}",
    response_model=CouponResponse,
    summary="Busca um cupom pelo código",
)
def get_coupon_by_code(code: str, db: DbSession) -> CouponResponse:
    return get_coupon_service(db).get_by_code(code)


@coupon_router.get(
    "/product/{product_id}",
    response_model=list[CouponResponse],
    summary="Lista cupons de um produto",
)
def get_coupons_by_product(product_id: int, db: DbSession) -> list:
    return get_coupon_service(db).get_by_product_id(product_id)


@coupon_router.get(
    "/valid-until/{valid_until}",
    response_model=list[CouponResponse],
    summary="Lista cupons por data de validade",
)
def get_coupons_by_valid_until(valid_until: datetime, db: DbSession) -> list:
    return get_coupon_service(db).get_by_valid_until(valid_until)


@coupon_router.get(
    "/max-uses/{max_uses}",
    response_model=list[CouponResponse],
    summary="Lista cupons por quantidade máxima de usos",
)
def get_coupons_by_max_uses(max_uses: int, db: DbSession) -> list:
    return get_coupon_service(db).get_by_max_uses(max_uses)


@coupon_router.get(
    "/discount-type/{discount_type}",
    response_model=list[CouponResponse],
    summary="Lista cupons por tipo de desconto",
)
def get_coupons_by_discount_type(discount_type: str, db: DbSession) -> list:
    return get_coupon_service(db).get_by_discount_type(discount_type)


@coupon_router.get(
    "/discount-value/{discount_value}",
    response_model=list[CouponResponse],
    summary="Lista cupons por valor de desconto",
)
def get_coupons_by_discount_value(discount_value: float, db: DbSession) -> list:
    return get_coupon_service(db).get_by_discount_value(discount_value)


@coupon_router.get(
    "/min-purchase/{min_purchase}",
    response_model=list[CouponResponse],
    summary="Lista cupons por valor mínimo de compra",
)
def get_coupons_by_min_purchase(min_purchase: float, db: DbSession) -> list:
    return get_coupon_service(db).get_by_min_purchase(min_purchase)


@coupon_router.get(
    "/max-discount/{max_discount}",
    response_model=list[CouponResponse],
    summary="Lista cupons por valor máximo de desconto",
)
def get_coupons_by_max_discount(max_discount: float, db: DbSession) -> list:
    return get_coupon_service(db).get_by_max_discount(max_discount)


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

