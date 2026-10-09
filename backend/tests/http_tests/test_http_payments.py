"""Testes HTTP da rota /api/v1/payments.

Sucesso: 201 na criação de pagamento e de checkout; 200 nas buscas e no
webhook.
Erros: validação 422; assinatura de webhook inválida 401; falha do service
(ValueError) vira 500 — ver RELATORIO_TESTES_HTTP.md.

AUTENTICAÇÃO: as rotas de criação/consulta exigem Bearer token
(``Depends(get_current_user)``). O webhook NÃO exige token: quem chama é o
Mercado Pago, e a autenticidade é garantida pela assinatura (``x-signature``).

NOTA: o PaymentService real lança ``ValueError`` em vez das exceções de
domínio — em produção esses erros viram 500 (o handler genérico não converte
ValueError). Os testes abaixo refletem o comportamento atual.
"""
from unittest.mock import Mock, patch

import pytest
from helpers import assert_validation_error, payment_payload

PREFIX = "/api/v1/payments"

CREATE_OK = {
    "provider": "mercadopago",
    "amount": 119.8,
    "currency": "BRL",
    "status": "pending",
    "order_id": 1,
}


@pytest.fixture
def auth_user():
    """Usuário autenticado injetado no lugar de ``get_current_user``."""
    from app.api.deps import get_current_user
    from app.main import app

    def _definir(user_id: int = 1):
        user = Mock(name="user")
        user.id = user_id
        user.email = "user@example.com"
        user.full_name = "John Doe"
        user.is_active = True

        app.dependency_overrides[get_current_user] = lambda: user
        return user

    yield _definir

    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def patch_payment_service(patch_service):
    """Instala um Mock no factory ``get_payment_service`` da rota de payments."""

    def _instalar(service: Mock):
        return patch_service("payments", "get_payment_service", service)

    return _instalar


class TestAuthRequired:
    """Sem token, nenhuma rota de pagamento autenticada deve responder."""

    def test_create_requires_auth(self, client):
        response = client.post(f"{PREFIX}/create", json=CREATE_OK)
        assert response.status_code == 401

    def test_get_by_id_requires_auth(self, client):
        response = client.get(f"{PREFIX}/get/1")
        assert response.status_code == 401

    def test_get_by_order_requires_auth(self, client):
        response = client.get(f"{PREFIX}/order/1")
        assert response.status_code == 401

    def test_history_requires_auth(self, client):
        response = client.get(f"{PREFIX}/history")
        assert response.status_code == 401

    def test_checkout_requires_auth(self, client):
        response = client.post(f"{PREFIX}/checkout/1")
        assert response.status_code == 401


class TestCreatePayment:
    def test_create_success(self, client, auth_user, patch_payment_service):
        auth_user(1)
        service = Mock(name="payment_service")
        service.create.return_value = payment_payload()

        with patch_payment_service(service):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert response.status_code == 201
        body = response.json()
        assert body["id"] == 1
        assert body["provider"] == "mercadopago"
        assert body["status"] == "pending"
        assert body["order_id"] == 1
        # SEGURANÇA: a rota repassa o id do usuário do token ao service, que
        # valida a posse do pedido e deriva o valor.
        service.create.assert_called_once()
        assert service.create.call_args.args[1] == 1

    def test_create_response_matches_schema(self, client, auth_user, patch_payment_service):
        """Todos os campos do PaymentResponse devem estar presentes."""
        auth_user(1)
        service = Mock(name="payment_service")
        service.create.return_value = payment_payload(provider_payment_id="MP-1")

        with patch_payment_service(service):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert response.status_code == 201
        assert set(response.json()) == {
            "id",
            "provider",
            "provider_payment_id",
            "amount",
            "currency",
            "status",
            "created_at",
            "updated_at",
            "order_id",
        }

    def test_create_invalid_payload(self, client, auth_user):
        auth_user(1)
        response = client.post(f"{PREFIX}/create", json={"provider": "mercadopago"})

        assert_validation_error(response)

    def test_create_invalid_amount_type(self, client, auth_user):
        auth_user(1)
        response = client.post(
            f"{PREFIX}/create", json={**CREATE_OK, "amount": "muito"}
        )

        assert_validation_error(response)


class TestGetPayment:
    def test_get_by_id_success(self, client, auth_user, patch_payment_service):
        auth_user(1)
        service = Mock(name="payment_service")
        service.get_by_id.return_value = payment_payload(id=7)

        with patch_payment_service(service):
            response = client.get(f"{PREFIX}/get/7")

        assert response.status_code == 200
        assert response.json()["id"] == 7
        # SEGURANÇA: o user_id do token é enviado ao service (checagem de dono).
        service.get_by_id.assert_called_once_with(7, 1)

    def test_get_by_id_not_found_is_500(self, client, auth_user, patch_payment_service):
        """O service lança ValueError; sem handler dedicado, vira 500."""
        auth_user(1)
        service = Mock(name="payment_service")
        service.get_by_id.side_effect = ValueError("No payment found with id 99")

        with patch_payment_service(service):
            response = client.get(f"{PREFIX}/get/99")

        assert response.status_code == 500

    def test_get_by_id_invalid_path_param(self, client, auth_user):
        auth_user(1)
        response = client.get(f"{PREFIX}/get/abc")

        assert_validation_error(response)


