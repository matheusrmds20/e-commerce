"""Testes HTTP da rota /api/v1/wishlists.

Sucesso: 201/200 com payloads válidos (criação, listagem por usuário, busca
por id, listagem geral, busca por produto, update e delete).
Erros: validação 422, usuário/produto/item inexistente 404 e item duplicado 409.

NOTA: o WishlistService real lança ``ValueError`` em vez das exceções de
domínio — em produção esses erros viram 500. Ver RELATORIO_TESTES_HTTP.md.
"""
from unittest.mock import Mock, patch

from helpers import assert_error, assert_validation_error, wishlist_payload

from app.api.exceptions import (
    DuplicateWishlistException,
    NotFoundException,
    ProductNotFoundException,
    UserNotFoundException,
)

PREFIX = "/api/v1/wishlists"

CREATE_OK = {"product_id": 1}


class TestCreateWishlistItem:
    def test_create_success(self, client):
        svc = Mock(name="wishlist_service")
        svc.create.return_value = wishlist_payload()

        with patch("app.api.v1.wishlist.get_wishlist_service", return_value=svc):
            response = client.post(f"{PREFIX}/create?user_id=1", json=CREATE_OK)

        assert response.status_code == 201
        body = response.json()
        assert body["product_id"] == 1
        assert body["user_id"] == 1

    def test_create_user_not_found(self, client):
        svc = Mock(name="wishlist_service")
        svc.create.side_effect = UserNotFoundException(user_id=999)

        with patch("app.api.v1.wishlist.get_wishlist_service", return_value=svc):
            response = client.post(f"{PREFIX}/create?user_id=999", json=CREATE_OK)

        assert_error(response, 404, "USER_NOT_FOUND")

    def test_create_product_not_found(self, client):
        svc = Mock(name="wishlist_service")
        svc.create.side_effect = ProductNotFoundException()

        with patch("app.api.v1.wishlist.get_wishlist_service", return_value=svc):
            response = client.post(
                f"{PREFIX}/create?user_id=1", json={"product_id": 999}
            )

        assert_error(response, 404, "PRODUCT_NOT_FOUND")

    def test_create_duplicate_item(self, client):
        svc = Mock(name="wishlist_service")
        svc.create.side_effect = DuplicateWishlistException()

        with patch("app.api.v1.wishlist.get_wishlist_service", return_value=svc):
            response = client.post(f"{PREFIX}/create?user_id=1", json=CREATE_OK)

        assert_error(response, 409, "DUPLICATE_WISHLIST")

    def test_create_missing_product_id(self, client):
        response = client.post(f"{PREFIX}/create?user_id=1", json={})
        assert_validation_error(response)

    def test_create_missing_user_id_query(self, client):
        response = client.post(f"{PREFIX}/create", json=CREATE_OK)
        assert_validation_error(response)


class TestListWishlistItems:
    def test_list_by_user_success(self, client):
        svc = Mock(name="wishlist_service")
        svc.get_by_user_id.return_value = [wishlist_payload(), wishlist_payload(id=2, product_id=2)]

        with patch("app.api.v1.wishlist.get_wishlist_service", return_value=svc):
            response = client.get(f"{PREFIX}/list?user_id=1")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_by_user_not_found(self, client):
        svc = Mock(name="wishlist_service")
        svc.get_by_user_id.side_effect = NotFoundException(
            "No wishlist items found with user_id 999", code="WISHLIST_NOT_FOUND"
        )

        with patch("app.api.v1.wishlist.get_wishlist_service", return_value=svc):
            response = client.get(f"{PREFIX}/list?user_id=999")

        assert_error(response, 404, "WISHLIST_NOT_FOUND")

    def test_list_all_success(self, client):
        svc = Mock(name="wishlist_service")
        svc.get_all.return_value = [wishlist_payload()]

        with patch("app.api.v1.wishlist.get_wishlist_service", return_value=svc):
            response = client.get(f"{PREFIX}/all")

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_by_product_success(self, client):
        svc = Mock(name="wishlist_service")
        svc.get_by_product_id.return_value = [wishlist_payload()]

        with patch("app.api.v1.wishlist.get_wishlist_service", return_value=svc):
            response = client.get(f"{PREFIX}/product/1")

        assert response.status_code == 200


class TestGetWishlistItem:
    def test_get_by_id_success(self, client):
        svc = Mock(name="wishlist_service")
        svc.get_by_id.return_value = wishlist_payload()

        with patch("app.api.v1.wishlist.get_wishlist_service", return_value=svc):
            response = client.get(f"{PREFIX}/get/1?user_id=1")

        assert response.status_code == 200
        assert response.json()["id"] == 1

    def test_get_by_id_not_found(self, client):
        svc = Mock(name="wishlist_service")
        svc.get_by_id.side_effect = NotFoundException(
            "No wishlist item found with id 999", code="WISHLIST_NOT_FOUND"
        )

        with patch("app.api.v1.wishlist.get_wishlist_service", return_value=svc):
            response = client.get(f"{PREFIX}/get/999?user_id=1")

        assert_error(response, 404, "WISHLIST_NOT_FOUND")


class TestUpdateWishlistItem:
    def test_update_success(self, client):
        svc = Mock(name="wishlist_service")
        svc.update.return_value = wishlist_payload(product_id=2)

        with patch("app.api.v1.wishlist.get_wishlist_service", return_value=svc):
            response = client.patch(f"{PREFIX}/update/1?user_id=1", json={"product_id": 2})

        assert response.status_code == 200
        assert response.json()["product_id"] == 2

    def test_update_not_found(self, client):
        svc = Mock(name="wishlist_service")
        svc.update.side_effect = NotFoundException(
            "No wishlist item found with id 999", code="WISHLIST_NOT_FOUND"
        )

        with patch("app.api.v1.wishlist.get_wishlist_service", return_value=svc):
            response = client.patch(f"{PREFIX}/update/999?user_id=1", json={"product_id": 2})

        assert_error(response, 404, "WISHLIST_NOT_FOUND")


class TestDeleteWishlistItem:
    def test_delete_success(self, client):
        svc = Mock(name="wishlist_service")
        svc.delete.return_value = wishlist_payload()

        with patch("app.api.v1.wishlist.get_wishlist_service", return_value=svc):
            response = client.delete(f"{PREFIX}/delete/1?user_id=1")

        assert response.status_code == 200
        assert response.json()["id"] == 1

    def test_delete_not_found(self, client):
        svc = Mock(name="wishlist_service")
        svc.delete.side_effect = NotFoundException(
            "No wishlist item found with id 999", code="WISHLIST_NOT_FOUND"
        )

        with patch("app.api.v1.wishlist.get_wishlist_service", return_value=svc):
            response = client.delete(f"{PREFIX}/delete/999?user_id=1")

        assert_error(response, 404, "WISHLIST_NOT_FOUND")
