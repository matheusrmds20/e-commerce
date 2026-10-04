import pytest

from app.models.order import Order, OrderStatus
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate


def make_order(**kwargs):
    fields = dict(
        id=1,
        user_id=1,
        address_id=1,
        subtotal=100.0,
        discount_amount=0.0,
        shipping_cost=0.0,
        total=100.0,
        status=OrderStatus.PENDING,
    )
    fields.update(kwargs)
    return Order(**fields)


def make_payment(**kwargs):
    fields = dict(
        id=1,
        order_id=1,
        provider="mercadopago",
        provider_payment_id=None,
        provider_preference_id="PREF1",
        amount=100.0,
        currency="BRL",
        status="pending",
    )
    fields.update(kwargs)
    return Payment(**fields)


def make_order_item(**kwargs):
    class _Product:
        def __init__(self, title):
            self.title = title

    class _Item:
        def __init__(self, product_id, title, quantity, price):
            self.product_id = product_id
            self.products = _Product(title)
            self.quantity = quantity
            self.price = price

    return _Item(
        kwargs.get("product_id", 1),
        kwargs.get("title", "Livro X"),
        kwargs.get("quantity", 2),
        kwargs.get("price", 50.0),
    )


def create_payload(**kwargs):
    fields = dict(
        provider="mercadopago",
        amount=100.0,
        currency="BRL",
        status="pending",
        order_id=1,
    )
    fields.update(kwargs)
    return PaymentCreate(**fields)


class TestCreate:
    def test_create_success(self, payment_service, order_repo, payment_repo):
        order_repo.get_by_id.return_value = make_order()

        result = payment_service.create(create_payload())

        assert result.order_id == 1
        assert result.provider == "mercadopago"
        assert result.amount == 100.0
        assert result.status == "pending"

        # O pagamento precisa ACABAR no session, senão o commit não persiste nada.
        payment_service.session.add.assert_called_once_with(result)

    def test_create_order_not_found(self, payment_service, order_repo, payment_repo):
        order_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            payment_service.create(create_payload(order_id=99))

        assert str(exc.value) == "Order not found with id 99"
        payment_service.session.add.assert_not_called()


class TestGetById:
    def test_get_by_id_success(self, payment_service, payment_repo):
        payment = make_payment()
        payment_repo.get_by_id.return_value = payment

        assert payment_service.get_by_id(1) is payment

    def test_get_by_id_not_found(self, payment_service, payment_repo):
        payment_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            payment_service.get_by_id(99)

        assert str(exc.value) == "No payment found with id 99"


class TestGetByOrderId:
    def test_get_by_order_id_success(self, payment_service, payment_repo):
        payments = [make_payment()]
        payment_repo.get_by_order_id.return_value = payments

        assert payment_service.get_by_order_id(1) == payments

    def test_get_by_order_id_empty(self, payment_service, payment_repo):
        payment_repo.get_by_order_id.return_value = []

        with pytest.raises(ValueError) as exc:
            payment_service.get_by_order_id(1)

        assert str(exc.value) == "No payments found with order_id 1"