class TestGetHistory:
    """GET /payments/history devolve o histórico paginado em 1 request."""

    @staticmethod
    def _pagina(items):
        return {
            "data": items,
            "meta": {
                "page": 1,
                "per_page": 20,
                "total": len(items),
                "total_pages": 1 if items else 0,
            },
        }

    def test_history_success(self, client, auth_user, patch_payment_service):
        auth_user(1)
        service = Mock(name="payment_service")
        service.get_history_paginated.return_value = self._pagina(
            [
                payment_payload(id=1),
                payment_payload(id=2, status="approved"),
            ]
        )

        with patch_payment_service(service):
            response = client.get(f"{PREFIX}/history")

        assert response.status_code == 200
        body = response.json()
        assert len(body["data"]) == 2
        assert [p["id"] for p in body["data"]] == [1, 2]
        service.get_history_paginated.assert_called_once_with(1, 1, 20)

    def test_history_vazio(self, client, auth_user, patch_payment_service):
        auth_user(1)
        service = Mock(name="payment_service")
        service.get_history_paginated.return_value = self._pagina([])

        with patch_payment_service(service):
            response = client.get(f"{PREFIX}/history")

        assert response.status_code == 200
        assert response.json()["data"] == []


class TestGetPaymentsByOrder:
    def test_get_by_order_success(self, client, auth_user, patch_payment_service):
        auth_user(1)
        service = Mock(name="payment_service")
        service.get_by_order_id.return_value = [
            payment_payload(id=1),
            payment_payload(id=2, status="approved"),
        ]

        with patch_payment_service(service):
            response = client.get(f"{PREFIX}/order/1")

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 2
        assert [p["id"] for p in body] == [1, 2]
        # A rota repassa (user, order_id) para o service. `user` é o objeto
        # autenticado injetado pelo override de `get_current_user`.
        args, _ = service.get_by_order_id.call_args
        chamado_user, chamado_order_id = args
        assert chamado_order_id == 1
        assert chamado_user.id == 1

    def test_get_by_order_empty_list(self, client, auth_user, patch_payment_service):
        auth_user(1)
        service = Mock(name="payment_service")
        service.get_by_order_id.return_value = []

        with patch_payment_service(service):
            response = client.get(f"{PREFIX}/order/1")

        assert response.status_code == 200
        assert response.json() == []

    def test_get_by_order_not_found_is_500(
        self, client, auth_user, patch_payment_service
    ):
        auth_user(1)
        service = Mock(name="payment_service")
        service.get_by_order_id.side_effect = ValueError(
            "No payments found with order_id 99"
        )

        with patch_payment_service(service):
            response = client.get(f"{PREFIX}/order/99")

        assert response.status_code == 500


class TestCreateCheckout:
    def test_checkout_success(self, client, auth_user, patch_payment_service):
        auth_user(1)
        service = Mock(name="payment_service")
        service.create_checkout.return_value = {
            "id": 1,
            "payment_id": 1,
            "checkout_url": "https://mp/checkout/PREF1",
        }

        with patch_payment_service(service):
            response = client.post(f"{PREFIX}/checkout/1")

        assert response.status_code == 201
        body = response.json()
        assert body["payment_id"] == 1
        assert body["checkout_url"] == "https://mp/checkout/PREF1"

    def test_checkout_passes_order_and_authenticated_user(
        self, client, auth_user, patch_payment_service
    ):
        """A rota deve repassar (order_id, user.id) do token — nunca da query."""
        auth_user(42)
        service = Mock(name="payment_service")
        service.create_checkout.return_value = {
            "id": 1,
            "payment_id": 1,
            "checkout_url": "https://mp/checkout/PREF1",
        }

        with patch_payment_service(service):
            client.post(f"{PREFIX}/checkout/7")

        service.create_checkout.assert_called_once_with(7, 42)

    def test_checkout_order_not_found_is_500(
        self, client, auth_user, patch_payment_service
    ):
        auth_user(1)
        service = Mock(name="payment_service")
        service.create_checkout.side_effect = ValueError(
            "Order not found with id 99"
        )

        with patch_payment_service(service):
            response = client.post(f"{PREFIX}/checkout/99")

        assert response.status_code == 500


@pytest.fixture
def validar_assinatura():
    """Controla a flag ``VALIDATE_WEBHOOK_SIGNATURE`` da rota de webhook.

    Como ``settings`` é importado no módulo da rota, o patch precisa ser no
    objeto ``app.api.v1.payments.settings``.
    """

    def _definir(valor: bool):
        return patch(
            "app.api.v1.payments.settings.VALIDATE_WEBHOOK_SIGNATURE", valor
        )

    return _definir


