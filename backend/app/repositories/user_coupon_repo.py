from sqlalchemy.orm import Session

from app.models.user_coupon import UserCoupon
from app.repositories.base import BaseRepository


class UserCouponRepository(BaseRepository[UserCoupon]):
    def __init__(self, db: Session) -> None:
        super().__init__(UserCoupon, db)

    def get_by_user_id(self, user_id: int) -> list[UserCoupon]:
        return (
            self.session.query(UserCoupon)
            .filter(UserCoupon.user_id == user_id)
            .all()
        )

    def get_by_coupon_id(self, coupon_id: int) -> list[UserCoupon]:
        return (
            self.session.query(UserCoupon)
            .filter(UserCoupon.coupon_id == coupon_id)
            .all()
        )

    def get_by_user_and_coupon(
        self, user_id: int, coupon_id: int
    ) -> UserCoupon | None:
        return (
            self.session.query(UserCoupon)
            .filter(
                UserCoupon.user_id == user_id,
                UserCoupon.coupon_id == coupon_id,
            )
            .first()
        )

    def get_by_user_and_coupon_for_update(
        self, user_id: int, coupon_id: int
    ) -> UserCoupon | None:
        """Como ``get_by_user_and_coupon``, mas travando a linha.

        Necessário no checkout de cupom de uso único por cliente: sem o lock,
        dois pedidos simultâneos do mesmo usuário leem ``used_at = NULL`` e
        ambos aplicam o desconto.
        """
        return (
            self.session.query(UserCoupon)
            .filter(
                UserCoupon.user_id == user_id,
                UserCoupon.coupon_id == coupon_id,
            )
            .with_for_update()
            .first()
        )
