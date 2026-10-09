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

    def get_by_id_for_update(self, coupon_id: int) -> Coupon | None:
        """Busca o cupom travando a linha at\u00e9 o fim da transa\u00e7\u00e3o.

        Usado no checkout: sem o ``FOR UPDATE`` dois pedidos concorrentes leem
        o mesmo ``used_count`` e ambos passam na valida\u00e7\u00e3o de
        ``max_uses`` (o incremento de um \u00e9 sobrescrito pelo outro).
        """
        return (
            self.session.query(Coupon)
            .filter(Coupon.id == coupon_id)
            .with_for_update()
            .first()
        )
