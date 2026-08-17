from datetime import datetime

from sqlalchemy.orm import Session

from app.models.coupon import Coupon
from app.repositories.base import BaseRepository


class CouponRepository(BaseRepository[Coupon]):
    def __init__(self, db: Session) -> None:
        super().__init__(Coupon, db)

    def get_by_code(self, code: str) -> Coupon | None:
        return self.session.query(Coupon).filter(
            Coupon.code == code
        ).first()

    def get_by_product_id(self, product_id: int) -> list[Coupon]:
        return self.session.query(Coupon).filter(
            Coupon.product_id == product_id,
            Coupon.is_active.is_(True)
            ).all()

    def get_by_valid_until(self, valid_until: datetime) -> list[Coupon]:
        return self.session.query(Coupon).filter(
            Coupon.valid_until == valid_until,
            Coupon.is_active.is_(True)
            ).all()

    def get_by_max_uses(self, max_uses: int) -> list[Coupon]:
        return self.session.query(Coupon).filter(
            Coupon.max_uses == max_uses,
            Coupon.is_active.is_(True)
            ).all()

    def get_by_discount_type(self, discount_type: str) -> list[Coupon]:
        return self.session.query(Coupon).filter(
            Coupon.discount_type == discount_type,
            Coupon.is_active.is_(True)
            ).all()

    def get_by_discount_value(self, discount_value: float) -> list[Coupon]:
        return self.session.query(Coupon).filter(
            Coupon.discount_value == discount_value,
            Coupon.is_active.is_(True)
            ).all()

    def get_by_min_purchase(self, min_purchase: float) -> list[Coupon]:
        return self.session.query(Coupon).filter(
            Coupon.min_purchase == min_purchase,
            Coupon.is_active.is_(True)
            ).all()

    def get_by_max_discount(self, max_discount: float) -> list[Coupon]:
        return self.session.query(Coupon).filter(
            Coupon.max_discount == max_discount,
            Coupon.is_active.is_(True)
            ).all()

    def get_by_created_at(self, created_at: datetime) -> list[Coupon]:
        return self.session.query(Coupon).filter(
            Coupon.created_at == created_at,
            Coupon.is_active.is_(True)
            ).all()

    def get_by_updated_at(self, updated_at: datetime) -> list[Coupon]:
        return self.session.query(Coupon).filter(
            Coupon.updated_at == updated_at,
            Coupon.is_active.is_(True)
            ).all()
