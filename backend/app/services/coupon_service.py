from datetime import datetime

from app.models.coupon import Coupon
from app.repositories.coupon_repo import CouponRepository
from app.repositories.product_repo import ProductRepository


class CouponService:
    def __init__(self, db):
        self.repo = CouponRepository(db)
        self.product_repo = ProductRepository(db)
        self.session = db

    def get_by_id(self, coupon_id: int) -> dict:
        coupon = self.repo.get_by_id(coupon_id)

        if coupon is None:
            raise ValueError(f"No coupon found with id {coupon_id}")

        return coupon

    def get_by_code(self, code: str) -> dict:
        coupon = self.repo.get_by_code(code)

        if coupon is None:
            raise ValueError(f"No coupon found with code {code}")

        return coupon

    def get_by_product_id(self, product_id: int) -> list:
        coupons = self.repo.get_by_product_id(product_id)

        if not coupons:
            raise ValueError(f"No coupons found with product_id {product_id}")

        return coupons

    def get_by_valid_until(self, valid_until: datetime) -> list:
        coupons = self.repo.get_by_valid_until(valid_until)

        if not coupons:
            raise ValueError(f"No coupons found with valid_until {valid_until}")

        return coupons

    def get_by_max_uses(self, max_uses: int) -> list:
        coupons = self.repo.get_by_max_uses(max_uses)

        if not coupons:
            raise ValueError(f"No coupons found with max_uses {max_uses}")

        return coupons

    def get_by_discount_type(self, discount_type: str) -> list:
        coupons = self.repo.get_by_discount_type(discount_type)

        if not coupons:
            raise ValueError(f"No coupons found with discount_type {discount_type}")

        return coupons


    def get_by_discount_value(self, discount_value: float) -> list:
        coupons = self.repo.get_by_discount_value(discount_value)

        if not coupons:
            raise ValueError(f"No coupons found with discount_value {discount_value}")

        return coupons

    def get_by_min_purchase(self, min_purchase: float) -> list:
        coupons = self.repo.get_by_min_purchase(min_purchase)

        if not coupons:
            raise ValueError(f"No coupons found with min_purchase {min_purchase}")

        return coupons

    def get_by_max_discount(self, max_discount: float) -> list:
        coupons = self.repo.get_by_max_discount(max_discount)

        if not coupons:
            raise ValueError(f"No coupons found with max_discount {max_discount}")

        return coupons

    def get_all(self) -> list:
        coupons = self.repo.get_all()

        if not coupons:
            raise ValueError("No coupons found")

        return coupons

    def create(self, data) -> dict:
        with self.session.begin():

            existing_code = self.repo.get_by_code(data.code)
            if existing_code is not None:
                raise ValueError(f"Coupon with code '{data.code}' already exists")

            if data.product_id is not None:
                product = self.product_repo.get_by_id(data.product_id)
                if product is None:
                    raise ValueError(f"No product found with id {data.product_id}")


            

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
                raise ValueError(f"No coupon found with id {coupon_id}")

            if data.code is not None:
                existing_code = self.repo.get_by_code(data.code)
                if existing_code is not None and existing_code.id != coupon_id:
                    raise ValueError(f"Coupon with code '{data.code}' already exists")

            if data.product_id is not None:
                product = self.product_repo.get_by_id(data.product_id)
                if product is None:
                    raise ValueError(f"No product found with id {data.product_id}")

            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(coupon, field, value)

            self.repo.update(coupon)

            return coupon

    def delete(self, coupon_id: int) -> dict:
        with self.session.begin():

            coupon = self.repo.get_by_id(coupon_id)

            if coupon is None:
                raise ValueError(f"No coupon found with id {coupon_id}")

            self.repo.delete(coupon)
            return coupon