class TestCreateCheckout:
    def _setup_success(self, order_repo, payment_repo):
        order_repo.get_by_id.return_value = make_order()
        order_repo.get_with_items_products.return_value = [make_order_item()]
        payment_repo.get_by_order_id.return_value = []

    def test_create_checkout_success(
        self, payment_service, order_repo, payment_repo, payment_gateway
    ):
        self._setup_success(order_repo, payment_repo)
        payment_gateway.create_preference.return_value = {
            "id": "PREF1",
            "init_point": "https://mp/checkout/PREF1",
        }

        result = payment_service.create_checkout(1, 1)

        assert result["payment_id"] == result["id"]
        assert result["checkout_url"] == "https://mp/checkout/PREF1"
        payment_service.session.add.assert_called_once()
        payment_service.session.commit.assert_called_once()

    def test_create_checkout_sends_correct_preference(
        self, payment_service, order_repo, payment_repo, payment_gateway
    ):
        self._setup_success(order_repo, payment_repo)
        payment_gateway.create_preference.return_value = {
            "id": "PREF1",
            "init_point": "https://mp/checkout/PREF1",
        }

        payment_service.create_checkout(1, 1)

        preference_data = payment_gateway.create_preference.call_args.args[0]
        assert preference_data["external_reference"] == "1"
        assert preference_data["items"] == [
            {
                "id": "1",
                "title": "Livro X",
                "quantity": 2,
                "unit_price": 50.0,
                "currency_id": "BRL",
            }
        ]
        assert set(preference_data["back_urls"]) == {"success", "failure", "pending"}
        assert preference_data["notification_url"].endswith(
            "/api/v1/payments/webhook/"
        )

    def test_create_checkout_usa_sandbox_init_point(
        self, payment_service, order_repo, payment_repo, payment_gateway
    ):
        """O checkout usa o ``sandbox_init_point`` (ambiente de teste)."""
        self._setup_success(order_repo, payment_repo)
        payment_gateway.create_preference.return_value = {
            "id": "PREF1",
            "init_point": "https://mp/real",
            "sandbox_init_point": "https://mp/sandbox",
        }

        result = payment_service.create_checkout(1, 1)

        assert result["checkout_url"] == "https://mp/sandbox"

    def test_create_checkout_fallback_para_init_point(
        self, payment_service, order_repo, payment_repo, payment_gateway
    ):
        """Sem ``sandbox_init_point``, cai no ``init_point``."""
        self._setup_success(order_repo, payment_repo)
        payment_gateway.create_preference.return_value = {
            "id": "PREF1",
            "init_point": "https://mp/real",
        }

        result = payment_service.create_checkout(1, 1)

        assert result["checkout_url"] == "https://mp/real"

    def test_create_checkout_nao_envia_auto_return(
        self, payment_service, order_repo, payment_repo, payment_gateway
    ):
        """A preferência não inclui ``auto_return``."""
        self._setup_success(order_repo, payment_repo)
        payment_gateway.create_preference.return_value = {
            "id": "PREF1",
            "sandbox_init_point": "https://mp/sandbox",
        }

        payment_service.create_checkout(1, 1)

        preference_data = payment_gateway.create_preference.call_args.args[0]
        assert "auto_return" not in preference_data

    def test_create_checkout_sem_urls_retorna_none(
        self, payment_service, order_repo, payment_repo, payment_gateway
    ):
        """Sem nenhuma URL na resposta, ``checkout_url`` fica None."""
        self._setup_success(order_repo, payment_repo)
        payment_gateway.create_preference.return_value = {"id": "PREF1"}

        result = payment_service.create_checkout(1, 1)

        assert result["checkout_url"] is None

    def test_create_checkout_order_not_found(
        self, payment_service, order_repo, payment_repo, payment_gateway
    ):
        order_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            payment_service.create_checkout(99, 1)

        assert str(exc.value) == "Order not found with id 99"
        payment_gateway.create_preference.assert_not_called()

    def test_create_checkout_not_owned(
        self, payment_service, order_repo, payment_repo, payment_gateway
    ):
        order_repo.get_by_id.return_value = make_order(user_id=2)

        with pytest.raises(ValueError) as exc:
            payment_service.create_checkout(1, 1)

        assert str(exc.value) == "Order 1 does not belong to user 1"
        payment_gateway.create_preference.assert_not_called()

    def test_create_checkout_without_items(
        self, payment_service, order_repo, payment_repo, payment_gateway
    ):
        order_repo.get_by_id.return_value = make_order()
        order_repo.get_with_items_products.return_value = []

        with pytest.raises(ValueError) as exc:
            payment_service.create_checkout(1, 1)

        assert str(exc.value) == "Order not found with id 1"
        payment_gateway.create_preference.assert_not_called()

    def test_create_checkout_already_exists(
        self, payment_service, order_repo, payment_repo, payment_gateway
    ):
        order_repo.get_by_id.return_value = make_order()
        order_repo.get_with_items_products.return_value = [make_order_item()]
        payment_repo.get_by_order_id.return_value = [make_payment()]

        with pytest.raises(ValueError) as exc:
            payment_service.create_checkout(1, 1)

        assert str(exc.value) == "Payment already exists for order 1"
        payment_gateway.create_preference.assert_not_called()


