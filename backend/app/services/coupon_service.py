from app.api.exceptions import (
    ConflictException,
    CouponNotFoundException,
    ProductNotFoundException,
)
from app.models.coupon import Coupon
from app.repositories.coupon_repo import CouponRepository
from app.repositories.product_repo import ProductRepository


class CouponService:
    def __init__(self, db):
        self.repo = CouponRepository(db)
        self.product_repo = ProductRepository(db)
        self.session = db

    def get_all(self) -> list:
        return self.repo.get_all()

    def create(self, data) -> dict:
        with self.session.begin():

            existing_code = self.repo.get_by_code(data.code)
            if existing_code is not None:
                raise ConflictException(
                    f"Já existe um cupom com o código '{data.code}'.",
                    code="DUPLICATE_COUPON",
                )

            if data.product_id is not None:
                product = self.product_repo.get_by_id(data.product_id)
                if product is None:
                    raise ProductNotFoundException()

            coupon = self.repo.create(
                Coupon(
                    code=data.code,
                    product_id=data.product_id,
                    discount_type=data.discount_type,
                    discount_value=data.discount_value,
                    min_purchase=data.min_purchase,
                    max_discount=data.max_discount,
                    valid_until=data.valid_until,
                    max_uses=data.max_uses,
                    is_active=data.is_active,
                )
            )

            return coupon


    def update(self, coupon_id: int, data) -> dict:
        with self.session.begin():

            coupon = self.repo.get_by_id(coupon_id)

            if coupon is None:
                raise CouponNotFoundException()

            if data.code is not None:
                existing_code = self.repo.get_by_code(data.code)
                if existing_code is not None and existing_code.id != coupon_id:
                    raise ConflictException(
                        f"Já existe um cupom com o código '{data.code}'.",
                        code="DUPLICATE_COUPON",
                    )

            if data.product_id is not None:
                product = self.product_repo.get_by_id(data.product_id)
                if product is None:
                    raise ProductNotFoundException()

            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(coupon, field, value)

            self.repo.update(coupon)

            return coupon

    def delete(self, coupon_id: int) -> dict:
        with self.session.begin():

            coupon = self.repo.get_by_id(coupon_id)

            if coupon is None:
                raise CouponNotFoundException()

            self.repo.delete(coupon)
            return coupon
