from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, db: Session) -> None:
        super().__init__(Payment, db)


    def get_all(self) -> list[Payment]:
        return self.session.query(Payment).all()

    def get_by_id(self, id: int) -> Payment | None:
        return self.session.query(Payment).filter(Payment.id == id).first()

    def get_by_order_id(self, order_id: int) -> list[Payment]:
        return self.session.query(Payment).filter(Payment.order_id == order_id).all()

    def get_by_provider_payment_id_for_update(self, provider_payment_id: str) -> Payment | None:

        return (
            self.session.query(Payment)
            .filter(Payment.provider_payment_id == provider_payment_id)
            .with_for_update()
            .first()
        )