class TestProcessWebhook:
    def _gateway_returns(self, gateway, status="approved", order_id=1):
        gateway.get_payment.return_value = {
            "status": status,
            "external_reference": str(order_id),
        }

    def test_webhook_approved_completes_order(
        self, payment_service, payment_repo, order_repo, payment_gateway
    ):
        payment_repo.get_by_provider_payment_id_for_update.return_value = None
        payment_repo.get_by_order_id.return_value = [make_payment()]
        order_repo.get_by_id.return_value = make_order()
        self._gateway_returns(payment_gateway, "approved")

        result = payment_service.process_webhook("MP-PAY-1")

        assert result.status == "approved"
        assert result.provider_payment_id == "MP-PAY-1"
        assert order_repo.get_by_id(1).status == OrderStatus.COMPLETED
        payment_service.session.commit.assert_called_once()

    def test_webhook_approved_dispara_email_automatico(
        self, payment_service, payment_repo, order_repo, payment_gateway
    ):
        """Pagamento aprovado dispara o e-mail de confirmação em background.

        Verifica que a task Celery ``send_order_confirmation_email.delay`` é
        enfileirada com o e-mail do usuário e o payload serializável do pedido.
        """
        from types import SimpleNamespace
        from unittest.mock import patch

        payment_repo.get_by_provider_payment_id_for_update.return_value = None
        payment_repo.get_by_order_id.return_value = [make_payment()]

        # Usamos um objeto simples (não o modelo Order instrumentado) porque a
        # relationship `order_items` do modelo SQLAlchemy não aceita atribuição
        # direta de objetos não-instrumentados.
        order = SimpleNamespace(
            id=1,
            user_id=1,
            total=110.0,
            subtotal=100.0,
            order_items=[
                SimpleNamespace(
                    products=SimpleNamespace(title="Livro X"),
                    quantity=2,
                    price=50.0,
                )
            ],
            users=SimpleNamespace(email="user@example.com"),
        )
        order_repo.get_by_id.return_value = order

        self._gateway_returns(payment_gateway, "approved", order_id=1)

        with patch(
            "app.services.payment_service.send_order_confirmation_email"
        ) as task:
            result = payment_service.process_webhook("MP-PAY-1")

        assert result.status == "approved"
        task.delay.assert_called_once_with(
            order.id,
            "user@example.com",
            {
                "total": 110.0,
                "subtotal": 100.0,
                "items": [{"name": "Livro X", "quantity": 2, "price": 50.0}],
            },
        )

    def test_webhook_approved_sem_usuario_nao_dispara_email(
        self, payment_service, payment_repo, order_repo, payment_gateway
    ):
        """Sem e-mail de usuário, o webhook segue sem enfileirar a task
        (fluxo desgradável, não quebra o processamento do pagamento)."""
        from types import SimpleNamespace
        from unittest.mock import patch

        payment_repo.get_by_provider_payment_id_for_update.return_value = None
        payment_repo.get_by_order_id.return_value = [make_payment()]
        order = SimpleNamespace(
            id=1,
            user_id=1,
            users=None,
            order_items=[],
        )
        order_repo.get_by_id.return_value = order
        self._gateway_returns(payment_gateway, "approved", order_id=1)

        with patch(
            "app.services.payment_service.send_order_confirmation_email"
        ) as task:
            result = payment_service.process_webhook("MP-PAY-1")

        assert result.status == "approved"
        task.delay.assert_not_called()

    def test_webhook_approved_dispara_geracao_comprovante(
        self, payment_service, payment_repo, order_repo, payment_gateway
    ):
        """Pagamento aprovado enfileira a geração do comprovante PDF.

        A task ``generate_order_receipt.delay`` é chamada com o id do pedido
        quando o pagamento é aprovado, junto do disparo do e-mail.
        """
        from types import SimpleNamespace
        from unittest.mock import patch

        payment_repo.get_by_provider_payment_id_for_update.return_value = None
        payment_repo.get_by_order_id.return_value = [make_payment()]
        order = SimpleNamespace(
            id=1,
            user_id=1,
            total=110.0,
            subtotal=100.0,
            order_items=[SimpleNamespace(
                products=SimpleNamespace(title="Livro X"),
                quantity=2,
                price=50.0,
            )],
            users=SimpleNamespace(email="user@example.com"),
        )
        order_repo.get_by_id.return_value = order
        self._gateway_returns(payment_gateway, "approved", order_id=1)

        with patch(
            "app.services.payment_service.send_order_confirmation_email"
        ) as email_task, patch(
            "app.services.payment_service.generate_order_receipt"
        ) as receipt_task:
            result = payment_service.process_webhook("MP-PAY-1")

        assert result.status == "approved"
        email_task.delay.assert_called_once()
        receipt_task.delay.assert_called_once_with(1)

    def test_webhook_merchant_order_resolves_payment(
        self, payment_service, payment_repo, order_repo, payment_gateway
    ):
        """Notificação de merchant_order: id é da order; o payment vem de dentro."""
        payment_repo.get_by_provider_payment_id_for_update.return_value = None
        payment_repo.get_by_order_id.return_value = [make_payment()]
        order_repo.get_by_id.return_value = make_order()

        payment_gateway.get_merchant_order.return_value = {
            "id": 5000,
            "external_reference": "1",
            "payments": [{"id": 9001}, {"id": 9002}],
        }
        payment_gateway.get_payment.return_value = {
            "status": "approved",
            "external_reference": "1",
        }

        result = payment_service.process_webhook("5000", topic="merchant_order")

        assert result.status == "approved"
        assert result.provider_payment_id == "9002"  # maior id entre os payments
        payment_gateway.get_merchant_order.assert_called_once_with("5000")
        payment_gateway.get_payment.assert_called_once_with("9002")
        assert order_repo.get_by_id(1).status == OrderStatus.COMPLETED

    def test_webhook_pending_sets_processing(
        self, payment_service, payment_repo, order_repo, payment_gateway
    ):
        payment_repo.get_by_provider_payment_id_for_update.return_value = None
        payment_repo.get_by_order_id.return_value = [make_payment()]
        order_repo.get_by_id.return_value = make_order()
        self._gateway_returns(payment_gateway, "pending")

        result = payment_service.process_webhook("MP-PAY-1")

        assert result.status == "pending"
        assert order_repo.get_by_id(1).status == OrderStatus.PROCESSING

    def test_webhook_rejected_cancels_order(
        self, payment_service, payment_repo, order_repo, payment_gateway
    ):
        payment_repo.get_by_provider_payment_id_for_update.return_value = None
        payment_repo.get_by_order_id.return_value = [make_payment()]
        order_repo.get_by_id.return_value = make_order()
        self._gateway_returns(payment_gateway, "rejected")

        result = payment_service.process_webhook("MP-PAY-1")

        assert result.status == "rejected"
        assert order_repo.get_by_id(1).status == OrderStatus.CANCELLED

    def test_webhook_links_by_provider_payment_id(
        self, payment_service, payment_repo, order_repo, payment_gateway
    ):
        """Se o pagamento já está vinculado, não cai no fallback por order_id."""
        payment_repo.get_by_provider_payment_id_for_update.return_value = make_payment()
        order_repo.get_by_id.return_value = make_order()
        self._gateway_returns(payment_gateway, "approved")

        result = payment_service.process_webhook("MP-PAY-1")

        assert result.provider_payment_id == "MP-PAY-1"
        payment_repo.get_by_order_id.assert_not_called()

    def test_webhook_idempotent_when_already_approved(
        self, payment_service, payment_repo, order_repo, payment_gateway
    ):
        payment_repo.get_by_provider_payment_id_for_update.return_value = make_payment(
            status="approved"
        )
        self._gateway_returns(payment_gateway, "approved")

        result = payment_service.process_webhook("MP-PAY-1")

        assert result.status == "approved"
        # Já aprovado: não deve reabrir transação nem reprocessar o pedido.
        payment_service.session.commit.assert_not_called()
        order_repo.get_by_id.assert_not_called()

    def test_webhook_updates_timestamp(
        self, payment_service, payment_repo, order_repo, payment_gateway
    ):
        payment_repo.get_by_provider_payment_id_for_update.return_value = None
        payment = make_payment()
        before = payment.updated_at
        payment_repo.get_by_order_id.return_value = [payment]
        order_repo.get_by_id.return_value = make_order()
        self._gateway_returns(payment_gateway, "approved")

        result = payment_service.process_webhook("MP-PAY-1")

        assert result.updated_at is not None
        assert result.updated_at != before

    def test_webhook_without_external_reference(
        self, payment_service, payment_repo, payment_gateway
    ):
        payment_gateway.get_payment.return_value = {"status": "approved"}

        with pytest.raises(ValueError) as exc:
            payment_service.process_webhook("MP-PAY-1")

        assert str(exc.value) == "Payment MP-PAY-1 has no external_reference"

    def test_webhook_payment_not_found(
        self, payment_service, payment_repo, payment_gateway
    ):
        payment_repo.get_by_provider_payment_id_for_update.return_value = None
        payment_repo.get_by_order_id.return_value = []
        self._gateway_returns(payment_gateway, "approved")

        with pytest.raises(ValueError) as exc:
            payment_service.process_webhook("MP-PAY-1")

        assert str(exc.value) == "Payment not found for order 1"

    def test_webhook_order_mismatch(
        self, payment_service, payment_repo, payment_gateway
    ):
        payment_repo.get_by_provider_payment_id_for_update.return_value = make_payment(
            order_id=2
        )
        self._gateway_returns(payment_gateway, "approved", order_id=1)

        with pytest.raises(ValueError) as exc:
            payment_service.process_webhook("MP-PAY-1")

        assert str(exc.value) == "Payment MP-PAY-1 does not match order 1"
