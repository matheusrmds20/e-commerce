"""Testes HTTP da rota /api/v1/admin (área administrativa).

SEGURANÇA: é o teste de regressão do achado CRÍTICO — o router `/admin` não
tinha NENHUMA autenticação, expondo faturamento, pedidos de todos os clientes
(nome/e-mail), PII de usuários e permitindo alterar o status de qualquer
pedido por um anônimo. Agora:

  - 401 sem Bearer token;
  - 403 com token de ``customer``;
  - 200 com token de ``admin``.

A checagem vive em ``app.api.deps.get_current_admin``, aplicada no router.
"""
from unittest.mock import Mock, patch

import pytest
from helpers import assert_error

from app.models.user import UserRole

PREFIX = "/api/v1/admin"

STATS_OK = {
    "total_revenue": 1000.0,
    "total_orders": 10,
    "pending_orders": 2,
    "total_products": 5,
    "total_stock": 40,
    "average_ticket": 100.0,
    "low_stock_products": [],
    "weekly_sales": [],
}

ORDER_OK = {
    "id": 1,
    "user_id": 1,
    "user": {"id": 1, "full_name": "John Doe", "email": "user@example.com"},
    "status": "pending",
    "subtotal": 119.8,
    "discount_amount": 0.0,
    "shipping_cost": 0.0,
    "total": 119.8,
    "notes": None,
    "items_count": 1,
    "items_summary": "Livro (x1)",
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-02T12:00:00",
}

USER_OK = {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "customer",
    "is_active": True,
    "orders_count": 3,
    "created_at": "2024-01-01T12:00:00",
}


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


@pytest.fixture
def admin_router_enabled():
    """Garante que o router admin do app real esteja montado para estes testes."""

    def _stub_service(**methods):
        svc = Mock(name="admin_service")
        for name, value in methods.items():
            getattr(svc, name).return_value = value
        return svc

    return _stub_service


PUBLICAS = [
    ("get", f"{PREFIX}/dashboard/stats"),
    ("get", f"{PREFIX}/orders"),
    ("get", f"{PREFIX}/users"),
]


class TestAdminRouterRequerAuth:
    """Sem token, nenhuma rota administrativa responde (era o bug crítico)."""

    @pytest.mark.parametrize("method,url", PUBLICAS)
    def test_sem_token_retorna_401(self, client, method, url):
        response = getattr(client, method)(url)
        assert response.status_code == 401

    def test_patch_status_sem_token_retorna_401(self, client):
        response = client.patch(
            f"{PREFIX}/orders/1/status", json={"status": "delivered"}
        )
        assert response.status_code == 401


class TestAdminRouterRequerPapelAdmin:
    """Token de cliente comum deve ser recusado com 403."""

    @pytest.mark.parametrize("method,url", PUBLICAS)
    def test_cliente_recebe_403(self, client, auth_user, method, url):
        auth_user(1, role="customer")
        response = getattr(client, method)(url)
        assert_error(response, 403)

    def test_cliente_nao_altera_status_de_pedido(self, client, auth_user):
        auth_user(1, role="customer")
        with patch("app.api.v1.admin.get_admin_service") as factory:
            response = client.patch(
                f"{PREFIX}/orders/1/status", json={"status": "delivered"}
            )

        assert_error(response, 403)
        factory.return_value.update_order_status.assert_not_called()


class TestAdminDashboard:
    def test_stats_success(self, client, auth_user, admin_router_enabled):
        auth_user(1, role="admin")
        svc = admin_router_enabled(get_dashboard_stats=STATS_OK)

        with patch("app.api.v1.admin.get_admin_service", return_value=svc):
            response = client.get(f"{PREFIX}/dashboard/stats")

        assert response.status_code == 200
        assert response.json()["total_revenue"] == 1000.0
        assert response.json()["total_orders"] == 10


class TestAdminOrders:
    def test_list_orders_success(self, client, auth_user, admin_router_enabled):
        auth_user(1, role="admin")
        svc = admin_router_enabled(list_all_orders=[ORDER_OK])

        with patch("app.api.v1.admin.get_admin_service", return_value=svc):
            response = client.get(f"{PREFIX}/orders")

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["user"]["email"] == "user@example.com"

    def test_update_status_success(self, client, auth_user, admin_router_enabled):
        auth_user(1, role="admin")
        svc = admin_router_enabled(
            update_order_status={**ORDER_OK, "status": "delivered"}
        )

        with patch("app.api.v1.admin.get_admin_service", return_value=svc):
            response = client.patch(
                f"{PREFIX}/orders/1/status", json={"status": "delivered"}
            )

        assert response.status_code == 200
        assert response.json()["status"] == "delivered"


class TestAdminUsers:
    def test_list_users_success(self, client, auth_user, admin_router_enabled):
        auth_user(1, role="admin")
        svc = admin_router_enabled(list_users=[USER_OK])

        with patch("app.api.v1.admin.get_admin_service", return_value=svc):
            response = client.get(f"{PREFIX}/users")

        assert response.status_code == 200
        assert response.json()[0]["email"] == "user@example.com"
