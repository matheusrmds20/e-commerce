"""Testes HTTP da rota /api/v1/addresses.

Sucesso: 201/200 com payloads válidos (criação, listagem, busca por id/CEP,
endereço padrão, update e delete).
Erros: validação 422, endereço/usuário inexistente 404, endereço de outro
usuário 403 e CEP duplicado 409.

AUTENTICAÇÃO: todas as rotas exigem Bearer token e derivam o ``user_id`` do
usuário autenticado (``Depends(get_current_user)``). O ``user_id`` NÃO é mais
aceito como query param nem no corpo do ``AddressCreate`` — fechou o IDOR de
criar/ler endereço em nome de outra pessoa. Ver test_http_cart.py para o padrão.

NOTA: o AddressService real lança ``ValueError`` em vez das exceções de domínio.
As rotas traduzem esse ``ValueError`` para 400/403/404/409.
"""
from unittest.mock import Mock, patch

import pytest
from helpers import address_payload, assert_error, assert_validation_error

from app.api.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
)

PREFIX = "/api/v1/addresses"

CREATE_OK = {
    "street": "Rua das Flores",
    "number": "100",
    "neighborhood": "Centro",
    "city": "Sao Paulo",
    "state": "SP",
    "zip_code": "01001000",
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
    """Sem token, nenhuma rota de endereço deve responder."""

    def test_create_requires_auth(self, client):
        response = client.post(f"{PREFIX}/create", json=CREATE_OK)
        assert response.status_code == 401

    def test_list_requires_auth(self, client):
        response = client.get(f"{PREFIX}/list")
        assert response.status_code == 401

    def test_get_requires_auth(self, client):
        response = client.get(f"{PREFIX}/get/1")
        assert response.status_code == 401

    def test_default_requires_auth(self, client):
        response = client.get(f"{PREFIX}/default")
        assert response.status_code == 401

    def test_update_requires_auth(self, client):
        response = client.patch(f"{PREFIX}/update/1", json={"city": "Rio"})
        assert response.status_code == 401

    def test_delete_requires_auth(self, client):
        response = client.delete(f"{PREFIX}/delete/1")
        assert response.status_code == 401

    def test_user_id_query_is_ignored(self, client, auth_user):
        """Passar user_id na query não muda quem é o dono (anti-IDOR).

        A requisição autentica pelo token; o ``user_id`` da query é ignorado.
        Aqui o token pertence ao usuário 1 e a query tenta o 999 — o service
        deve receber 1.
        """
        auth_user(1)
        svc = Mock(name="address_service")
        svc.get_by_user_id.return_value = [address_payload()]

        with patch("app.api.v1.addresses.get_address_service", return_value=svc):
            response = client.get(f"{PREFIX}/list?user_id=999")

        assert response.status_code == 200
        svc.get_by_user_id.assert_called_once_with(1)


class TestCreateAddress:
    def test_create_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="address_service")
        svc.create.return_value = address_payload()

        with patch("app.api.v1.addresses.get_address_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert response.status_code == 201
        body = response.json()
        assert body["street"] == "Rua das Flores"
        assert body["zip_code"] == "01001000"
        assert body["user_id"] == 1

    def test_create_uses_token_user_id(self, client, auth_user):
        """O ``user_id`` passado ao service é o do token, não de query/corpo."""
        auth_user(7)
        svc = Mock(name="address_service")
        svc.create.return_value = address_payload(user_id=7)

        with patch("app.api.v1.addresses.get_address_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert response.status_code == 201
        # service.create(data, user_id) — o segundo argumento vem do token.
        assert svc.create.call_args.args[1] == 7

    def test_create_duplicate_zip_code(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="address_service")
        svc.create.side_effect = ConflictException(
            "Address with zip_code 01001000 already exists",
            code="ADDRESS_ALREADY_EXISTS",
        )

        with patch("app.api.v1.addresses.get_address_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert_error(response, 409, "ADDRESS_ALREADY_EXISTS")

    def test_create_short_state(self, client, auth_user):
        auth_user(1)
        response = client.post(
            f"{PREFIX}/create", json={**CREATE_OK, "state": "S"}
        )
        assert_validation_error(response)

    def test_create_long_state(self, client, auth_user):
        auth_user(1)
        response = client.post(
            f"{PREFIX}/create", json={**CREATE_OK, "state": "SPO"}
        )
        assert_validation_error(response)

    def test_create_short_zip_code(self, client, auth_user):
        auth_user(1)
        response = client.post(
            f"{PREFIX}/create", json={**CREATE_OK, "zip_code": "123"}
        )
        assert_validation_error(response)

    def test_create_missing_street(self, client, auth_user):
        auth_user(1)
        payload = {k: v for k, v in CREATE_OK.items() if k != "street"}
        response = client.post(f"{PREFIX}/create", json=payload)
        assert_validation_error(response)

    def test_create_user_id_in_body_is_ignored(self, client, auth_user):
        """``user_id`` no corpo é apenas ignorado (não autentica nem quebra)."""
        auth_user(1)
        svc = Mock(name="address_service")
        svc.create.return_value = address_payload()

        with patch("app.api.v1.addresses.get_address_service", return_value=svc):
            response = client.post(
                f"{PREFIX}/create", json={**CREATE_OK, "user_id": 999}
            )

        assert response.status_code == 201
        assert svc.create.call_args.args[1] == 1


class TestListAddresses:
    def test_list_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="address_service")
        svc.get_by_user_id.return_value = [
            address_payload(),
            address_payload(id=2, zip_code="02002000"),
        ]

        with patch("app.api.v1.addresses.get_address_service", return_value=svc):
            response = client.get(f"{PREFIX}/list")

        assert response.status_code == 200
        assert len(response.json()) == 2
        svc.get_by_user_id.assert_called_once_with(1)

    def test_list_not_found(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="address_service")
        svc.get_by_user_id.side_effect = NotFoundException(
            "No addresses found with user_id 999", code="ADDRESS_NOT_FOUND"
        )

        with patch("app.api.v1.addresses.get_address_service", return_value=svc):
            response = client.get(f"{PREFIX}/list")

        assert_error(response, 404, "ADDRESS_NOT_FOUND")


class TestGetAddress:
    def test_get_by_id_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="address_service")
        svc.get_by_id.return_value = address_payload()

        with patch("app.api.v1.addresses.get_address_service", return_value=svc):
            response = client.get(f"{PREFIX}/get/1")

        assert response.status_code == 200
        assert response.json()["id"] == 1
        svc.get_by_id.assert_called_once_with(1, 1)

    def test_get_by_id_not_found(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="address_service")
        svc.get_by_id.side_effect = NotFoundException(
            "No address found with id 999", code="ADDRESS_NOT_FOUND"
        )

        with patch("app.api.v1.addresses.get_address_service", return_value=svc):
            response = client.get(f"{PREFIX}/get/999")

        assert_error(response, 404, "ADDRESS_NOT_FOUND")

    def test_get_by_id_ownership_forbidden(self, client, auth_user):
        auth_user(2)
        svc = Mock(name="address_service")
        svc.get_by_id.side_effect = ForbiddenException("Address is not owned by user")

        with patch("app.api.v1.addresses.get_address_service", return_value=svc):
            response = client.get(f"{PREFIX}/get/1")

        assert_error(response, 403, "FORBIDDEN")

    def test_get_default_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="address_service")
        svc.get_actual_address_default.return_value = address_payload(is_default=True)

        with patch("app.api.v1.addresses.get_address_service", return_value=svc):
            response = client.get(f"{PREFIX}/default")

        assert response.status_code == 200
        assert response.json()["is_default"] is True

    def test_get_default_not_found(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="address_service")
        svc.get_actual_address_default.side_effect = NotFoundException(
            "No default address found", code="ADDRESS_NOT_FOUND"
        )

        with patch("app.api.v1.addresses.get_address_service", return_value=svc):
            response = client.get(f"{PREFIX}/default")

        assert_error(response, 404, "ADDRESS_NOT_FOUND")

    def test_get_by_zip_code_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="address_service")
        svc.get_by_zip_code.return_value = address_payload()

        with patch("app.api.v1.addresses.get_address_service", return_value=svc):
            response = client.get(f"{PREFIX}/zip/01001000")

        assert response.status_code == 200
        assert response.json()["zip_code"] == "01001000"

    def test_get_by_zip_code_not_found(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="address_service")
        svc.get_by_zip_code.side_effect = NotFoundException(
            "No address found with zip_code 00000000", code="ADDRESS_NOT_FOUND"
        )

        with patch("app.api.v1.addresses.get_address_service", return_value=svc):
            response = client.get(f"{PREFIX}/zip/00000000")

        assert_error(response, 404, "ADDRESS_NOT_FOUND")


