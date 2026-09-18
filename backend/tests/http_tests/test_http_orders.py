"""Testes HTTP da rota /api/v1/orders.

Sucesso: 201/200 com payloads válidos (criação, listagem, busca, itens,
update e delete).
Erros: validação 422, pedido/endereço/produto inexistente 404, pedido de
outro usuário 403, estoque insuficiente 409 e cupom inválido 400.

AUTENTICAÇÃO: todas as rotas exigem Bearer token e derivam o ``user_id`` do
usuário autenticado (``Depends(get_current_user)``). O ``user_id`` NÃO é mais
aceito como query param — fechou o IDOR de ler/criar pedido em nome de outra
pessoa. Ver test_http_cart.py para o padrão.

NOTA: o OrderService real sinaliza falhas com ``ValueError``; as rotas o
traduzem para 400/403/404/409 (ver ``_traduzir_value_error`` em
``app/api/v1/orders.py``).
"""
from unittest.mock import Mock, patch

import pytest
from helpers import assert_error, assert_validation_error, order_payload

from app.api.exceptions import (
    BadRequestException,
    ForbiddenException,
    InsufficientStockException,
    InvalidCouponException,
    NotFoundException,
    ProductNotFoundException,
)

PREFIX = "/api/v1/orders"

CREATE_OK = {
    "address_id": 1,
    "items": [{"product_id": 1, "quantity": 2}],
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


class TestAuthRequired:
    """Sem token, nenhuma rota de pedido deve responder."""

    def test_create_requires_auth(self, client):
        response = client.post(f"{PREFIX}/create", json=CREATE_OK)
        assert response.status_code == 401

    def test_list_requires_auth(self, client):
        response = client.get(f"{PREFIX}/list")
        assert response.status_code == 401

    def test_get_requires_auth(self, client):
        response = client.get(f"{PREFIX}/get/1")
        assert response.status_code == 401

    def test_items_requires_auth(self, client):
        response = client.get(f"{PREFIX}/items/1")
        assert response.status_code == 401

    def test_update_requires_auth(self, client):
        response = client.patch(f"{PREFIX}/update/1", json={"status": "processing"})
        assert response.status_code == 401

    def test_delete_requires_auth(self, client):
        response = client.delete(f"{PREFIX}/delete/1")
        assert response.status_code == 401

    def test_user_id_query_is_ignored(self, client, auth_user):
        """Passar user_id na query não muda quem é o dono (anti-IDOR).

        O token do usuário 1 autentica; o ``user_id=999`` da query é ignorado
        e o service recebe 1.
        """
        auth_user(1)
        svc = Mock(name="order_service")
        svc.get_by_user_id.return_value = [order_payload()]

        with patch("app.api.v1.orders.get_order_service", return_value=svc):
            response = client.get(f"{PREFIX}/list?user_id=999")

        assert response.status_code == 200
        svc.get_by_user_id.assert_called_once_with(1)


class TestCreateOrder:
    def test_create_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="order_service")
        svc.create.return_value = order_payload()

        with patch("app.api.v1.orders.get_order_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert response.status_code == 201
        body = response.json()
        assert body["id"] == 1
        assert body["user_id"] == 1
        assert body["status"] == "pending"
        assert body["total"] == 119.8
        assert len(body["order_items"]) == 1

    def test_create_uses_token_user_id(self, client, auth_user):
        """O ``user_id`` passado ao service é o do token, não de query."""
        auth_user(7)
        svc = Mock(name="order_service")
        svc.create.return_value = order_payload(user_id=7)

        with patch("app.api.v1.orders.get_order_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert response.status_code == 201
        assert svc.create.call_args.args[0] == 7

    def test_create_address_not_found(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="order_service")
        svc.create.side_effect = NotFoundException(
            "No address found with id 999", code="ADDRESS_NOT_FOUND"
        )

        with patch("app.api.v1.orders.get_order_service", return_value=svc):
            response = client.post(
                f"{PREFIX}/create", json={**CREATE_OK, "address_id": 999}
            )

        assert_error(response, 404, "ADDRESS_NOT_FOUND")

    def test_create_product_not_found(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="order_service")
        svc.create.side_effect = ProductNotFoundException()

        with patch("app.api.v1.orders.get_order_service", return_value=svc):
            response = client.post(
                f"{PREFIX}/create",
                json={"address_id": 1, "items": [{"product_id": 999, "quantity": 1}]},
            )

        assert_error(response, 404, "PRODUCT_NOT_FOUND")

    def test_create_insufficient_stock(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="order_service")
        svc.create.side_effect = InsufficientStockException("Clean Code", 2)

        with patch("app.api.v1.orders.get_order_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert_error(response, 409, "INSUFFICIENT_STOCK")

    def test_create_invalid_coupon(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="order_service")
        svc.create.side_effect = InvalidCouponException()

        with patch("app.api.v1.orders.get_order_service", return_value=svc):
            response = client.post(
                f"{PREFIX}/create", json={**CREATE_OK, "coupon_id": 999}
            )

        assert_error(response, 400, "INVALID_COUPON")

    def test_create_address_not_owned(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="order_service")
        svc.create.side_effect = ForbiddenException("Address is not owned by user")

        with patch("app.api.v1.orders.get_order_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert_error(response, 403, "FORBIDDEN")

    def test_create_item_quantity_zero(self, client, auth_user):
        auth_user(1)
        response = client.post(
            f"{PREFIX}/create",
            json={"address_id": 1, "items": [{"product_id": 1, "quantity": 0}]},
        )
        assert_validation_error(response)

    def test_create_missing_address_id(self, client, auth_user):
        auth_user(1)
        response = client.post(
            f"{PREFIX}/create", json={"items": [{"product_id": 1, "quantity": 1}]}
        )
        assert_validation_error(response)

    def test_create_item_missing_product_id(self, client, auth_user):
        auth_user(1)
        response = client.post(
            f"{PREFIX}/create",
            json={"address_id": 1, "items": [{"quantity": 1}]},
        )
        assert_validation_error(response)


class TestListOrders:
    def test_list_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="order_service")
        svc.get_by_user_id.return_value = [order_payload(), order_payload(id=2)]

        with patch("app.api.v1.orders.get_order_service", return_value=svc):
            response = client.get(f"{PREFIX}/list")

        assert response.status_code == 200
        assert len(response.json()) == 2
        svc.get_by_user_id.assert_called_once_with(1)

    def test_list_not_found(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="order_service")
        svc.get_by_user_id.side_effect = NotFoundException(
            "No orders found with user_id 999", code="ORDER_NOT_FOUND"
        )

        with patch("app.api.v1.orders.get_order_service", return_value=svc):
            response = client.get(f"{PREFIX}/list")

        assert_error(response, 404, "ORDER_NOT_FOUND")


class TestGetOrder:
    def test_get_by_id_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="order_service")
        svc.get_by_id.return_value = order_payload()

        with patch("app.api.v1.orders.get_order_service", return_value=svc):
            response = client.get(f"{PREFIX}/get/1")

        assert response.status_code == 200
        assert response.json()["id"] == 1
        svc.get_by_id.assert_called_once_with(1, 1)

    def test_get_by_id_not_found(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="order_service")
        svc.get_by_id.side_effect = NotFoundException(
            "No order found with id 999", code="ORDER_NOT_FOUND"
        )

        with patch("app.api.v1.orders.get_order_service", return_value=svc):
            response = client.get(f"{PREFIX}/get/999")

        assert_error(response, 404, "ORDER_NOT_FOUND")

    def test_get_by_id_not_owned(self, client, auth_user):
        auth_user(2)
        svc = Mock(name="order_service")
        svc.get_by_id.side_effect = ForbiddenException("Order is not owned by user")

        with patch("app.api.v1.orders.get_order_service", return_value=svc):
            response = client.get(f"{PREFIX}/get/1")

        assert_error(response, 403, "FORBIDDEN")

    def test_get_items_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="order_service")
        svc.get_with_items.return_value = [
            {"id": 1, "order_id": 1, "product_id": 1, "quantity": 2, "price": 59.9}
        ]

        with patch("app.api.v1.orders.get_order_service", return_value=svc):
            response = client.get(f"{PREFIX}/items/1")

        assert response.status_code == 200
        assert len(response.json()) == 1
        svc.get_with_items.assert_called_once_with(1, 1)

    def test_get_items_not_found(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="order_service")
        svc.get_with_items.side_effect = NotFoundException(
            "No items found in order with id 999", code="ORDER_ITEM_NOT_FOUND"
        )

        with patch("app.api.v1.orders.get_order_service", return_value=svc):
            response = client.get(f"{PREFIX}/items/999")

        assert_error(response, 404, "ORDER_ITEM_NOT_FOUND")


class TestUpdateOrder:
    def test_update_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="order_service")
        svc.update.return_value = order_payload(status="processing")

        with patch("app.api.v1.orders.get_order_service", return_value=svc):
            response = client.patch(
                f"{PREFIX}/update/1", json={"status": "processing"}
            )

        assert response.status_code == 200
        assert response.json()["status"] == "processing"

    def test_update_not_found(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="order_service")
        svc.update.side_effect = NotFoundException(
            "No order found with id 999", code="ORDER_NOT_FOUND"
        )

        with patch("app.api.v1.orders.get_order_service", return_value=svc):
            response = client.patch(
                f"{PREFIX}/update/999", json={"status": "processing"}
            )

        assert_error(response, 404, "ORDER_NOT_FOUND")

    def test_update_cancelled_order(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="order_service")
        svc.update.side_effect = BadRequestException(
            "Cannot update a cancelled order", code="INVALID_STATE_TRANSITION"
        )

        with patch("app.api.v1.orders.get_order_service", return_value=svc):
            response = client.patch(
                f"{PREFIX}/update/1", json={"status": "processing"}
            )

        assert_error(response, 400, "INVALID_STATE_TRANSITION")

    def test_update_invalid_status(self, client, auth_user):
        auth_user(1)
        response = client.patch(
            f"{PREFIX}/update/1", json={"status": "inexistente"}
        )
        assert_validation_error(response)


class TestDeleteOrder:
    def test_delete_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="order_service")
        svc.delete.return_value = order_payload()

        with patch("app.api.v1.orders.get_order_service", return_value=svc):
            response = client.delete(f"{PREFIX}/delete/1")

        assert response.status_code == 200
        assert response.json()["id"] == 1

    def test_delete_not_found(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="order_service")
        svc.delete.side_effect = NotFoundException(
            "No order found with id 999", code="ORDER_NOT_FOUND"
        )

        with patch("app.api.v1.orders.get_order_service", return_value=svc):
            response = client.delete(f"{PREFIX}/delete/999")

        assert_error(response, 404, "ORDER_NOT_FOUND")
