"""Testes HTTP da rota /api/v1/coupons.

Sucesso: 201/200 com payloads válidos (criação, listagem e update/delete).
Erros: validação 422, cupom/produto inexistente 404 e código duplicado 409.

SEGURANÇA: cupons são catálogo administrativo. Todo o router exige Bearer token
de **administrador** — 401 sem token, 403 com papel ``customer``. Antes o router
era totalmente anônimo e permitia emitir cupons de desconto arbitrário.

NOTA: o CouponService real lança ``ValueError`` em vez das exceções de domínio
— em produção esses erros viram 500. Ver RELATORIO_TESTES_HTTP.md.
"""
from unittest.mock import Mock, patch

import pytest
from helpers import assert_error, assert_validation_error, coupon_payload

from app.api.exceptions import (
    ConflictException,
    NotFoundException,
    ProductNotFoundException,
)
from app.models.user import UserRole

PREFIX = "/api/v1/coupons"

CREATE_OK = {
    "code": "PROMO10",
    "discount_type": "percentage",
    "discount_value": 10.0,
    "valid_until": "2025-12-31T23:59:59",
}


@pytest.fixture
def auth_user():
    """Usuário autenticado injetado no lugar de ``get_current_user``.

    Mesmo padrão de test_http_products.py / test_http_categories.py.
    """
    from app.api.deps import get_current_user
    from app.main import app

    def _set(user_id: int = 1, role: str = "customer"):
        user = Mock(name="user")
        user.id = user_id
        user.role = UserRole(role)
        app.dependency_overrides[get_current_user] = lambda: user
        return user

    yield _set
    app.dependency_overrides.pop(get_current_user, None)


class TestCreateCoupon:
    def test_create_success(self, client, auth_user):
        auth_user(1, role="admin")
        svc = Mock(name="coupon_service")
        svc.create.return_value = coupon_payload()

        with patch("app.api.v1.coupons.get_coupon_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert response.status_code == 201
        body = response.json()
        assert body["code"] == "PROMO10"
        assert body["discount_type"] == "percentage"
        assert body["discount_value"] == 10.0

    def test_create_requires_auth(self, client):
        """Sem Bearer token a rota nem chega ao service (fecha o acesso anônimo)."""
        response = client.post(f"{PREFIX}/create", json=CREATE_OK)
        assert response.status_code == 401

    def test_create_customer_forbidden(self, client, auth_user):
        """Cliente autenticado não pode emitir cupons."""
        auth_user(1, role="customer")
        svc = Mock(name="coupon_service")

        with patch("app.api.v1.coupons.get_coupon_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert response.status_code == 403
        svc.create.assert_not_called()

    def test_create_duplicate_code(self, client, auth_user):
        auth_user(1, role="admin")
        svc = Mock(name="coupon_service")
        svc.create.side_effect = ConflictException(
            "Coupon with code 'PROMO10' already exists", code="DUPLICATE_COUPON"
        )

        with patch("app.api.v1.coupons.get_coupon_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert_error(response, 409, "DUPLICATE_COUPON")

    def test_create_product_not_found(self, client, auth_user):
        auth_user(1, role="admin")
        svc = Mock(name="coupon_service")
        svc.create.side_effect = ProductNotFoundException()

        with patch("app.api.v1.coupons.get_coupon_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json={**CREATE_OK, "product_id": 999})

        assert_error(response, 404, "PRODUCT_NOT_FOUND")

    def test_create_short_code(self, client, auth_user):
        auth_user(1, role="admin")
        response = client.post(f"{PREFIX}/create", json={**CREATE_OK, "code": "ab"})
        assert_validation_error(response)

    def test_create_negative_discount_value(self, client, auth_user):
        auth_user(1, role="admin")
        response = client.post(f"{PREFIX}/create", json={**CREATE_OK, "discount_value": -5})
        assert_validation_error(response)

    def test_create_invalid_discount_type(self, client, auth_user):
        auth_user(1, role="admin")
        response = client.post(f"{PREFIX}/create", json={**CREATE_OK, "discount_type": "total"})
        assert_validation_error(response)

    def test_create_missing_valid_until(self, client, auth_user):
        auth_user(1, role="admin")
        payload = {k: v for k, v in CREATE_OK.items() if k != "valid_until"}
        response = client.post(f"{PREFIX}/create", json=payload)
        assert_validation_error(response)


class TestListCoupons:
    def test_list_success(self, client, auth_user):
        auth_user(1, role="admin")
        svc = Mock(name="coupon_service")
        svc.get_all.return_value = [coupon_payload(), coupon_payload(id=2, code="PROMO20")]

        with patch("app.api.v1.coupons.get_coupon_service", return_value=svc):
            response = client.get(f"{PREFIX}/list")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_requires_auth(self, client):
        response = client.get(f"{PREFIX}/list")
        assert response.status_code == 401


class TestUpdateCoupon:
    def test_update_success(self, client, auth_user):
        auth_user(1, role="admin")
        svc = Mock(name="coupon_service")
        svc.update.return_value = coupon_payload(discount_value=15.0)

        with patch("app.api.v1.coupons.get_coupon_service", return_value=svc):
            response = client.patch(f"{PREFIX}/update/1", json={"discount_value": 15.0})

        assert response.status_code == 200
        assert response.json()["discount_value"] == 15.0

    def test_update_requires_auth(self, client):
        response = client.patch(f"{PREFIX}/update/1", json={"discount_value": 15.0})
        assert response.status_code == 401

    def test_update_invalid_discount_value(self, client, auth_user):
        auth_user(1, role="admin")
        response = client.patch(f"{PREFIX}/update/1", json={"discount_value": -1})
        assert_validation_error(response)

    def test_update_short_code(self, client, auth_user):
        auth_user(1, role="admin")
        response = client.patch(f"{PREFIX}/update/1", json={"code": "ab"})
        assert_validation_error(response)


class TestDeleteCoupon:
    def test_delete_success(self, client, auth_user):
        auth_user(1, role="admin")
        svc = Mock(name="coupon_service")
        svc.delete.return_value = coupon_payload()

        with patch("app.api.v1.coupons.get_coupon_service", return_value=svc):
            response = client.delete(f"{PREFIX}/delete/1")

        assert response.status_code == 200
        assert response.json()["id"] == 1

    def test_delete_requires_auth(self, client):
        response = client.delete(f"{PREFIX}/delete/1")
        assert response.status_code == 401

    def test_delete_not_found(self, client, auth_user):
        auth_user(1, role="admin")
        svc = Mock(name="coupon_service")
        svc.delete.side_effect = NotFoundException(
            "No coupon found with id 999", code="COUPON_NOT_FOUND"
        )

        with patch("app.api.v1.coupons.get_coupon_service", return_value=svc):
            response = client.delete(f"{PREFIX}/delete/999")

        assert_error(response, 404, "COUPON_NOT_FOUND")
