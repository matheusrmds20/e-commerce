from unittest.mock import Mock, patch

import pytest
from helpers import assert_error, assert_validation_error, cart_item_payload, cart_payload

from app.api.exceptions import (
    CartNotFoundException,
    ConflictException,
    InsufficientStockException,
    NotFoundException,
    ProductNotFoundException,
    UserNotFoundException,
)

PREFIX = "/api/v1/cart"

ADD_ITEM_OK = {"product_id": 1, "quantity": 2}


@pytest.fixture
def auth_user():

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


    def test_create_requires_auth(self, client):
        response = client.post(f"{PREFIX}/create")
        assert response.status_code == 401

    def test_list_requires_auth(self, client):
        response = client.get(f"{PREFIX}/cart/me")
        assert response.status_code == 401

    def test_add_item_requires_auth(self, client):
        response = client.post(f"{PREFIX}/1/items/add", json=ADD_ITEM_OK)
        assert response.status_code == 401

    def test_user_id_query_is_ignored(self, client, auth_user):

        response = client.get(f"{PREFIX}/cart/me?user_id=1")
        assert response.status_code == 401


class TestCreateCart:
    def test_create_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="cart_service")
        svc.create.return_value = cart_payload(items=[])

        with patch("app.api.v1.cart.get_cart_service", return_value=svc):
            response = client.post(f"{PREFIX}/create")

        assert response.status_code == 201
        body = response.json()
        assert body["id"] == 1
        assert body["user_id"] == 1
        # O user_id vem do token, não da query.
        svc.create.assert_called_once_with(1)

    def test_create_user_not_found(self, client, auth_user):
        auth_user(999)
        svc = Mock(name="cart_service")
        svc.create.side_effect = UserNotFoundException(user_id=999)

        with patch("app.api.v1.cart.get_cart_service", return_value=svc):
            response = client.post(f"{PREFIX}/create")

        assert_error(response, 404, "USER_NOT_FOUND")

    def test_create_user_already_has_cart(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="cart_service")
        svc.create.side_effect = ConflictException(
            "User 1 already has a cart", code="CART_ALREADY_EXISTS"
        )

        with patch("app.api.v1.cart.get_cart_service", return_value=svc):
            response = client.post(f"{PREFIX}/create")

        assert_error(response, 409, "CART_ALREADY_EXISTS")


class TestGetCart:
    def test_get_by_user_id_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="cart_service")
        svc.get_by_user_id.return_value = cart_payload()

        with patch("app.api.v1.cart.get_cart_service", return_value=svc):
            response = client.get(f"{PREFIX}/cart/me")

        assert response.status_code == 200
        assert response.json()["user_id"] == 1
        svc.get_by_user_id.assert_called_once_with(1)

    def test_get_by_user_id_not_found(self, client, auth_user):
        auth_user(999)
        svc = Mock(name="cart_service")
        svc.get_by_user_id.side_effect = NotFoundException(
            "No cart found with user_id 999", code="CART_NOT_FOUND"
        )

        with patch("app.api.v1.cart.get_cart_service", return_value=svc):
            response = client.get(f"{PREFIX}/cart/me")

        assert_error(response, 404, "CART_NOT_FOUND")

    def test_get_by_user_id_cart_nao_encontrada_vira_404(self, client, auth_user):

        auth_user(1)
        svc = Mock(name="cart_service")
        svc.get_by_user_id.side_effect = CartNotFoundException()

        with patch("app.api.v1.cart.get_cart_service", return_value=svc):
            response = client.get(f"{PREFIX}/cart/me")

        assert_error(response, 404, "CART_NOT_FOUND")
        assert response.json()["error"]["message"] == "Carrinho não encontrado."


