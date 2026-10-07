"""Testes HTTP das rotas /api/v1/shipping (frete Melhor Envio).

Sucesso: 200 em calculate e apply.
Erros: autenticação 401; validação 422.
"""
from unittest.mock import Mock

import pytest
from helpers import (
    assert_validation_error,
    shipping_apply_response,
)

from app.api.exceptions import (
    OrderNotFoundException,
    ShippingCalculationException,
)

PREFIX = "/api/v1/shipping"

CALCULATE_OFFERS = [
    {"service_id": "1", "name": "PAC", "company_name": "Correios", "price": 27.5, "delivery_time": 4},
    {"service_id": "2", "name": "SEDEX", "company_name": "Correios", "price": 40.0, "delivery_time": 2},
]


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
def patch_shipping_service(patch_service):
    """Instala um Mock no factory ``get_shipping_service`` da rota de shipping."""

    def _instalar(service: Mock):
        return patch_service("shipping", "get_shipping_service", service)

    return _instalar


class TestAuthRequired:
    def test_calculate_requires_auth(self, client):
        response = client.post(f"{PREFIX}/calculate/1")
        assert response.status_code == 401

    def test_apply_requires_auth(self, client):
        response = client.post(f"{PREFIX}/apply", json={"order_id": 1, "price": 10.0})
        assert response.status_code == 401


class TestCalculate:
    def test_calculate_success(self, client, auth_user, patch_shipping_service):
        auth_user(1)
        service = Mock(name="shipping_service")
        service.calculate.return_value = {
            "order_id": 1,
            "offers": CALCULATE_OFFERS,
            "best_offer_index": 0,
            "is_real": True,
        }

        with patch_shipping_service(service):
            response = client.post(f"{PREFIX}/calculate/1")

        assert response.status_code == 200
        body = response.json()
        assert body["order_id"] == 1
        assert body["is_real"] is True
        assert len(body["offers"]) == 2
        assert body["best_offer_index"] == 0
        service.calculate.assert_called_once_with(1, 1)

    def test_calculate_fallback(self, client, auth_user, patch_shipping_service):
        """Sem ofertas reais, o service retorna is_real=False (não é erro)."""
        auth_user(1)
        service = Mock(name="shipping_service")
        service.calculate.return_value = {
            "order_id": 9,
            "offers": [],
            "best_offer_index": None,
            "is_real": False,
            "fallback_reason": "frete ainda não configurado",
        }

        with patch_shipping_service(service):
            response = client.post(f"{PREFIX}/calculate/9")

        assert response.status_code == 200
        assert response.json()["is_real"] is False

    def test_calculate_order_not_found(self, client, auth_user, patch_shipping_service):
        auth_user(1)
        service = Mock(name="shipping_service")
        service.calculate.side_effect = OrderNotFoundException()

        with patch_shipping_service(service):
            response = client.post(f"{PREFIX}/calculate/999")

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "ORDER_NOT_FOUND"

    def test_calculate_gateway_error(self, client, auth_user, patch_shipping_service):
        auth_user(1)
        service = Mock(name="shipping_service")
        service.calculate.side_effect = ShippingCalculationException("API indisponível")

        with patch_shipping_service(service):
            response = client.post(f"{PREFIX}/calculate/1")

        assert response.status_code == 400


class TestApply:
    def test_apply_success(self, client, auth_user, patch_shipping_service):
        auth_user(1)
        service = Mock(name="shipping_service")
        service.apply_to_order.return_value = shipping_apply_response()

        with patch_shipping_service(service):
            response = client.post(
                f"{PREFIX}/apply",
                json={"order_id": 1, "price": 27.5, "delivery_time": 4},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["applied"] is True
        assert body["shipping_cost"] == 27.5
        assert body["total"] == 147.3
        service.apply_to_order.assert_called_once()
        # user.id é derivado do token, não do corpo
        call_kwargs = service.apply_to_order.call_args.kwargs
        assert call_kwargs["order_id"] == 1
        assert call_kwargs["price"] == 27.5

    def test_apply_missing_fields(self, client, auth_user):
        auth_user(1)
        response = client.post(f"{PREFIX}/apply", json={"order_id": 1})

        assert_validation_error(response)

    def test_apply_negative_price(self, client, auth_user):
        auth_user(1)
        response = client.post(
            f"{PREFIX}/apply", json={"order_id": 1, "price": -5.0}
        )

        assert_validation_error(response)

    def test_apply_order_not_found(self, client, auth_user, patch_shipping_service):
        auth_user(1)
        service = Mock(name="shipping_service")
        service.apply_to_order.side_effect = OrderNotFoundException()

        with patch_shipping_service(service):
            response = client.post(
                f"{PREFIX}/apply", json={"order_id": 999, "price": 10.0}
            )

        assert response.status_code == 404
