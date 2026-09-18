"""Testes HTTP da rota /api/v1/users.

Sucesso: 201/200 com payloads válidos.
Erros: validação 422, e-mail duplicado 409, usuário inexistente 404 e
senha atual incorreta 400.

ATENÇÃO (schema): o endpoint aceita ``AdminUserCreate | CustomerUserCreate``.
Como o payload sem ``role`` valida primeiro como ``AdminUserCreate`` (default
admin), um POST sem ``role`` cria um usuário ADMIN — ver RELATORIO_TESTES_HTTP.md.
"""
from unittest.mock import Mock, patch

from helpers import assert_error, assert_validation_error, user_payload

from app.api.exceptions import (
    BadRequestException,
    EmailAlreadyExistsException,
    UserNotFoundException,
)
from app.models.user import UserRole

PREFIX = "/api/v1/users"

CREATE_OK = {
    "email": "user@example.com",
    "full_name": "John Doe",
    "password": "secret123",
}


class TestCreateUser:
    def test_create_customer_success(self, client):
        svc = Mock(name="user_service")
        svc.create.return_value = user_payload(role="customer")

        with patch("app.api.v1.users.get_user_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json={**CREATE_OK, "role": "customer"})

        assert response.status_code == 201
        body = response.json()
        assert body["email"] == "user@example.com"
        assert body["role"] == "customer"

    def test_create_admin_success(self, client):
        svc = Mock(name="user_service")
        svc.create.return_value = user_payload(role="admin")

        with patch("app.api.v1.users.get_user_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json={**CREATE_OK, "role": "admin"})

        assert response.status_code == 201
        assert response.json()["role"] == "admin"

    def test_create_without_role_defaults_to_admin(self, client):
        """Documenta o comportamento atual do schema (problema de segurança).

        O payload sem ``role`` é validado como ``AdminUserCreate`` (primeiro da
        união), portanto o usuário criado é ADMIN por padrão.
        """
        svc = Mock(name="user_service")
        svc.create.return_value = user_payload(role="admin")

        with patch("app.api.v1.users.get_user_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert response.status_code == 201
        data = svc.create.call_args[0][0]
        assert data.role == UserRole.ADMIN

    def test_create_email_already_exists(self, client):
        svc = Mock(name="user_service")
        svc.create.side_effect = EmailAlreadyExistsException()

        with patch("app.api.v1.users.get_user_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert_error(response, 409, "EMAIL_ALREADY_EXISTS")

    def test_create_invalid_email(self, client):
        response = client.post(f"{PREFIX}/create", json={**CREATE_OK, "email": "x"})
        assert_validation_error(response)

    def test_create_short_password(self, client):
        response = client.post(f"{PREFIX}/create", json={**CREATE_OK, "password": "abc"})
        assert_validation_error(response)

    def test_create_password_without_letter(self, client):
        response = client.post(f"{PREFIX}/create", json={**CREATE_OK, "password": "12345678"})
        assert_validation_error(response)

    def test_create_invalid_role(self, client):
        response = client.post(f"{PREFIX}/create", json={**CREATE_OK, "role": "root"})
        assert_validation_error(response)

    def test_create_missing_fields(self, client):
        response = client.post(f"{PREFIX}/create", json={})
        assert_validation_error(response)


class TestGetUser:
    def test_get_by_id_success(self, client):
        svc = Mock(name="user_service")
        svc.get_by_id.return_value = user_payload()

        with patch("app.api.v1.users.get_user_service", return_value=svc):
            response = client.get(f"{PREFIX}/user_id/1")

        assert response.status_code == 200
        assert response.json()["id"] == 1

    def test_get_by_id_not_found(self, client):
        svc = Mock(name="user_service")
        svc.get_by_id.side_effect = UserNotFoundException(user_id=999)

        with patch("app.api.v1.users.get_user_service", return_value=svc):
            response = client.get(f"{PREFIX}/user_id/999")

        assert_error(response, 404, "USER_NOT_FOUND")

    def test_get_by_email_success(self, client):
        svc = Mock(name="user_service")
        svc.get_by_email.return_value = user_payload()

        with patch("app.api.v1.users.get_user_service", return_value=svc):
            response = client.get(f"{PREFIX}/email/user@example.com")

        assert response.status_code == 200
        assert response.json()["email"] == "user@example.com"

    def test_get_by_email_not_found(self, client):
        svc = Mock(name="user_service")
        svc.get_by_email.side_effect = UserNotFoundException(user_id="nobody@example.com")

        with patch("app.api.v1.users.get_user_service", return_value=svc):
            response = client.get(f"{PREFIX}/email/nobody@example.com")

        assert_error(response, 404, "USER_NOT_FOUND")


class TestUpdateUser:
    def test_update_success(self, client):
        svc = Mock(name="user_service")
        svc.update.return_value = user_payload(full_name="Jane Doe")

        with patch("app.api.v1.users.get_user_service", return_value=svc):
            response = client.patch(f"{PREFIX}/update/1", json={"full_name": "Jane Doe"})

        assert response.status_code == 200
        assert response.json()["full_name"] == "Jane Doe"

    def test_update_not_found(self, client):
        svc = Mock(name="user_service")
        svc.update.side_effect = UserNotFoundException(user_id=999)

        with patch("app.api.v1.users.get_user_service", return_value=svc):
            response = client.patch(f"{PREFIX}/update/999", json={"full_name": "Jane Doe"})

        assert_error(response, 404, "USER_NOT_FOUND")

    def test_update_email_conflict(self, client):
        svc = Mock(name="user_service")
        svc.update.side_effect = EmailAlreadyExistsException()

        with patch("app.api.v1.users.get_user_service", return_value=svc):
            response = client.patch(
                f"{PREFIX}/update/1", json={"email": "taken@example.com"}
            )

        assert_error(response, 409, "EMAIL_ALREADY_EXISTS")

    def test_update_invalid_password(self, client):
        response = client.patch(f"{PREFIX}/update/1", json={"password": "abc"})
        assert_validation_error(response)


class TestChangePassword:
    def test_change_password_success(self, client):
        svc = Mock(name="user_service")
        svc.change_password.return_value = {"message": "Senha alterada com sucesso."}

        with patch("app.api.v1.users.get_user_service", return_value=svc):
            response = client.post(
                f"{PREFIX}/change_password/1/change-password",
                json={"current_password": "secret123", "new_password": "novaSenha123"},
            )

        assert response.status_code == 200
        assert response.json()["message"] == "Senha alterada com sucesso."

    def test_change_password_wrong_current(self, client):
        svc = Mock(name="user_service")
        svc.change_password.side_effect = BadRequestException(
            "A senha atual informada está incorreta.", code="INVALID_CURRENT_PASSWORD"
        )

        with patch("app.api.v1.users.get_user_service", return_value=svc):
            response = client.post(
                f"{PREFIX}/change_password/1/change-password",
                json={"current_password": "errada123", "new_password": "novaSenha123"},
            )

        assert_error(response, 400, "INVALID_CURRENT_PASSWORD")

    def test_change_password_user_not_found(self, client):
        svc = Mock(name="user_service")
        svc.change_password.side_effect = UserNotFoundException(user_id=999)

        with patch("app.api.v1.users.get_user_service", return_value=svc):
            response = client.post(
                f"{PREFIX}/change_password/999/change-password",
                json={"current_password": "secret123", "new_password": "novaSenha123"},
            )

        assert_error(response, 404, "USER_NOT_FOUND")

    def test_change_password_short_new_password(self, client):
        response = client.post(
            f"{PREFIX}/change_password/1/change-password",
            json={"current_password": "secret123", "new_password": "abc"},
        )
        assert_validation_error(response)


class TestDeactivateUser:
    def test_deactivate_success(self, client):
        svc = Mock(name="user_service")
        svc.deactivate.return_value = user_payload(is_active=False)

        with patch("app.api.v1.users.get_user_service", return_value=svc):
            response = client.delete(f"{PREFIX}/delete/1")

        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_deactivate_not_found(self, client):
        svc = Mock(name="user_service")
        svc.deactivate.side_effect = UserNotFoundException(user_id=999)

        with patch("app.api.v1.users.get_user_service", return_value=svc):
            response = client.delete(f"{PREFIX}/delete/999")

        assert_error(response, 404, "USER_NOT_FOUND")
