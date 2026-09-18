"""Testes HTTP da rota /api/v1/auth (register, login, me).

Sucesso: 201/200 com payloads válidos.
Erros: validação 422, e-mail duplicado 409, credenciais inválidas 401,
usuário inativo 403 e usuário inexistente 404.
"""
from unittest.mock import Mock, patch

from helpers import assert_error, assert_validation_error, auth_user_payload

from app.api.exceptions import (
    EmailAlreadyExistsException,
    InactiveUserException,
    InvalidCredentialsException,
    UserNotFoundException,
)

PREFIX = "/api/v1/auth"

REGISTER_OK = {
    "email": "user@example.com",
    "full_name": "John Doe",
    "password": "secret123",
}


class TestRegister:
    def test_register_success(self, client):
        svc = Mock(name="auth_service")
        svc.register.return_value = auth_user_payload()

        with patch("app.api.v1.auth.get_auth_service", return_value=svc):
            response = client.post(f"{PREFIX}/register", json=REGISTER_OK)

        assert response.status_code == 201
        body = response.json()
        assert body["id"] == 1
        assert body["email"] == "user@example.com"
        assert body["role"] == "customer"
        assert body["is_active"] is True

    def test_register_email_already_exists(self, client):
        svc = Mock(name="auth_service")
        svc.register.side_effect = EmailAlreadyExistsException()

        with patch("app.api.v1.auth.get_auth_service", return_value=svc):
            response = client.post(f"{PREFIX}/register", json=REGISTER_OK)

        assert_error(response, 409, "EMAIL_ALREADY_EXISTS")

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
    LOGIN_OK = {"email": "user@example.com", "password": "secret123"}

    def test_login_success(self, client):
        svc = Mock(name="auth_service")
        svc.login.return_value = {"access_token": "jwt-token", "token_type": "bearer"}

        with patch("app.api.v1.auth.get_auth_service", return_value=svc):
            response = client.post(f"{PREFIX}/login", json=self.LOGIN_OK)

        assert response.status_code == 200
        body = response.json()
        assert body["access_token"] == "jwt-token"
        assert body["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client):
        svc = Mock(name="auth_service")
        svc.login.side_effect = InvalidCredentialsException()

        with patch("app.api.v1.auth.get_auth_service", return_value=svc):
            response = client.post(f"{PREFIX}/login", json=self.LOGIN_OK)

        assert_error(response, 401, "INVALID_CREDENTIALS")

    def test_login_inactive_user(self, client):
        svc = Mock(name="auth_service")
        svc.login.side_effect = InactiveUserException()

        with patch("app.api.v1.auth.get_auth_service", return_value=svc):
            response = client.post(f"{PREFIX}/login", json=self.LOGIN_OK)

        assert_error(response, 403, "INACTIVE_USER")

    def test_login_invalid_email_format(self, client):
        payload = {**self.LOGIN_OK, "email": "invalid"}
        response = client.post(f"{PREFIX}/login", json=payload)
        assert_validation_error(response)

    def test_login_missing_password(self, client):
        response = client.post(f"{PREFIX}/login", json={"email": "user@example.com"})
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
