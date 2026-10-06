import logging
from datetime import datetime

from app.api.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    OrderNotFoundException,
    PaymentNotFoundException,
)
from app.core.config import get_settings
from app.integrations.MercadoPago.geteway import MercadoPagoGateway
from app.models.order import OrderStatus
from app.models.payment import Payment
from app.repositories.order_repo import OrderRepository
from app.repositories.payment_repo import PaymentRepository
from app.repositories.user_repo import UserRepository
from app.utils.email import build_order_details, send_order_confirmation_email
from app.utils.receipt_tasks import generate_order_receipt

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
            raise OrderNotFoundException()

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
            raise PaymentNotFoundException()

        return payment

    def get_by_order_id(self, order_id: int) -> list[Payment]:
        # Pedido sem pagamentos é estado normal (lista vazia), não erro.
        return self.repo.get_by_order_id(order_id)

    def create_checkout(self, order_id: int, user_id: int) -> dict:


        order = self.order_repo.get_by_id(order_id)

        if not order:
            raise OrderNotFoundException()

        if order.user_id != user_id:
            raise ForbiddenException(
                f"O pedido {order_id} não pertence a este usuário.",
                code="ORDER_FORBIDDEN",
            )


        order_items = self.order_repo.get_with_items_products(order_id)

        if not order_items:
            raise OrderNotFoundException()


        payment_already_exists = self.repo.get_by_order_id(order_id)

        if payment_already_exists:
            raise ConflictException(
                "Já existe um pagamento para este pedido.",
                code="PAYMENT_ALREADY_EXISTS",
            )

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


        if topic == "merchant_order":
            merchant_order = self.gateway.get_merchant_order(payment_provider_id)
            payments = merchant_order.get("payments") or []
            if not payments:
                raise BadRequestException(
                    f"Merchant order {payment_provider_id} has no payments"
                )

            approved = [p for p in payments if p.get("status") == "approved"]
            chosen = (approved or payments)
            payment_provider_id = str(max(p["id"] for p in chosen))


        try:
            provider_payment = self.gateway.get_payment(payment_provider_id)
        except RuntimeError as err:
            if "404" not in str(err):
                raise

            merchant_order = self.gateway.get_merchant_order(payment_provider_id)
            payments = merchant_order.get("payments") or []
            if not payments:
                raise BadRequestException(
                    f"{payment_provider_id} não é payment nem merchant_order "
                    "com payments"
                ) from err
            approved = [p for p in payments if p.get("status") == "approved"]
            chosen = (approved or payments)
            payment_provider_id = str(max(p["id"] for p in chosen))

            provider_payment = self.gateway.get_payment(payment_provider_id)

        external_reference = provider_payment.get("external_reference")

        if not external_reference:
            raise BadRequestException(
                f"Payment {payment_provider_id} has no external_reference"
            )

        order_id = int(external_reference)

        with self.session.begin():

            payment = self.repo.get_by_provider_payment_id_for_update(payment_provider_id)

            if not payment:
                payments = self.repo.get_by_order_id(order_id)
                payment = payments[0] if payments else None

            if not payment:
                raise PaymentNotFoundException()

            if payment.order_id != order_id:
                raise ConflictException(
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
                    try:
                        user_email = order.users.email if order.users else None
                        if user_email:
                            send_order_confirmation_email.delay(
                                order.id,
                                user_email,
                                build_order_details(order),
                            )
                    except Exception as exc:
                        logger.warning(
                            "Falha ao enfileirar e-mail de confirmação "
                            "para o pedido %s: %s",
                            order.id,
                            exc,
                        )

                    # Gera o comprovante PDF em background (só quando aprovado).
                    try:
                        generate_order_receipt.delay(order.id)
                    except Exception as exc:
                        logger.warning(
                            "Falha ao enfileirar geração do comprovante "
                            "para o pedido %s: %s",
                            order.id,
                            exc,
                        )
                elif payment.status == "pending":
                    order.status = OrderStatus.PROCESSING
                elif payment.status == "rejected":
                    order.status = OrderStatus.CANCELLED
                order.updated_at = datetime.now()

            self.session.commit()
            self.session.refresh(payment)

            return payment
