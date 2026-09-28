"""Testes HTTP da rota /api/v1/categories.

Sucesso: 201/200 com payloads válidos (criação, listagem, buscas, update, delete).
Erros: validação 422, categoria inexistente 404 e conflito 409 (nome/slug
duplicados).

SEGURANÇA: create/update/delete exigem Bearer token de **administrador**
(401 sem token, 403 sem permissão). Leitura (list/get/name/slug) continua
pública — o catálogo precisa das categorias sem login.

NOTA: o ``_traduzir_value_error`` da rota converte os ``ValueError`` do service
em 403 (não-admin) / 409 (duplicado) / 404 (não encontrado).
"""
from unittest.mock import Mock, patch

import pytest
from helpers import assert_error, assert_validation_error, category_payload

from app.api.exceptions import CategoryNotFoundException, ConflictException
from app.models.user import UserRole

PREFIX = "/api/v1/categories"

CREATE_OK = {"name": "Tecnologia", "slug": "tecnologia"}


@pytest.fixture
def auth_user():
    """Usuário autenticado injetado no lugar de ``get_current_user``.

    Mesmo padrão de test_http_wishlist.py / test_http_reviews.py.
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


class TestCreateCategory:
    def test_create_success(self, client, auth_user):
        auth_user(1, role="admin")
        svc = Mock(name="category_service")
        svc.create.return_value = category_payload()

        with patch("app.api.v1.categories.get_category_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert response.status_code == 201
        body = response.json()
        assert body["id"] == 1
        assert body["name"] == "Tecnologia"
        assert body["slug"] == "tecnologia"

    def test_create_duplicate_name(self, client, auth_user):
        auth_user(1, role="admin")
        svc = Mock(name="category_service")
        svc.create.side_effect = ConflictException(
            "Category with name 'Tecnologia' already exists", code="DUPLICATE_CATEGORY"
        )

        with patch("app.api.v1.categories.get_category_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert_error(response, 409, "DUPLICATE_CATEGORY")

    def test_create_requires_auth(self, client):
        response = client.post(f"{PREFIX}/create", json=CREATE_OK)
        assert response.status_code == 401

    def test_create_customer_forbidden(self, client, auth_user):
        auth_user(1, role="customer")
        svc = Mock(name="category_service")
        svc.create.side_effect = ValueError(
            "Admin permission required to manage categories"
        )

        with patch("app.api.v1.categories.get_category_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert_error(response, 403, "INSUFFICIENT_PERMISSION")

    def test_create_short_name(self, client, auth_user):
        auth_user(1, role="admin")
        response = client.post(f"{PREFIX}/create", json={"name": "ab", "slug": "abc"})
        assert_validation_error(response)

    def test_create_short_slug(self, client, auth_user):
        auth_user(1, role="admin")
        response = client.post(f"{PREFIX}/create", json={"name": "abc", "slug": "ab"})
        assert_validation_error(response)

    def test_create_missing_fields(self, client, auth_user):
        auth_user(1, role="admin")
        response = client.post(f"{PREFIX}/create", json={})
        assert_validation_error(response)


class TestListCategories:
    def test_list_success(self, client):
        svc = Mock(name="category_service")
        svc.get_all.return_value = [category_payload(), category_payload(id=2, name="Ficcao", slug="ficcao")]

        with patch("app.api.v1.categories.get_category_service", return_value=svc):
            response = client.get(f"{PREFIX}/list")

        assert response.status_code == 200
        assert len(response.json()) == 2


class TestGetCategory:
    def test_get_by_id_success(self, client):
        svc = Mock(name="category_service")
        svc.get_by_id.return_value = category_payload()

        with patch("app.api.v1.categories.get_category_service", return_value=svc):
            response = client.get(f"{PREFIX}/get/1")

        assert response.status_code == 200
        assert response.json()["id"] == 1

    def test_get_by_id_not_found(self, client):
        svc = Mock(name="category_service")
        svc.get_by_id.side_effect = CategoryNotFoundException()

        with patch("app.api.v1.categories.get_category_service", return_value=svc):
            response = client.get(f"{PREFIX}/get/999")

        assert_error(response, 404, "CATEGORY_NOT_FOUND")

    def test_get_by_name_success(self, client):
        svc = Mock(name="category_service")
        svc.get_by_name.return_value = category_payload()

        with patch("app.api.v1.categories.get_category_service", return_value=svc):
            response = client.get(f"{PREFIX}/name/Tecnologia")

        assert response.status_code == 200

    def test_get_by_name_not_found(self, client):
        svc = Mock(name="category_service")
        svc.get_by_name.side_effect = CategoryNotFoundException()

        with patch("app.api.v1.categories.get_category_service", return_value=svc):
            response = client.get(f"{PREFIX}/name/Inexistente")

        assert_error(response, 404, "CATEGORY_NOT_FOUND")

    def test_get_by_slug_success(self, client):
        svc = Mock(name="category_service")
        svc.get_by_slug.return_value = category_payload()

        with patch("app.api.v1.categories.get_category_service", return_value=svc):
            response = client.get(f"{PREFIX}/slug/tecnologia")

        assert response.status_code == 200


class TestUpdateCategory:
    def test_update_success(self, client, auth_user):
        auth_user(1, role="admin")
        svc = Mock(name="category_service")
        svc.update.return_value = category_payload(name="Tecnologia Web")

        with patch("app.api.v1.categories.get_category_service", return_value=svc):
            response = client.patch(f"{PREFIX}/update/1", json={"name": "Tecnologia Web"})

        assert response.status_code == 200
        assert response.json()["name"] == "Tecnologia Web"

    def test_update_requires_auth(self, client):
        response = client.patch(f"{PREFIX}/update/1", json={"name": "Nova"})
        assert response.status_code == 401

    def test_update_customer_forbidden(self, client, auth_user):
        auth_user(1, role="customer")
        svc = Mock(name="category_service")
        svc.update.side_effect = ValueError(
            "Admin permission required to manage categories"
        )

        with patch("app.api.v1.categories.get_category_service", return_value=svc):
            response = client.patch(f"{PREFIX}/update/1", json={"name": "Nova"})

        assert_error(response, 403, "INSUFFICIENT_PERMISSION")

    def test_update_not_found(self, client, auth_user):
        auth_user(1, role="admin")
        svc = Mock(name="category_service")
        svc.update.side_effect = CategoryNotFoundException()

        with patch("app.api.v1.categories.get_category_service", return_value=svc):
            response = client.patch(f"{PREFIX}/update/999", json={"name": "Nova"})

        assert_error(response, 404, "CATEGORY_NOT_FOUND")

    def test_update_invalid_name(self, client, auth_user):
        auth_user(1, role="admin")
        response = client.patch(f"{PREFIX}/update/1", json={"name": "ab"})
        assert_validation_error(response)


class TestDeleteCategory:
    def test_delete_success(self, client, auth_user):
        auth_user(1, role="admin")
        svc = Mock(name="category_service")
        svc.delete.return_value = category_payload()

        with patch("app.api.v1.categories.get_category_service", return_value=svc):
            response = client.delete(f"{PREFIX}/delete/1")

        assert response.status_code == 200
        assert response.json()["id"] == 1

    def test_delete_requires_auth(self, client):
        response = client.delete(f"{PREFIX}/delete/1")
        assert response.status_code == 401

    def test_delete_customer_forbidden(self, client, auth_user):
        auth_user(1, role="customer")
        svc = Mock(name="category_service")
        svc.delete.side_effect = ValueError(
            "Admin permission required to manage categories"
        )

        with patch("app.api.v1.categories.get_category_service", return_value=svc):
            response = client.delete(f"{PREFIX}/delete/1")

        assert_error(response, 403, "INSUFFICIENT_PERMISSION")

    def test_delete_not_found(self, client, auth_user):
        auth_user(1, role="admin")
        svc = Mock(name="category_service")
        svc.delete.side_effect = CategoryNotFoundException()

        with patch("app.api.v1.categories.get_category_service", return_value=svc):
            response = client.delete(f"{PREFIX}/delete/999")

        assert_error(response, 404, "CATEGORY_NOT_FOUND")
