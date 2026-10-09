"""Testes HTTP da rota /api/v1/user-coupons.

SEGURANÇA (regressão dos achados críticos):
  - `POST /create` era ANÔNIMO e aceitava `user_id` do corpo, permitindo a
    qualquer pessoa atribuir qualquer cupom (ex.: 100% off) à própria conta.
    Agora exige token e ignora o `user_id` do corpo — sempre vincula ao usuário
    autenticado.
  - `GET /list`, `/all`, `/user/{id}`, `/coupon/{id}` eram anônimos e liam os
    vínculos de qualquer usuário. Agora exigem administrador.
  - `GET /get/{id}` e `DELETE /delete/{id}` aceitavam `user_id` da query (valor
    do cliente) como prova de posse. Agora a posse vem do token, com admin
    podendo operar sobre qualquer vínculo.
"""
from unittest.mock import Mock, patch

import pytest
from helpers import CREATED_AT, assert_error

from app.api.exceptions import CouponNotAssignedException
from app.models.user import UserRole

PREFIX = "/api/v1/user-coupons"


def link_payload(**overrides):
    payload = {
        "id": 1,
        "user_id": 1,
        "coupon_id": 1,
        "created_at": CREATED_AT,
        "updated_at": CREATED_AT,
    }
    payload.update(overrides)
    return payload


def coupon_payload(**overrides):
    payload = {
        "id": 1,
        "code": "PROMO10",
        "product_id": None,
        "discount_type": "percentage",
        "discount_value": 10.0,
        "min_purchase": None,
        "max_discount": None,
        "valid_until": "2025-12-31T23:59:59",
        "max_uses": 100,
        "used_count": 0,
        "is_active": True,
        "created_at": CREATED_AT,
        "updated_at": CREATED_AT,
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def auth_user():
    """Usuário autenticado injetado no lugar de ``get_current_user``."""
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


class TestCreateUserCoupon:
    def test_vincula_ao_proprio_usuario_do_token(self, client, auth_user):
        """O `user_id` do corpo é IGNORADO: o alvo é sempre o do token."""
        auth_user(7, role="customer")
        svc = Mock(name="user_coupon_service")
        svc.create_for_user.return_value = link_payload(user_id=7)

        with patch(
            "app.api.v1.user_coupons.get_user_coupon_service", return_value=svc
        ):
            response = client.post(
                f"{PREFIX}/create", json={"user_id": 999, "coupon_id": 1}
            )

        assert response.status_code == 201
        # Alvo é o usuário autenticado (7), não o 999 enviado no corpo.
        svc.create_for_user.assert_called_once_with(7, 1)

    def test_sem_token_retorna_401(self, client):
        response = client.post(
            f"{PREFIX}/create", json={"user_id": 1, "coupon_id": 1}
        )
        assert response.status_code == 401


class TestAdminAssign:
    """Rota administrativa de atribuição a terceiros."""

    def test_admin_atribui_a_terceiro(self, client, auth_user):
        auth_user(1, role="admin")
        svc = Mock(name="user_coupon_service")
        svc.admin_assign.return_value = link_payload(user_id=42)

        with patch(
            "app.api.v1.user_coupons.get_user_coupon_service", return_value=svc
        ):
            response = client.post(
                f"{PREFIX}/admin/assign", json={"user_id": 42, "coupon_id": 1}
            )

        assert response.status_code == 201
        svc.admin_assign.assert_called_once_with(42, 1)

    def test_cliente_nao_atribui_a_terceiro(self, client, auth_user):
        auth_user(1, role="customer")
        with patch("app.api.v1.user_coupons.get_user_coupon_service") as factory:
            response = client.post(
                f"{PREFIX}/admin/assign", json={"user_id": 42, "coupon_id": 1}
            )

        assert_error(response, 403)
        factory.return_value.admin_assign.assert_not_called()

    def test_sem_token_401(self, client):
        response = client.post(
            f"{PREFIX}/admin/assign", json={"user_id": 42, "coupon_id": 1}
        )
        assert response.status_code == 401


class TestListMyCoupons:
    def test_my_coupons_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="user_coupon_service")
        svc.list_coupons_by_user.return_value = [coupon_payload()]

        with patch(
            "app.api.v1.user_coupons.get_user_coupon_service", return_value=svc
        ):
            response = client.get(f"{PREFIX}/my")

        assert response.status_code == 200
        assert response.json()[0]["code"] == "PROMO10"
        svc.list_coupons_by_user.assert_called_once_with(1)

    def test_my_coupons_sem_token_401(self, client):
        response = client.get(f"{PREFIX}/my")
        assert response.status_code == 401


