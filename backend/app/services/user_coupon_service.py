from app.models.coupon import Coupon
from app.models.user_coupon import UserCoupon
from app.repositories.coupon_repo import CouponRepository
from app.repositories.user_coupon_repo import UserCouponRepository
from app.repositories.user_repo import UserRepository


class UserCouponService:
    """Gerencia o vínculo N:N entre usuários e cupons (ownership).

    Regras:
    - Só atribui cupons existentes e usuários existentes.
    - Não permite o mesmo cupom duas vezes para o mesmo usuário.
    - A remoção é escopada por usuário, como em wishlist.
    """

    def __init__(self, db):
        self.repo = UserCouponRepository(db)
        self.user_repo = UserRepository(db)
        self.coupon_repo = CouponRepository(db)
        self.session = db

    def get_by_id(self, user_coupon_id: int, user_id: int | None = None) -> dict:
        user_coupon = self.repo.get_by_id(user_coupon_id)

        if user_coupon is None:
            raise ValueError(f"No user coupon found with id {user_coupon_id}")

        if user_id is not None and user_coupon.user_id != user_id:
            raise ValueError("User coupon is not owned by user")

        return user_coupon

    def get_by_user_id(self, user_id: int) -> list:
        user = self.user_repo.get_by_id(user_id)

        if user is None:
            raise ValueError(f"No user found with id {user_id}")

        return self.repo.get_by_user_id(user_id)

    def get_by_coupon_id(self, coupon_id: int) -> list:
        coupon = self.coupon_repo.get_by_id(coupon_id)

        if coupon is None:
            raise ValueError(f"No coupon found with id {coupon_id}")

        return self.repo.get_by_coupon_id(coupon_id)

    def get_all(self) -> list:
        return self.repo.get_all()

    def list_coupons_by_user(self, user_id: int) -> list[Coupon]:
        """Devolve os cupons (entidades) atribuídos a um usuário."""
        user = self.user_repo.get_by_id(user_id)

        if user is None:
            raise ValueError(f"No user found with id {user_id}")

        return [link.coupons for link in self.repo.get_by_user_id(user_id)]

    def create(self, data) -> dict:
        with self.session.begin():

            user = self.user_repo.get_by_id(data.user_id)

            if user is None:
                raise ValueError(f"No user found with id {data.user_id}")

            coupon = self.coupon_repo.get_by_id(data.coupon_id)

            if coupon is None:
                raise ValueError(f"No coupon found with id {data.coupon_id}")

            existing = self.repo.get_by_user_and_coupon(
                data.user_id, data.coupon_id
            )

            if existing is not None:
                raise ValueError(
                    f"User {data.user_id} already has coupon "
                    f"{data.coupon_id}"
                )

            user_coupon = self.repo.create(
                UserCoupon(
                    user_id=data.user_id,
                    coupon_id=data.coupon_id,
                )
            )

            return user_coupon

    def delete(self, user_coupon_id: int, user_id: int | None = None) -> dict:
        with self.session.begin():

            user_coupon = self.repo.get_by_id(user_coupon_id)

            if user_coupon is None:
                raise ValueError(f"No user coupon found with id {user_coupon_id}")

            if user_id is not None and user_coupon.user_id != user_id:
                raise ValueError("User coupon is not owned by user")

            self.repo.delete(user_coupon)
            return user_coupon