class TestWebhook:
    """O webhook não exige token; a autenticidade vem da assinatura.

    O endpoint processa SOMENTE o formato Webhook novo (?data.id=...&type=...).
    Notificações IPN clássicas (?id=...&topic=...) são ignoradas.
    """

    def test_webhook_assinatura_invalida_retorna_401(
        self, client, validar_assinatura
    ):
        """Com validação ligada, assinatura inválida vira 401."""
        import mercadopago.webhook as mpw

        erro = mpw.InvalidWebhookSignatureError(
            mpw.SignatureFailureReason.SIGNATURE_MISMATCH
        )

        with (
            validar_assinatura(True),
            patch(
                "app.api.v1.payments.WebhookSignatureValidator.validate",
                side_effect=erro,
            ),
        ):
            response = client.post(
                f"{PREFIX}/webhook/?data.id=123&type=payment",
                json={"type": "payment", "data": {"id": "123"}},
            )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid webhook signature"

    def test_webhook_assinatura_invalida_aceita_quando_validacao_desligada(
        self, client, patch_payment_service, validar_assinatura
    ):
        """Com VALIDATE_WEBHOOK_SIGNATURE=false (sandbox), o webhook é aceito."""
        import mercadopago.webhook as mpw

        erro = mpw.InvalidWebhookSignatureError(
            mpw.SignatureFailureReason.SIGNATURE_MISMATCH
        )
        service = Mock(name="payment_service")

        with (
            validar_assinatura(False),
            patch(
                "app.api.v1.payments.WebhookSignatureValidator.validate",
                side_effect=erro,
            ),
            patch_payment_service(service),
        ):
            response = client.post(
                f"{PREFIX}/webhook/?data.id=MP-1&type=payment",
                json={"type": "payment", "data": {"id": "MP-1"}},
            )

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        service.process_webhook.assert_called_once_with("MP-1", "payment")

    def test_webhook_sucesso_formato_novo(
        self, client, patch_payment_service, validar_assinatura
    ):
        """Formato novo: ?data.id=...&type=topic_merchant_order_wh."""
        service = Mock(name="payment_service")

        with (
            validar_assinatura(True),
            patch(
                "app.api.v1.payments.WebhookSignatureValidator.validate",
                return_value=None,
            ),
            patch_payment_service(service),
        ):
            response = client.post(
                f"{PREFIX}/webhook/?data.id=MP-1&type=topic_merchant_order_wh",
                json={"type": "topic_merchant_order_wh", "data": {"id": "MP-1"}},
            )

        assert response.status_code == 200
        service.process_webhook.assert_called_once_with("MP-1", "merchant_order")

    def test_webhook_formato_ipn_classico_e_ignorado(
        self, client, patch_payment_service
    ):
        """IPN clássico (?id=...&topic=...) é ignorado: 200 e não processa."""
        service = Mock(name="payment_service")

        with patch_payment_service(service):
            response = client.post(
                f"{PREFIX}/webhook/?id=MP-9&topic=payment",
                json={"type": "payment", "id": "MP-9"},
            )

        assert response.status_code == 200
        assert response.json()["status"] == "ignored"
        service.process_webhook.assert_not_called()

    def test_webhook_tipo_nao_pagamento_e_ignorado(
        self, client, patch_payment_service, validar_assinatura
    ):
        """Tipos que não são payment/merchant_order (ex.: mp-connect) → ignored."""
        service = Mock(name="payment_service")

        with (
            validar_assinatura(True),
            patch(
                "app.api.v1.payments.WebhookSignatureValidator.validate",
                return_value=None,
            ),
            patch_payment_service(service),
        ):
            response = client.post(
                f"{PREFIX}/webhook/?data.id=MP-1&type=mp-connect",
                json={"type": "mp-connect", "data": {"id": "MP-1"}},
            )

        assert response.status_code == 200
        assert response.json()["status"] == "ignored"
        service.process_webhook.assert_not_called()

    def test_webhook_erro_no_service_retorna_200(
        self, client, patch_payment_service, validar_assinatura
    ):
        """Falha no processamento vira 200 com status=error (evita retry do MP)."""
        service = Mock(name="payment_service")
        service.process_webhook.side_effect = ValueError(
            "Payment not found for order 1"
        )

        with (
            validar_assinatura(True),
            patch(
                "app.api.v1.payments.WebhookSignatureValidator.validate",
                return_value=None,
            ),
            patch_payment_service(service),
        ):
            response = client.post(
                f"{PREFIX}/webhook/?data.id=MP-1&type=payment",
                json={"type": "payment", "data": {"id": "MP-1"}},
            )

        assert response.status_code == 200
        assert response.json()["status"] == "error"

    def test_webhook_passes_signature_headers_to_validator(
        self, client, validar_assinatura
    ):
        """Os headers x-signature/x-request-id devem chegar ao validador."""
        with (
            validar_assinatura(True),
            patch(
                "app.api.v1.payments.WebhookSignatureValidator.validate",
                return_value=None,
            ) as mock_validate,
        ):
            client.post(
                f"{PREFIX}/webhook/?data.id=MP-1&type=payment",
                json={"type": "payment", "data": {"id": "MP-1"}},
                headers={
                    "x-signature": "ts=1,v1=abc",
                    "x-request-id": "req-1",
                },
            )

        args = mock_validate.call_args.args
        assert args[0] == "ts=1,v1=abc"
        assert args[1] == "req-1"
        assert args[2] == "MP-1"
