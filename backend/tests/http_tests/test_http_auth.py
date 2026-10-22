from unittest.mock import Mock, patch

from helpers import assert_error, assert_validation_error, auth_user_payload

from app.api.exceptions import (
    AccountLockedException,
    InactiveUserException,
    InvalidCredentialsException,
    InvalidTokenException,
    UserNotFoundException,
)
from app.schemas.auth import TokenResponse

PREFIX = "/api/v1/auth"

REGISTER_OK = {
    "email": "user@example.com",
    "full_name": "John Doe",
    "password": "secret123",
}


class TestRegister:
    def test_register_success(self, client):
        from app.schemas.auth import MessageResponse

        svc = Mock(name="auth_service")
        svc.register.return_value = MessageResponse(message="Cadastro realizado com sucesso.")

        with patch("app.api.v1.auth.get_auth_service", return_value=svc):
            response = client.post(f"{PREFIX}/register", json=REGISTER_OK)

        assert response.status_code == 201
        assert response.json()["message"] == "Cadastro realizado com sucesso."

    def test_register_email_already_exists_is_generic(self, client):
        """P1-2: e-mail já existente responde o mesmo 201 genérico (anti-enumeração)."""
        from app.schemas.auth import MessageResponse

        svc = Mock(name="auth_service")
        svc.register.return_value = MessageResponse(message="Cadastro realizado com sucesso.")

        with patch("app.api.v1.auth.get_auth_service", return_value=svc):
            response = client.post(f"{PREFIX}/register", json=REGISTER_OK)

        assert response.status_code == 201
        assert response.json()["message"] == "Cadastro realizado com sucesso."
        assert "EMAIL_ALREADY_EXISTS" not in response.text
        assert "error" not in response.json()

    def test_register_invalid_email(self, client):
        payload = {**REGISTER_OK, "email": "not-an-email"}
        response = client.post(f"{PREFIX}/register", json=payload)
        assert_validation_error(response)

    def test_register_short_password(self, client):
        payload = {**REGISTER_OK, "password": "123"}
        response = client.post(f"{PREFIX}/register", json=payload)
        assert_validation_error(response)

    def test_register_password_without_letter(self, client):
        payload = {**REGISTER_OK, "password": "12345678"}
        response = client.post(f"{PREFIX}/register", json=payload)
        assert_validation_error(response)

    def test_register_password_without_number(self, client):
        payload = {**REGISTER_OK, "password": "abcdefgh"}
        response = client.post(f"{PREFIX}/register", json=payload)
        assert_validation_error(response)

    def test_register_short_full_name(self, client):
        payload = {**REGISTER_OK, "full_name": "Jo"}
        response = client.post(f"{PREFIX}/register", json=payload)
        assert_validation_error(response)

    def test_register_missing_fields(self, client):
        response = client.post(f"{PREFIX}/register", json={})
        assert_validation_error(response)

    def test_register_empty_body(self, client):
        response = client.post(f"{PREFIX}/register", json=None)
        assert_validation_error(response)


class TestLogin:

    LOGIN_OK = {"username": "user@example.com", "password": "secret123"}

    @staticmethod
    def _enviar(client, svc, form=None):
        with patch("app.api.v1.auth.get_auth_service", return_value=svc):
            return client.post(f"{PREFIX}/login", data=form or TestLogin.LOGIN_OK)

    def test_login_success(self, client):
        svc = Mock(name="auth_service")
        svc.login.return_value = TokenResponse(
            access_token="jwt-token",
            refresh_token="refresh-token",
        )

        response = self._enviar(client, svc)

        assert response.status_code == 200
        body = response.json()
        assert body["access_token"] == "jwt-token"
        assert body["token_type"] == "bearer"
        assert body["refresh_token"] == "refresh-token"
        # O refresh token também vai num cookie httpOnly papiro_refresh.
        assert response.cookies["papiro_refresh"] == "refresh-token"

    def test_login_invalid_credentials(self, client):
        svc = Mock(name="auth_service")
        svc.login.side_effect = InvalidCredentialsException()

        response = self._enviar(client, svc)

        assert_error(response, 401, "INVALID_CREDENTIALS")

    def test_login_inactive_user(self, client):
        svc = Mock(name="auth_service")
        svc.login.side_effect = InactiveUserException()

        response = self._enviar(client, svc)

        assert_error(response, 403, "INACTIVE_USER")

    def test_login_account_locked_returns_429_with_retry_after(self, client):
        """P1-5: conta bloqueada -> 429 com Retry-After (e código ACCOUNT_LOCKED)."""
        svc = Mock(name="auth_service")
        svc.login.side_effect = AccountLockedException(retry_after=120)

        response = self._enviar(client, svc)

        assert_error(response, 429, "ACCOUNT_LOCKED")
        assert response.headers.get("Retry-After") == "120"

    def test_login_missing_username(self, client):
        response = client.post(f"{PREFIX}/login", data={"password": "secret123"})
        assert_validation_error(response)

    def test_login_missing_password(self, client):
        response = client.post(
            f"{PREFIX}/login", data={"username": "user@example.com"}
        )
        assert_validation_error(response)


