"""Testes HTTP da rota /api/v1/newsletter.

Sucesso: 201/200 com payloads válidos (subscribe público, unsubscribe
público, listagem de inscritos [admin]).
Erros: validação 422 (e-mail inválido), e-mail duplicado 409,
inscrito inexistente 404 e listagem sem permissão 403.

NOTA: subscribe/unsubscribe são PÚBLICOS (sem token). A listagem exige
token e papel de administrador (``get_current_user``), mesmo padrão de
test_http_users.py: sobrescreve a dependência e devolve um objeto com
``id``/``role``.
"""
from unittest.mock import Mock

import pytest
from helpers import assert_error, assert_validation_error

from app.models.user import UserRole

PREFIX = "/api/v1/newsletter"

SUBSCRIBE_OK = {"email": "reader@example.com"}


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


def subscriber_payload(**overrides):
    payload = {
        "id": 1,
        "email": "reader@example.com",
        "subscribed_at": "2026-01-01T12:00:00",
    }
    payload.update(overrides)
    return payload


class TestSubscribe:
    def test_subscribe_success(self, client, patch_service):
        svc = Mock(name="newsletter_service")
        svc.subscribe.return_value = subscriber_payload()

        with patch_service("newsletter", "get_newsletter_service", svc):
            resp = client.post(f"{PREFIX}/subscribe", json=SUBSCRIBE_OK)

        assert resp.status_code == 201
        assert resp.json() == subscriber_payload()

    def test_subscribe_duplicate(self, client, patch_service):
        svc = Mock(name="newsletter_service")
        svc.subscribe.side_effect = ValueError("Email x@y.com is already subscribed")

        with patch_service("newsletter", "get_newsletter_service", svc):
            resp = client.post(f"{PREFIX}/subscribe", json=SUBSCRIBE_OK)

        assert_error(resp, 409, code="NEWSLETTER_ALREADY_SUBSCRIBED")

    def test_subscribe_invalid_email(self, client, patch_service):
        svc = Mock(name="newsletter_service")

        with patch_service("newsletter", "get_newsletter_service", svc):
            resp = client.post(f"{PREFIX}/subscribe", json={"email": "invalid"})

        assert_validation_error(resp)
        svc.subscribe.assert_not_called()


class TestUnsubscribe:
    def test_unsubscribe_success(self, client, patch_service):
        svc = Mock(name="newsletter_service")
        svc.unsubscribe.return_value = subscriber_payload()

        with patch_service("newsletter", "get_newsletter_service", svc):
            resp = client.post(f"{PREFIX}/unsubscribe", json=SUBSCRIBE_OK)

        assert resp.status_code == 200
        assert "message" in resp.json()

    def test_unsubscribe_not_found(self, client, patch_service):
        svc = Mock(name="newsletter_service")
        svc.unsubscribe.side_effect = ValueError("No subscriber found with email x@y.com")

        with patch_service("newsletter", "get_newsletter_service", svc):
            resp = client.post(f"{PREFIX}/unsubscribe", json=SUBSCRIBE_OK)

        assert_error(resp, 404, code="NEWSLETTER_SUBSCRIBER_NOT_FOUND")


class TestListSubscribers:
    def test_list_success_admin(self, client, patch_service, auth_user):
        auth_user(99, role="admin")
        svc = Mock(name="newsletter_service")
        svc.list_all.return_value = [subscriber_payload()]

        with patch_service("newsletter", "get_newsletter_service", svc):
            resp = client.get(f"{PREFIX}/list")

        assert resp.status_code == 200
        assert resp.json() == [subscriber_payload()]

    def test_list_forbidden_customer(self, client, patch_service, auth_user):
        auth_user(1)
        svc = Mock(name="newsletter_service")
        svc.list_all.side_effect = ValueError("Admin permission required to list subscribers")

        with patch_service("newsletter", "get_newsletter_service", svc):
            resp = client.get(f"{PREFIX}/list")

        assert_error(resp, 403)

    def test_list_requires_token(self, client, patch_service):
        svc = Mock(name="newsletter_service")

        with patch_service("newsletter", "get_newsletter_service", svc):
            resp = client.get(f"{PREFIX}/list")

        assert resp.status_code == 401
