"""Testes HTTP da rota /api/v1/reviews.

Sucesso: 201/200 com payloads válidos (criação, minhas avaliações, busca por
produto, update e delete).
Erros: validação 422 (nota fora de 1-5, comentário curto), usuário/produto/
avaliação inexistente 404, avaliação duplicada 409, avaliação de outro
usuário 403 e ausência de token 401.

SEGURANÇA: o autor da avaliação vem do TOKEN (``Depends(get_current_user)``),
não mais da query ``user_id``. Isso fecha o IDOR que permitia criar/editar/
excluir avaliações em nome de outra pessoa. Um cliente comum só acessa as
próprias avaliações; administradores podem operar sobre qualquer uma.

Rotas removidas como órfãs: ``GET /list`` (substituído por /list autenticado),
``GET /get/{id}`` e ``GET /rating/{rating}``.

NOTA: o ``ReviewService`` real sinaliza falhas com ``ValueError``; a rota as
traduz para 403 (não-dono) / 409 (duplicado) / 404 (não encontrado) em
``_traduzir_value_error``.
"""
from unittest.mock import Mock, patch

import pytest
from helpers import assert_error, assert_validation_error, review_payload

from app.api.exceptions import (
    DuplicateReviewException,
    NotFoundException,
    ProductNotFoundException,
    ReviewForbiddenException,
    UserNotFoundException,
)
from app.models.user import UserRole

PREFIX = "/api/v1/reviews"

CREATE_OK = {"product_id": 1, "rating": 5, "comment": "Excelente livro"}


@pytest.fixture
def auth_user():
    """Usuário autenticado injetado no lugar de ``get_current_user``.

    Mesmo padrão de test_http_wishlist.py: sobrescreve a dependência e devolve
    um objeto simples com ``id``/``role``.
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


class TestCreateReview:
    def test_create_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="review_service")
        svc.create.return_value = review_payload()

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert response.status_code == 201
        body = response.json()
        assert body["rating"] == 5
        assert body["product_id"] == 1
        # O service recebe o usuário autenticado, não um user_id de query.
        assert svc.create.call_args[0][0].id == 1

    def test_create_requires_auth(self, client):
        response = client.post(f"{PREFIX}/create", json=CREATE_OK)
        assert response.status_code == 401

    def test_create_user_not_found(self, client, auth_user):
        auth_user(999)
        svc = Mock(name="review_service")
        svc.create.side_effect = UserNotFoundException(user_id=999)

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert_error(response, 404, "USER_NOT_FOUND")

    def test_create_product_not_found(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="review_service")
        svc.create.side_effect = ProductNotFoundException()

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.post(
                f"{PREFIX}/create", json={**CREATE_OK, "product_id": 999}
            )

        assert_error(response, 404, "PRODUCT_NOT_FOUND")

    def test_create_duplicate_review(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="review_service")
        svc.create.side_effect = DuplicateReviewException()

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert_error(response, 409, "DUPLICATE_REVIEW")

    def test_create_rating_above_5(self, client, auth_user):
        auth_user(1)
        response = client.post(f"{PREFIX}/create", json={**CREATE_OK, "rating": 6})
        assert_validation_error(response)

    def test_create_rating_zero(self, client, auth_user):
        auth_user(1)
        response = client.post(f"{PREFIX}/create", json={**CREATE_OK, "rating": 0})
        assert_validation_error(response)

    def test_create_short_comment(self, client, auth_user):
        auth_user(1)
        response = client.post(
            f"{PREFIX}/create", json={**CREATE_OK, "comment": "ab"}
        )
        assert_validation_error(response)

    def test_create_missing_rating(self, client, auth_user):
        auth_user(1)
        response = client.post(f"{PREFIX}/create", json={"product_id": 1})
        assert_validation_error(response)


class TestListMyReviews:
    def test_list_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="review_service")
        svc.get_by_user_id.return_value = [review_payload(), review_payload(id=2, rating=4)]

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.get(f"{PREFIX}/list")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_requires_auth(self, client):
        response = client.get(f"{PREFIX}/list")
        assert response.status_code == 401

    def test_list_other_user_forbidden(self, client, auth_user):
        auth_user(2)
        svc = Mock(name="review_service")
        svc.get_by_user_id.side_effect = ReviewForbiddenException()

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.get(f"{PREFIX}/list?user_id=1")

        assert_error(response, 403, "REVIEW_FORBIDDEN")

    def test_list_other_user_as_admin(self, client, auth_user):
        auth_user(99, role="admin")
        svc = Mock(name="review_service")
        svc.get_by_user_id.return_value = [review_payload()]

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.get(f"{PREFIX}/list?user_id=1")

        assert response.status_code == 200
        assert len(response.json()) == 1


class TestGetReviewsByProduct:
    def test_get_by_product_success(self, client):
        svc = Mock(name="review_service")
        svc.get_by_product_id.return_value = [review_payload()]

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.get(f"{PREFIX}/product/1")

        assert response.status_code == 200

    def test_get_by_product_not_found(self, client):
        svc = Mock(name="review_service")
        svc.get_by_product_id.side_effect = ProductNotFoundException()

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.get(f"{PREFIX}/product/999")

        assert_error(response, 404, "PRODUCT_NOT_FOUND")


class TestUpdateReview:
    def test_update_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="review_service")
        svc.update.return_value = review_payload(rating=4, comment="Muito bom")

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.patch(
                f"{PREFIX}/update/1", json={"rating": 4, "comment": "Muito bom"}
            )

        assert response.status_code == 200
        assert response.json()["rating"] == 4

    def test_update_requires_auth(self, client):
        response = client.patch(f"{PREFIX}/update/1", json={"rating": 4})
        assert response.status_code == 401

    def test_update_not_owned(self, client, auth_user):
        auth_user(2)
        svc = Mock(name="review_service")
        svc.update.side_effect = ReviewForbiddenException()

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.patch(f"{PREFIX}/update/1", json={"rating": 3})

        assert_error(response, 403, "REVIEW_FORBIDDEN")

    def test_update_not_found(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="review_service")
        svc.update.side_effect = NotFoundException(
            "No review found with id 999", code="REVIEW_NOT_FOUND"
        )

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.patch(f"{PREFIX}/update/999", json={"rating": 3})

        assert_error(response, 404, "REVIEW_NOT_FOUND")

    def test_update_rating_invalid(self, client, auth_user):
        auth_user(1)
        response = client.patch(f"{PREFIX}/update/1", json={"rating": 7})
        assert_validation_error(response)


class TestDeleteReview:
    def test_delete_success(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="review_service")
        svc.delete.return_value = review_payload()

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.delete(f"{PREFIX}/delete/1")

        assert response.status_code == 200
        assert response.json()["id"] == 1

    def test_delete_requires_auth(self, client):
        response = client.delete(f"{PREFIX}/delete/1")
        assert response.status_code == 401

    def test_delete_not_owned(self, client, auth_user):
        auth_user(2)
        svc = Mock(name="review_service")
        svc.delete.side_effect = ReviewForbiddenException()

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.delete(f"{PREFIX}/delete/1")

        assert_error(response, 403, "REVIEW_FORBIDDEN")

    def test_delete_not_found(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="review_service")
        svc.delete.side_effect = NotFoundException(
            "No review found with id 999", code="REVIEW_NOT_FOUND"
        )

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.delete(f"{PREFIX}/delete/999")

        assert_error(response, 404, "REVIEW_NOT_FOUND")
