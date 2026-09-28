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
