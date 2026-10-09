import logging
from datetime import datetime

from app.api.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    OrderNotFoundException,
    PaymentNotFoundException,
    UserNotFoundException,
)
from app.core.config import get_settings
from app.db.transaction import transacao
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

    def create(self, data, user_id: int) -> Payment:
        """Registra um pagamento para um pedido DO PRÓPRIO usuário.

        SEGURANÇA: antes o `user_id` nem chegava aqui e `amount`/`status`/
        `currency`/`provider_payment_id` vinham crus do cliente, permitindo
        injetar um pagamento `approved` de valor arbitrário em qualquer pedido
        (e ainda bloquear o checkout real via `PAYMENT_ALREADY_EXISTS`).
        Agora: (1) o pedido precisa pertencer ao usuário; (2) o valor cobrado é
        sempre o total do pedido; (3) o status inicial é sempre `pending`.
        A promoção para `approved` só acontece pelo webhook assinado do
        provedor (``process_webhook``).
        """
        order = self.order_repo.get_by_id(data.order_id)

        if not order:
            raise OrderNotFoundException()

        if order.user_id != user_id:
            raise ForbiddenException(
                f"O pedido {data.order_id} não pertence a este usuário.",
                code="ORDER_FORBIDDEN",
            )

        payment = Payment(
            order_id=data.order_id,
            provider=data.provider,
            provider_payment_id=data.provider_payment_id,
            amount=order.total,
            currency="BRL",
            status="pending",
        )

        # Transação explícita: o `with` faz o commit no exit. Antes era um
        # `commit()` solto, que deixava a fronteira de transação implícita.
        with transacao(self.session):
            self.session.add(payment)

        self.session.refresh(payment)

        return payment


    def get_by_id(self, id: int, user_id: int | None = None) -> Payment:
        """Busca um pagamento pelo ID.

        Quando `user_id` é informado, exige que o pagamento pertença a um
        pedido do usuário — fecha o IDOR que devolvia o pagamento de qualquer
        pessoa para qualquer usuário autenticado.
        """
        payment = self.repo.get_by_id(id)

        if payment is None:
            raise PaymentNotFoundException()

        if user_id is not None:
            order = self.order_repo.get_by_id(payment.order_id)
            if order is None or order.user_id != user_id:
                raise ForbiddenException(
                    f"O pagamento {id} não pertence a este usuário.",
                    code="PAYMENT_FORBIDDEN",
                )

        return payment

    def get_by_order_id(self, user, order_id: int) -> list[Payment]:

        user = self.user_repo.get_by_id(user.id)

        if not user:
            raise UserNotFoundException(user_id=user.id)

        order = self.order_repo.get_by_id(order_id)

        if not order:
            raise OrderNotFoundException()

        if order.user_id != user.id:
            raise ForbiddenException(
                f"O pedido {order_id} não pertence a este usuário.",
                code="ORDER_FORBIDDEN",
            )

        return self.repo.get_by_order_id(order_id)

    def get_history(self, user_id: int) -> list[Payment]:
        """Retorna o histórico de pagamentos do usuário em uma única query.

        A aba "Pagamentos" da Minha Conta não precisa mais fazer 1 request por
        pedido (antes um ``Promise.all`` de ``get_by_order_id`` por pedido).
        Se o usuário não existe, levanta erro de autenticação.
        """
        user = self.user_repo.get_by_id(user_id)

        if not user:
            raise UserNotFoundException(user_id=user_id)

        return self.repo.get_by_user_id(user_id)

    def get_history_paginated(
        self, user_id: int, page: int = 1, per_page: int = 20
    ) -> dict:
        """Histórico de pagamentos paginado no envelope ``Page[T]``."""
        from app.schemas.common import montar_pagina

        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(user_id=user_id)

        items, total = self.repo.paginate_by_user_id(user_id, page, per_page)
        return montar_pagina(items, page, per_page, total)

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

        # Se o pedido tem desconto, entra como item de valor NEGATIVO para que
        # o Mercado Pago cobre `subtotal - desconto (+ frete)`. Antes o
        # desconto existia em `order.total` mas era omitido da preferência, e
        # o cliente pagava o subtotal cheio (a mais que o próprio pedido).
        if order.discount_amount and order.discount_amount > 0:
            items.append(
                {
                    "id": "desconto",
                    "title": "Desconto",
                    "quantity": 1,
                    "unit_price": -float(order.discount_amount),
                    "currency_id": "BRL",
                }
            )

        # Se o pedido tem frete, inclui-o como item da preferência para que o
        # Mercado Pago cobre o total (subtotal - desconto + frete). Sem isso o
        # MP soma apenas os produtos (subtotal) e o frete ficaria de fora.
        if order.shipping_cost and order.shipping_cost > 0:
            items.append(
                {
                    "id": "frete",
                    "title": "Frete",
                    "quantity": 1,
                    "unit_price": order.shipping_cost,
                    "currency_id": "BRL",
                }
            )


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




        # Total do pedido capturado ANTES do commit: ao encerrar a transação de
        # leitura, os atributos de `order` ficam expirados/recarregados no acesso.
        total_para_cobrar = order.total

        # Coerência de centavos: a soma dos itens da preferência é o que o MP
        # efetivamente cobra. Se divergir do total do pedido (arredondamento de
        # float acumulado), o valor pago não bate com o registrado — melhor
        # falhar alto do que cobrar um valor inconsistente.
        soma_itens = round(sum(float(i["unit_price"]) * i["quantity"] for i in items), 2)
        if soma_itens != round(float(total_para_cobrar), 2):
            logger.error(
                "Checkout %s: soma dos itens (%.2f) != total do pedido (%.2f)."
                " Abortando para não cobrar valor divergente.",
                order_id,
                soma_itens,
                float(total_para_cobrar),
            )
            raise ConflictException(
                "O total do pedido está inconsistente. Tente novamente.",
                code="ORDER_TOTAL_MISMATCH",
            )

        # FASE 2: encerra a transação de LEITURA antes da chamada externa ao
        # Mercado Pago. Com autocommit=False, a primeira query (get_by_id)
        # abriria uma transação que permaneceria aberta durante todo o request
        # de rede, segurando uma conexão do pool por até o timeout. Fechar essa
        # transação agora libera a conexão; o `Payment` é persistido numa
        # transação nova, logo após o retorno do MP.
        self.session.commit()

        preference = self.gateway.create_preference(preference_data)

        payment = Payment(
            order_id=order_id,
            provider="mercadopago",
            provider_payment_id=None,
            provider_preference_id=preference["id"],
            amount=total_para_cobrar,
            currency="BRL",
            status="pending",
        )

        # Transação explícita para persistir o pagamento.
        with transacao(self.session):
            self.session.add(payment)

        payment_id = payment.id



        # Sandbox: usa o sandbox_init_point (checkout de teste). Faz fallback
        # para o init_point caso o MP não retorne o campo em sandbox.
        checkout_url = preference.get("sandbox_init_point") or preference.get(
            "init_point"
        )



        return {
            "id": payment_id,
            "payment_id": payment_id,
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

        # `transacao` reaproveita a transação caso a sessão já tenha feito query
        # antes (autobegin) — o `begin()` direto lançaria InvalidRequestError.
        # O commit acontece no exit; não chamamos `commit()` lá dentro.
        with transacao(self.session):

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
                # O pedido já estava aprovado: nada a fazer. O `with` abaixo
                # faz o commit (sem mudanças) ao sair do bloco.
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

        # Commit feito por `transacao(self.session)` ao sair do bloco.
        # Não chamamos `commit()`/`refresh()` lá dentro: o commit manual
        # encerrava a transação antes do `__exit__` do context manager, que
        # então operava sobre uma transação já finalizada (e um erro entre o
        # commit manual e o exit deixava os dois estados inconsistentes).
        self.session.refresh(payment)
        return payment
