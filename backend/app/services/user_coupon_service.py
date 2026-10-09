from app.api.exceptions import (
    ConflictException,
    CouponNotAssignedException,
    CouponNotFoundException,
    NotFoundException,
    UserNotFoundException,
)
from app.models.coupon import Coupon
from app.models.user import User, UserRole
from app.models.user_coupon import UserCoupon
from app.repositories.coupon_repo import CouponRepository
from app.repositories.user_coupon_repo import UserCouponRepository
from app.repositories.user_repo import UserRepository


def _is_admin(user: User) -> bool:
    return user.role == UserRole.ADMIN


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
            raise NotFoundException(
                "Vínculo de cupom não encontrado.", code="USER_COUPON_NOT_FOUND"
            )

        if user_id is not None and user_coupon.user_id != user_id:
            raise CouponNotAssignedException()

        return user_coupon

    def get_by_user_id(self, user_id: int) -> list:
        user = self.user_repo.get_by_id(user_id)

        if user is None:
            raise UserNotFoundException(user_id=user_id)

        return self.repo.get_by_user_id(user_id)

    def get_by_coupon_id(self, coupon_id: int) -> list:
        coupon = self.coupon_repo.get_by_id(coupon_id)

        if coupon is None:
            raise CouponNotFoundException()

        return self.repo.get_by_coupon_id(coupon_id)

    def get_all(self) -> list:
        return self.repo.get_all()

    def list_coupons_by_user(self, user_id: int) -> list[Coupon]:
        """Devolve os cupons (entidades) atribuídos a um usuário."""
        user = self.user_repo.get_by_id(user_id)

        if user is None:
            raise UserNotFoundException(user_id=user_id)

        return [link.coupons for link in self.repo.get_by_user_id(user_id)]

    def get_for_user(self, user_coupon_id: int, current_user: User) -> dict:
        """Busca um vínculo garantindo que o dono (ou um admin) o acesse.

        Fecha o IDOR que permitia ler o vínculo de qualquer usuário passando
        qualquer `user_id` na query (o valor vinha do cliente).
        """
        user_coupon = self.repo.get_by_id(user_coupon_id)

        if user_coupon is None:
            raise NotFoundException(
                "Vínculo de cupom não encontrado.", code="USER_COUPON_NOT_FOUND"
            )

        if not _is_admin(current_user) and user_coupon.user_id != current_user.id:
            raise CouponNotAssignedException()

        return user_coupon

    def delete_for_user(self, user_coupon_id: int, current_user: User) -> dict:
        """Remove um vínculo apenas se pertencer ao autenticado (ou se for admin)."""
        with self.session.begin():

            user_coupon = self.repo.get_by_id(user_coupon_id)

            if user_coupon is None:
                raise NotFoundException(
                    "Vínculo de cupom não encontrado.", code="USER_COUPON_NOT_FOUND"
                )

            if not _is_admin(current_user) and user_coupon.user_id != current_user.id:
                raise CouponNotAssignedException()

            self.repo.delete(user_coupon)
            return user_coupon

    def create_for_user(self, user_id: int, coupon_id: int) -> dict:
        """Atribui um cupom ao usuário autenticado (alvo vem do token).

        Diferente de ``admin_assign``, que aceita um ``user_id`` arbitrário
        (uso administrativo), aqui o alvo é sempre o próprio usuário.
        """
        return self._create_link(user_id, coupon_id)

    def admin_assign(self, user_id: int, coupon_id: int) -> dict:
        """Atribui um cupom a QUALQUER usuário (uso administrativo).

        Chamado pela rota ``POST /user-coupons/admin/assign``, que exige
        administrador. Mantém a atribuição em lote do painel admin sem expor
        um endpoint que aceite ``user_id`` arbitrário de cliente.
        """
        return self._create_link(user_id, coupon_id)

    def create(self, data) -> dict:
        """Atribui um cupom a um usuário a partir do payload (uso interno).

        Mantido para compatibilidade; as rotas de cliente usam
        ``create_for_user`` e a rota admin usa ``admin_assign``.
        """
        return self._create_link(data.user_id, data.coupon_id)

    def _create_link(self, user_id: int, coupon_id: int) -> dict:
        with self.session.begin():

            user = self.user_repo.get_by_id(user_id)

            if user is None:
                raise UserNotFoundException(user_id=user_id)

            coupon = self.coupon_repo.get_by_id(coupon_id)

            if coupon is None:
                raise CouponNotFoundException()

            existing = self.repo.get_by_user_and_coupon(user_id, coupon_id)

            if existing is not None:
                raise ConflictException(
                    "Este cupom já está atribuído a este usuário.",
                    code="USER_COUPON_DUPLICATE",
                )

            user_coupon = self.repo.create(
                UserCoupon(
                    user_id=user_id,
                    coupon_id=coupon_id,
                )
            )

            return user_coupon

    def delete(self, user_coupon_id: int, user_id: int | None = None) -> dict:
        with self.session.begin():

            user_coupon = self.repo.get_by_id(user_coupon_id)

            if user_coupon is None:
                raise NotFoundException(
                    "Vínculo de cupom não encontrado.", code="USER_COUPON_NOT_FOUND"
                )

            if user_id is not None and user_coupon.user_id != user_id:
                raise CouponNotAssignedException()

            self.repo.delete(user_coupon)
            return user_coupon
