import logging
from datetime import datetime

from app.core.config import get_settings
from app.integrations.MercadoPago.geteway import MercadoPagoGateway
from app.models.order import OrderStatus
from app.models.payment import Payment
from app.repositories.order_repo import OrderRepository
from app.repositories.payment_repo import PaymentRepository
from app.repositories.user_repo import UserRepository

settings = get_settings()

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self, db):
        self.repo = PaymentRepository(db)
        self.user_repo = UserRepository(db)
        self.order_repo = OrderRepository(db)
        self.gateway = MercadoPagoGateway()
        self.session = db

    def create(self, data) -> Payment:
        order = self.order_repo.get_by_id(data.order_id)

        if not order:
            raise ValueError(f"Order not found with id {data.order_id}")

        payment = Payment(
            order_id=data.order_id,
            provider=data.provider,
            provider_payment_id=data.provider_payment_id,
            amount=data.amount,
            currency=data.currency,
            status=data.status,
        )

        self.session.add(payment)
        self.session.commit()
        self.session.refresh(payment)

        return payment


    def get_by_id(self, id: int) -> Payment:
        payment = self.repo.get_by_id(id)

        if payment is None:
            raise ValueError(f"No payment found with id {id}")

        return payment

    def get_by_order_id(self, order_id: int) -> list[Payment]:
        payments = self.repo.get_by_order_id(order_id)

        if not payments:
            raise ValueError(f"No payments found with order_id {order_id}")

        return payments

    def create_checkout(self, order_id: int, user_id: int) -> dict:


        order = self.order_repo.get_by_id(order_id)

        if not order:
            raise ValueError(f"Order not found with id {order_id}")

        if order.user_id != user_id:
            raise ValueError(f"Order {order_id} does not belong to user {user_id}")


        order_items = self.order_repo.get_with_items_products(order_id)

        if not order_items:
            raise ValueError(f"Order not found with id {order_id}")


        payment_already_exists = self.repo.get_by_order_id(order_id)

        if payment_already_exists:
            raise ValueError(f"Payment already exists for order {order_id}")

        items = [
            {
                "id": str(item.product_id),
                "title": item.products.title,
                "quantity": item.quantity,
                "unit_price": item.price,
                "currency_id": "BRL",
            }
            for item in order_items
        ]


        preference_data = {
            "items": items,

            "external_reference": str(order.id),

            "back_urls": {
                "success": f"{settings.FRONTEND_URL}/payment/success",
                "failure": f"{settings.FRONTEND_URL}/payment/failure",
                "pending": f"{settings.FRONTEND_URL}/payment/pending",
            },

            "notification_url": (
                f"{settings.BACKEND_URL.rstrip('/')}/api/v1/payments/webhook/"
            ),
        }




        preference = self.gateway.create_preference(preference_data)

        payment = Payment(
            order_id=order_id,
            provider="mercadopago",
            provider_payment_id=None,
            provider_preference_id=preference["id"],
            amount=order.total,
            currency="BRL",
            status="pending",
        )


        self.session.add(payment)
        self.session.commit()



        # Sandbox: usa o sandbox_init_point (checkout de teste). Faz fallback
        # para o init_point caso o MP não retorne o campo em sandbox.
        checkout_url = preference.get("sandbox_init_point") or preference.get(
            "init_point"
        )



        return {
            "id": payment.id,
            "payment_id": payment.id,
            "checkout_url": checkout_url,
        }

    def process_webhook(self, payment_provider_id: str, topic: str | None = None) -> Payment:

        logger.info(
            "process_webhook start: provider_id=%s topic=%s",
            payment_provider_id,
            topic,
        )

        # Quando a notificação é de merchant_order, o id recebido é da
        # merchant_order (que agrega vários payments). O payment de verdade
        # fica em payments[i]["id"] da resposta.
        if topic == "merchant_order":
            merchant_order = self.gateway.get_merchant_order(payment_provider_id)
            payments = merchant_order.get("payments") or []
            logger.info(
                "merchant_order %s -> %d payment(s): %s",
                payment_provider_id,
                len(payments),
                [(p.get("id"), p.get("status")) for p in payments],
            )
            if not payments:
                raise ValueError(
                    f"Merchant order {payment_provider_id} has no payments"
                )
            # Prefere um payment aprovado; senão, o de maior id. A merchant_order
            # pode listar payments de tentativas antigas/rejeitadas, e pegar o
            # max(id) cegamente pode escolher um que não seja o relevante.
            approved = [p for p in payments if p.get("status") == "approved"]
            chosen = (approved or payments)
            payment_provider_id = str(max(p["id"] for p in chosen))
            logger.info(
                "merchant_order %s -> usando payment %s",
                merchant_order.get("id"),
                payment_provider_id,
            )

        try:
            provider_payment = self.gateway.get_payment(payment_provider_id)
        except RuntimeError as err:
            # Alguns formatos de notificação (ex.: type=mp-connect, ou
            # topic_merchant_order sem mapeamento de topic) trazem o id de uma
            # merchant_order em vez de um payment. Se o get_payment der 404,
            # tenta resolver como merchant_order antes de desistir.
            if "404" not in str(err):
                raise
            logger.warning(
                "get_payment(%s) deu 404; tentando como merchant_order",
                payment_provider_id,
            )
            merchant_order = self.gateway.get_merchant_order(payment_provider_id)
            payments = merchant_order.get("payments") or []
            if not payments:
                raise ValueError(
                    f"{payment_provider_id} não é payment nem merchant_order "
                    "com payments"
                ) from err
            approved = [p for p in payments if p.get("status") == "approved"]
            chosen = (approved or payments)
            payment_provider_id = str(max(p["id"] for p in chosen))
            logger.info(
                "fallback merchant_order %s -> payment %s",
                merchant_order.get("id"),
                payment_provider_id,
            )
            provider_payment = self.gateway.get_payment(payment_provider_id)

        external_reference = provider_payment.get("external_reference")

        if not external_reference:
            raise ValueError(
                f"Payment {payment_provider_id} has no external_reference"
            )

        order_id = int(external_reference)


        payment = self.repo.get_by_provider_payment_id(payment_provider_id)

        if not payment:
            payments = self.repo.get_by_order_id(order_id)
            payment = payments[0] if payments else None

        if not payment:
            raise ValueError(f"Payment not found for order {order_id}")

        if payment.order_id != order_id:
            raise ValueError(
                f"Payment {payment_provider_id} does not match order {order_id}"
            )

        if payment.status == "approved":
            return payment

        payment.status = provider_payment["status"]
        payment.provider_payment_id = payment_provider_id
        payment.updated_at = datetime.now()

        order = self.order_repo.get_by_id(order_id)

        if order:
            if payment.status == "approved":
                order.status = OrderStatus.COMPLETED
            elif payment.status == "pending":
                order.status = OrderStatus.PROCESSING
            elif payment.status == "rejected":
                order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.now()

        self.session.commit()
        self.session.refresh(payment)

        return payment

