"""Testes HTTP da rota /api/v1/wishlists.

Sucesso: 201/200 com payloads válidos (criação, listagem do próprio usuário,
busca por id, listagem geral [admin], busca por produto, update e delete).
Erros: validação 422, usuário/produto/item inexistente 404, item duplicado 409,
item de outro usuário 403 e ausência de token 401.

SEGURANÇA: o dono da wishlist vem do TOKEN (``Depends(get_current_user)``), não
mais da query ``user_id``. Isso fecha o IDOR que permitia ler/alterar a
wishlist de outra pessoa passando um id arbitrário. Um cliente comum só acessa
a própria wishlist; administradores podem operar sobre qualquer usuário.

NOTA: o ``WishlistService`` real sinaliza falhas com ``ValueError``; a rota as
traduz para 403 (não-dono) / 409 (duplicado) / 404 (não encontrado) em
``_traduzir_value_error``.
"""
from unittest.mock import Mock, patch

import pytest
from helpers import assert_error, assert_validation_error, wishlist_payload

from app.api.exceptions import (
    DuplicateWishlistException,
    NotFoundException,
    ProductNotFoundException,
    UserNotFoundException,
)
from app.models.user import UserRole

PREFIX = "/api/v1/wishlists"

CREATE_OK = {"product_id": 1}


@pytest.fixture
def auth_user():
    """Usuário autenticado injetado no lugar de ``get_current_user``.

    Mesmo padrão de test_http_users.py: sobrescreve a dependência e devolve um
    objeto simples com ``id``/``role``.
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


class TestCreateWishlistItem:
    def test_create_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="wishlist_service")
        svc.create.return_value = wishlist_payload()

        with patch("app.api.v1.wishlist.get_wishlist_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert response.status_code == 201
        body = response.json()
        assert body["product_id"] == 1
        assert body["user_id"] == 1
        # O service recebe o usuário autenticado, não um user_id de query.
        assert svc.create.call_args[0][1].id == 1

    def test_create_requires_auth(self, client):
        response = client.post(f"{PREFIX}/create", json=CREATE_OK)
        assert response.status_code == 401

    def test_create_user_not_found(self, client, auth_user):
        auth_user(999)
        svc = Mock(name="wishlist_service")
        svc.create.side_effect = UserNotFoundException(user_id=999)

        with patch("app.api.v1.wishlist.get_wishlist_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert_error(response, 404, "USER_NOT_FOUND")

    def test_create_product_not_found(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="wishlist_service")
        svc.create.side_effect = ProductNotFoundException()

        with patch("app.api.v1.wishlist.get_wishlist_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json={"product_id": 999})

        assert_error(response, 404, "PRODUCT_NOT_FOUND")

    def test_create_duplicate_item(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="wishlist_service")
        svc.create.side_effect = DuplicateWishlistException()

        with patch("app.api.v1.wishlist.get_wishlist_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert_error(response, 409, "DUPLICATE_WISHLIST")

    def test_create_missing_product_id(self, client, auth_user):
        auth_user(1)
        response = client.post(f"{PREFIX}/create", json={})
        assert_validation_error(response)


class TestListWishlistItems:
    def test_list_by_user_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="wishlist_service")
        svc.get_by_user_id.return_value = [
            wishlist_payload(),
            wishlist_payload(id=2, product_id=2),
        ]

        with patch("app.api.v1.wishlist.get_wishlist_service", return_value=svc):
            response = client.get(f"{PREFIX}/list")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_requires_auth(self, client):
        response = client.get(f"{PREFIX}/list")
        assert response.status_code == 401

    def test_list_by_user_not_found(self, client, auth_user):
        auth_user(999)
        svc = Mock(name="wishlist_service")
        svc.get_by_user_id.side_effect = NotFoundException(
            "No wishlist items found with user_id 999", code="WISHLIST_NOT_FOUND"
        )

        with patch("app.api.v1.wishlist.get_wishlist_service", return_value=svc):
            response = client.get(f"{PREFIX}/list")

        assert_error(response, 404, "WISHLIST_NOT_FOUND")

    def test_list_all_success(self, client, auth_user):
        auth_user(99, role="admin")
        svc = Mock(name="wishlist_service")
        svc.get_all.return_value = [wishlist_payload()]

        with patch("app.api.v1.wishlist.get_wishlist_service", return_value=svc):
            response = client.get(f"{PREFIX}/all")

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_list_all_forbidden_for_customer(self, client, auth_user):
        auth_user(1, role="customer")
        svc = Mock(name="wishlist_service")
        svc.get_all.side_effect = ValueError(
            "Admin permission required to list all wishlists"
        )

        with patch("app.api.v1.wishlist.get_wishlist_service", return_value=svc):
            response = client.get(f"{PREFIX}/all")

        assert_error(response, 403, "WISHLIST_FORBIDDEN")

    def test_get_by_product_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="wishlist_service")
        svc.get_by_product_id.return_value = [wishlist_payload()]

        with patch("app.api.v1.wishlist.get_wishlist_service", return_value=svc):
            response = client.get(f"{PREFIX}/product/1")

        assert response.status_code == 200


class TestDeleteWishlistItem:
    def test_delete_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="wishlist_service")
        svc.delete.return_value = wishlist_payload()

        with patch("app.api.v1.wishlist.get_wishlist_service", return_value=svc):
            response = client.delete(f"{PREFIX}/delete/1")

        assert response.status_code == 200
        assert response.json()["id"] == 1

    def test_delete_not_found(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="wishlist_service")
        svc.delete.side_effect = NotFoundException(
            "No wishlist item found with id 999", code="WISHLIST_NOT_FOUND"
        )

        with patch("app.api.v1.wishlist.get_wishlist_service", return_value=svc):
            response = client.delete(f"{PREFIX}/delete/999")

        assert_error(response, 404, "WISHLIST_NOT_FOUND")

    def test_delete_forbidden_for_other_user(self, client, auth_user):
        auth_user(2)
        svc = Mock(name="wishlist_service")
        svc.delete.side_effect = ValueError("Wishlist item is not owned by user")

        with patch("app.api.v1.wishlist.get_wishlist_service", return_value=svc):
            response = client.delete(f"{PREFIX}/delete/1")

        assert_error(response, 403, "WISHLIST_FORBIDDEN")