class TestRotasAdmin:
    """Listagens globais exigem administrador."""

    def test_list_sem_token_401(self, client):
        response = client.get(f"{PREFIX}/list?user_id=1")
        assert response.status_code == 401

    def test_list_cliente_403(self, client, auth_user):
        auth_user(1, role="customer")
        response = client.get(f"{PREFIX}/list?user_id=1")
        assert_error(response, 403)

    def test_all_cliente_403(self, client, auth_user):
        auth_user(1, role="customer")
        response = client.get(f"{PREFIX}/all")
        assert_error(response, 403)

    def test_por_usuario_cliente_403(self, client, auth_user):
        auth_user(1, role="customer")
        response = client.get(f"{PREFIX}/user/2")
        assert_error(response, 403)

    def test_por_cupom_cliente_403(self, client, auth_user):
        auth_user(1, role="customer")
        response = client.get(f"{PREFIX}/coupon/1")
        assert_error(response, 403)

    def test_all_admin_success(self, client, auth_user):
        auth_user(1, role="admin")
        svc = Mock(name="user_coupon_service")
        svc.get_all.return_value = [link_payload()]

        with patch(
            "app.api.v1.user_coupons.get_user_coupon_service", return_value=svc
        ):
            response = client.get(f"{PREFIX}/all")

        assert response.status_code == 200
        assert len(response.json()) == 1


class TestGetUserCoupon:
    def test_dono_acessa(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="user_coupon_service")
        svc.get_for_user.return_value = link_payload(user_id=1)

        with patch(
            "app.api.v1.user_coupons.get_user_coupon_service", return_value=svc
        ):
            response = client.get(f"{PREFIX}/get/1")

        assert response.status_code == 200
        # A posse é resolvida pelo service a partir do usuário do token.
        assert svc.get_for_user.call_args.args[0] == 1
        assert svc.get_for_user.call_args.args[1].id == 1

    def test_vinculo_de_outro_usuario_403(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="user_coupon_service")
        svc.get_for_user.side_effect = CouponNotAssignedException()

        with patch(
            "app.api.v1.user_coupons.get_user_coupon_service", return_value=svc
        ):
            response = client.get(f"{PREFIX}/get/99")

        assert_error(response, 403, "COUPON_NOT_ASSIGNED")

    def test_sem_token_401(self, client):
        response = client.get(f"{PREFIX}/get/1")
        assert response.status_code == 401


class TestDeleteUserCoupon:
    def test_dono_remove(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="user_coupon_service")
        svc.delete_for_user.return_value = link_payload(user_id=1)

        with patch(
            "app.api.v1.user_coupons.get_user_coupon_service", return_value=svc
        ):
            response = client.delete(f"{PREFIX}/delete/1")

        assert response.status_code == 200
        assert svc.delete_for_user.call_args.args[0] == 1

    def test_vinculo_de_outro_usuario_403(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="user_coupon_service")
        svc.delete_for_user.side_effect = CouponNotAssignedException()

        with patch(
            "app.api.v1.user_coupons.get_user_coupon_service", return_value=svc
        ):
            response = client.delete(f"{PREFIX}/delete/99")

        assert_error(response, 403, "COUPON_NOT_ASSIGNED")

    def test_sem_token_401(self, client):
        response = client.delete(f"{PREFIX}/delete/1")
        assert response.status_code == 401
