"""Testes HTTP dos endpoints de e-mail de confirmação de pedido.

Cobre:
- ``POST /api/v1/orders/send-confirmation-email`` (disparo manual)
- ``GET /api/v1/orders/send-confirmation-email/status/{task_id}`` (consulta)

O ``OrderService`` é mockado na factory da rota (``get_order_service``);
nenhum Redis/broker real é usado — ``use_scaler``.
"""
from unittest.mock import AsyncMock, Mock, patch

import pytest

PREFIX = "/api/v1/orders"


@pytest.fixture
def auth_user():
    """Usuário autenticado injetado no lugar de ``get_current_user``."""
    from app.api.deps import get_current_user
    from app.main import app

    def _definir(user_id: int = 1):
        user = Mock(name="user")
        user.id = user_id
        user.email = "user@example.com"
        user.is_active = True
        app.dependency_overrides[get_current_user] = lambda: user
        return user

    yield _definir
    app.dependency_overrides.pop(get_current_user, None)


class TestSendConfirmationEmail:
    def test_require_auth(self, client):
        response = client.post(f"{PREFIX}/send-confirmation-email?order_id=10")
        assert response.status_code == 401

    def test_success(self, client, auth_user):
        user = auth_user(1)
        svc = Mock(name="order_service")
        svc.send_confirmation_email.return_value = {
            "status": "success",
            "sended": "task_abc123",
        }

        with patch("app.api.v1.orders.get_order_service", return_value=svc):
            response = client.post(f"{PREFIX}/send-confirmation-email?order_id=10")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["sended"] == "task_abc123"
        svc.send_confirmation_email.assert_called_once_with(10, user)


class TestGetTaskStatus:
    def test_require_auth(self, client):
        """SEGURANÇA: o status de tarefa não é mais público."""
        response = client.get(
            f"{PREFIX}/send-confirmation-email/status/task_abc"
        )
        assert response.status_code == 401

    def test_returns_status(self, client, auth_user):
        """Endpoint exige Bearer token (a tarefa vaza dados do pedido)."""
        auth_user(1)
        svc = AsyncMock(name="order_service")
        svc.get_task_status.return_value = {
            "task_id": "task_abc",
            "status": "SUCCESS",
            "result": {"status": "success", "order_id": 10},
        }

        with patch("app.api.v1.orders.get_order_service", return_value=svc):
            response = client.get(
                f"{PREFIX}/send-confirmation-email/status/task_abc"
            )

        assert response.status_code == 200
        body = response.json()
        assert body["task_id"] == "task_abc"
        assert body["status"] == "SUCCESS"
        assert body["result"]["order_id"] == 10