class TestMe:
    def _override_current_user(self, user):
        from app.api.deps import get_current_user
        from app.main import app

        app.dependency_overrides[get_current_user] = lambda: user

    def _fake_user(self):
        fake_user = Mock(name="user")
        fake_user.db = Mock(name="db")
        fake_user.id = 1
        fake_user.email = "user@example.com"
        fake_user.full_name = "John Doe"
        fake_user.role = "customer"
        fake_user.is_active = True
        fake_user.created_at = "2024-01-01T12:00:00"
        return fake_user

    def test_me_success(self, client):
        self._override_current_user(self._fake_user())

        svc = Mock(name="auth_service")
        svc.me.return_value = auth_user_payload()

        with patch("app.api.v1.auth.get_auth_service", return_value=svc):
            response = client.get(f"{PREFIX}/me")

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == 1
        assert body["email"] == "user@example.com"

    def test_me_user_not_found(self, client):
        self._override_current_user(self._fake_user())

        svc = Mock(name="auth_service")
        svc.me.side_effect = UserNotFoundException(user_id=1)

        with patch("app.api.v1.auth.get_auth_service", return_value=svc):
            response = client.get(f"{PREFIX}/me")

        assert_error(response, 404, "USER_NOT_FOUND")


class TestRefresh:


    @staticmethod
    def _fresh_response():
        return TokenResponse(access_token="new-access", refresh_token="new-refresh")

    def test_refresh_success_via_cookie(self, client):
        svc = Mock(name="auth_service")
        svc.refresh.return_value = self._fresh_response()

        client.cookies.set("papiro_refresh", "old-refresh-token")

        with patch("app.api.v1.auth.get_auth_service", return_value=svc):
            response = client.post(f"{PREFIX}/refresh")

        assert response.status_code == 200
        body = response.json()
        assert body["access_token"] == "new-access"
        # NFC: o body do refresh não devolve refresh_token (trocado no cookie).
        assert "refresh_token" not in body
        svc.refresh.assert_called_once_with("old-refresh-token")
        assert response.cookies["papiro_refresh"] == "new-refresh"

    def test_refresh_success_via_body(self, client):
        svc = Mock(name="auth_service")
        svc.refresh.return_value = self._fresh_response()

        with patch("app.api.v1.auth.get_auth_service", return_value=svc):
            response = client.post(
                f"{PREFIX}/refresh", json={"refresh_token": "body-refresh"}
            )

        assert response.status_code == 200
        svc.refresh.assert_called_once_with("body-refresh")

    def test_refresh_rejects_invalid_token(self, client):
        svc = Mock(name="auth_service")
        svc.refresh.side_effect = InvalidTokenException()

        client.cookies.set("papiro_refresh", "bad-refresh")

        with patch("app.api.v1.auth.get_auth_service", return_value=svc):
            response = client.post(f"{PREFIX}/refresh")

        assert_error(response, 401, "INVALID_TOKEN")


class TestLogout:


    def test_logout_clears_cookie(self, client):
        svc = Mock(name="auth_service")
        client.cookies.set("papiro_refresh", "refresh-to-remove")

        with patch("app.api.v1.auth.get_auth_service", return_value=svc):
            response = client.post(f"{PREFIX}/logout")

        assert response.status_code == 200
        body = response.json()
        assert body["message"] == "Sessão encerrada."
        svc.logout.assert_called_once()