class TestSetDefaultAddress:
    def test_set_default_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="address_service")
        svc.set_default.return_value = address_payload(is_default=True)

        with patch("app.api.v1.addresses.get_address_service", return_value=svc):
            response = client.patch(f"{PREFIX}/default/set/1")

        assert response.status_code == 200
        assert response.json()["is_default"] is True
        svc.set_default.assert_called_once_with(1, 1)

    def test_set_default_not_found(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="address_service")
        svc.set_default.side_effect = NotFoundException(
            "No address found with id 999", code="ADDRESS_NOT_FOUND"
        )

        with patch("app.api.v1.addresses.get_address_service", return_value=svc):
            response = client.patch(f"{PREFIX}/default/set/999")

        assert_error(response, 404, "ADDRESS_NOT_FOUND")


class TestUpdateAddress:
    def test_update_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="address_service")
        svc.update.return_value = address_payload(city="Rio de Janeiro")

        with patch("app.api.v1.addresses.get_address_service", return_value=svc):
            response = client.patch(
                f"{PREFIX}/update/1", json={"city": "Rio de Janeiro"}
            )

        assert response.status_code == 200
        assert response.json()["city"] == "Rio de Janeiro"

    def test_update_not_found(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="address_service")
        svc.update.side_effect = NotFoundException(
            "No address found with id 999", code="ADDRESS_NOT_FOUND"
        )

        with patch("app.api.v1.addresses.get_address_service", return_value=svc):
            response = client.patch(
                f"{PREFIX}/update/999", json={"city": "Rio"}
            )

        assert_error(response, 404, "ADDRESS_NOT_FOUND")

    def test_update_invalid_state(self, client, auth_user):
        auth_user(1)
        response = client.patch(f"{PREFIX}/update/1", json={"state": "X"})
        assert_validation_error(response)


class TestDeleteAddress:
    def test_delete_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="address_service")
        svc.delete.return_value = address_payload()

        with patch("app.api.v1.addresses.get_address_service", return_value=svc):
            response = client.delete(f"{PREFIX}/delete/1")

        assert response.status_code == 200
        assert response.json()["id"] == 1

    def test_delete_not_found(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="address_service")
        svc.delete.side_effect = NotFoundException(
            "No address found with id 999", code="ADDRESS_NOT_FOUND"
        )

        with patch("app.api.v1.addresses.get_address_service", return_value=svc):
            response = client.delete(f"{PREFIX}/delete/999")

        assert_error(response, 404, "ADDRESS_NOT_FOUND")