class TestAddItem:
    def test_add_item_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="cart_service")
        svc.add_item.return_value = cart_item_payload()

        with patch("app.api.v1.cart.get_cart_service", return_value=svc):
            response = client.post(f"{PREFIX}/1/items/add", json=ADD_ITEM_OK)

        assert response.status_code == 201
        body = response.json()
        assert body["product_id"] == 1
        assert body["quantity"] == 2
        svc.add_item.assert_called_once_with(1, 1, 1, 2)

    def test_add_item_product_not_found(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="cart_service")
        svc.add_item.side_effect = ProductNotFoundException()

        with patch("app.api.v1.cart.get_cart_service", return_value=svc):
            response = client.post(f"{PREFIX}/1/items/add", json=ADD_ITEM_OK)

        assert_error(response, 404, "PRODUCT_NOT_FOUND")

    def test_add_item_insufficient_stock(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="cart_service")
        svc.add_item.side_effect = InsufficientStockException("Book", 1)

        with patch("app.api.v1.cart.get_cart_service", return_value=svc):
            response = client.post(f"{PREFIX}/1/items/add", json=ADD_ITEM_OK)

        assert_error(response, 409, "INSUFFICIENT_STOCK")

    def test_add_item_cart_not_found(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="cart_service")
        svc.add_item.side_effect = NotFoundException(
            "No cart found with id 999", code="CART_NOT_FOUND"
        )

        with patch("app.api.v1.cart.get_cart_service", return_value=svc):
            response = client.post(f"{PREFIX}/999/items/add", json=ADD_ITEM_OK)

        assert_error(response, 404, "CART_NOT_FOUND")

    def test_add_item_zero_quantity(self, client, auth_user):
        auth_user(1)
        response = client.post(
            f"{PREFIX}/1/items/add", json={"product_id": 1, "quantity": 0}
        )
        assert_validation_error(response)

    def test_add_item_missing_product_id(self, client, auth_user):
        auth_user(1)
        response = client.post(f"{PREFIX}/1/items/add", json={"quantity": 2})
        assert_validation_error(response)


class TestUpdateItem:
    def test_update_quantity_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="cart_service")
        svc.update_item.return_value = cart_item_payload(quantity=5)

        with patch("app.api.v1.cart.get_cart_service", return_value=svc):
            response = client.patch(f"{PREFIX}/1/items/update/1?quantity=5")

        assert response.status_code == 200
        assert response.json()["quantity"] == 5
        svc.update_item.assert_called_once_with(1, 1, 1, 5)

    def test_update_quantity_zero_removes_item(self, client, auth_user):

        auth_user(1)
        svc = Mock(name="cart_service")
        svc.update_item.return_value = cart_item_payload(quantity=0)

        with patch("app.api.v1.cart.get_cart_service", return_value=svc):
            response = client.patch(f"{PREFIX}/1/items/update/1?quantity=0")

        assert response.status_code == 200
        svc.update_item.assert_called_once_with(1, 1, 1, 0)

    def test_update_quantity_missing(self, client, auth_user):
        auth_user(1)
        response = client.patch(f"{PREFIX}/1/items/update/1")
        assert response.status_code == 422

    def test_update_item_not_found(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="cart_service")
        svc.update_item.side_effect = NotFoundException(
            "No cart item found with id 999", code="CART_ITEM_NOT_FOUND"
        )

        with patch("app.api.v1.cart.get_cart_service", return_value=svc):
            response = client.patch(f"{PREFIX}/1/items/update/999?quantity=3")

        assert_error(response, 404, "CART_ITEM_NOT_FOUND")


class TestRemoveItem:
    def test_remove_item_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="cart_service")
        svc.remove_item.return_value = cart_item_payload()

        with patch("app.api.v1.cart.get_cart_service", return_value=svc):
            response = client.delete(f"{PREFIX}/1/items/delete/1")

        assert response.status_code == 200
        assert response.json()["id"] == 1
        svc.remove_item.assert_called_once_with(1, 1, 1)

    def test_remove_item_not_found(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="cart_service")
        svc.remove_item.side_effect = NotFoundException(
            "No cart item found with id 999", code="CART_ITEM_NOT_FOUND"
        )

        with patch("app.api.v1.cart.get_cart_service", return_value=svc):
            response = client.delete(f"{PREFIX}/1/items/delete/999")

        assert_error(response, 404, "CART_ITEM_NOT_FOUND")


class TestClearCart:
    def test_clear_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="cart_service")
        svc.clear.return_value = cart_payload(cart_items=[])

        with patch("app.api.v1.cart.get_cart_service", return_value=svc):
            response = client.delete(f"{PREFIX}/1/items/clear")

        assert response.status_code == 200
        assert response.json()["cart_items"] == []
        svc.clear.assert_called_once_with(1, 1)

    def test_clear_cart_not_found(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="cart_service")
        svc.clear.side_effect = NotFoundException(
            "No cart found with id 999", code="CART_NOT_FOUND"
        )

        with patch("app.api.v1.cart.get_cart_service", return_value=svc):
            response = client.delete(f"{PREFIX}/999/items/clear")

        assert_error(response, 404, "CART_NOT_FOUND")

