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

    def get_by_user_id(self, user_id: int) -> list[Payment]:
        """Lista todos os pagamentos pertencentes a um usuário.

        Filtra via join com ``orders`` (``payments.order_id -> orders.id``)
        usando ``user_id`` de ``orders``. Permite uma única query agregada para
        a aba "Pagamentos" da conta, em vez de 1 request por pedido.
        """
        from app.models.order import Order

        return (
            self.session.query(Payment)
            .join(Order, Payment.order_id == Order.id)
            .filter(Order.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .all()
        )

    def paginate_by_user_id(
        self, user_id: int, page: int, per_page: int
    ) -> tuple[list[Payment], int]:
        """Histórico de pagamentos do usuário paginado no banco.

        Mesmo join de ``get_by_user_id``, mas com ``count`` + ``offset``/``limit``
        para o histórico não crescer indefinidamente com o tempo de conta.
        """
        from app.models.order import Order

        query = (
            self.session.query(Payment)
            .join(Order, Payment.order_id == Order.id)
            .filter(Order.user_id == user_id)
        )
        total = query.count()
        items = (
            query.order_by(Payment.created_at.desc(), Payment.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    def get_by_provider_payment_id_for_update(self, provider_payment_id: str) -> Payment | None:

        return (
            self.session.query(Payment)
            .filter(Payment.provider_payment_id == provider_payment_id)
            .with_for_update()
            .first()
        )





