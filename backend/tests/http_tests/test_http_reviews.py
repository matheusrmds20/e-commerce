"""Testes HTTP da rota /api/v1/reviews.

Sucesso: 201/200 com payloads válidos (criação, listagem, buscas por id/
usuário/produto/nota, update e delete).
Erros: validação 422 (nota fora de 1-5, comentário curto), usuário/produto/
avaliação inexistente 404 e avaliação duplicada 409.

NOTA: o ReviewService real lança ``ValueError`` em vez das exceções de domínio
— em produção esses erros viram 500. Ver RELATORIO_TESTES_HTTP.md.
"""
from unittest.mock import Mock, patch

from helpers import assert_error, assert_validation_error, review_payload

from app.api.exceptions import (
    DuplicateReviewException,
    NotFoundException,
    ProductNotFoundException,
    UserNotFoundException,
)

PREFIX = "/api/v1/reviews"

CREATE_OK = {"product_id": 1, "rating": 5, "comment": "Excelente livro"}


class TestCreateReview:
    def test_create_success(self, client):
        svc = Mock(name="review_service")
        svc.create.return_value = review_payload()

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.post(f"{PREFIX}/create?user_id=1", json=CREATE_OK)

        assert response.status_code == 201
        body = response.json()
        assert body["rating"] == 5
        assert body["product_id"] == 1

    def test_create_user_not_found(self, client):
        svc = Mock(name="review_service")
        svc.create.side_effect = UserNotFoundException(user_id=999)

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.post(f"{PREFIX}/create?user_id=999", json=CREATE_OK)

        assert_error(response, 404, "USER_NOT_FOUND")

    def test_create_product_not_found(self, client):
        svc = Mock(name="review_service")
        svc.create.side_effect = ProductNotFoundException()

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.post(
                f"{PREFIX}/create?user_id=1", json={**CREATE_OK, "product_id": 999}
            )

        assert_error(response, 404, "PRODUCT_NOT_FOUND")

    def test_create_duplicate_review(self, client):
        svc = Mock(name="review_service")
        svc.create.side_effect = DuplicateReviewException()

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.post(f"{PREFIX}/create?user_id=1", json=CREATE_OK)

        assert_error(response, 409, "DUPLICATE_REVIEW")

    def test_create_rating_above_5(self, client):
        response = client.post(
            f"{PREFIX}/create?user_id=1", json={**CREATE_OK, "rating": 6}
        )
        assert_validation_error(response)

    def test_create_rating_zero(self, client):
        response = client.post(
            f"{PREFIX}/create?user_id=1", json={**CREATE_OK, "rating": 0}
        )
        assert_validation_error(response)

    def test_create_short_comment(self, client):
        response = client.post(
            f"{PREFIX}/create?user_id=1", json={**CREATE_OK, "comment": "ab"}
        )
        assert_validation_error(response)

    def test_create_missing_rating(self, client):
        response = client.post(
            f"{PREFIX}/create?user_id=1", json={"product_id": 1}
        )
        assert_validation_error(response)

    def test_create_missing_user_id_query(self, client):
        response = client.post(f"{PREFIX}/create", json=CREATE_OK)
        assert_validation_error(response)


class TestListReviews:
    def test_list_success(self, client):
        svc = Mock(name="review_service")
        svc.get_all.return_value = [review_payload(), review_payload(id=2, rating=4)]

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.get(f"{PREFIX}/list")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_empty_returns_500(self, client):
        """Lista vazia: o serviço real lança ValueError -> 500 (ver relatório)."""
        svc = Mock(name="review_service")
        svc.get_all.side_effect = ValueError("No reviews found")

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.get(f"{PREFIX}/list")

        assert response.status_code == 500


class TestGetReview:
    def test_get_by_id_success(self, client):
        svc = Mock(name="review_service")
        svc.get_by_id.return_value = review_payload()

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.get(f"{PREFIX}/get/1?user_id=1")

        assert response.status_code == 200
        assert response.json()["id"] == 1

    def test_get_by_id_not_found(self, client):
        svc = Mock(name="review_service")
        svc.get_by_id.side_effect = NotFoundException(
            "No review found with id 999", code="REVIEW_NOT_FOUND"
        )

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.get(f"{PREFIX}/get/999?user_id=1")

        assert_error(response, 404, "REVIEW_NOT_FOUND")

    def test_get_by_user_success(self, client):
        svc = Mock(name="review_service")
        svc.get_by_user_id.return_value = [review_payload()]

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.get(f"{PREFIX}/user/1")

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_by_product_success(self, client):
        svc = Mock(name="review_service")
        svc.get_by_product_id.return_value = [review_payload()]

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.get(f"{PREFIX}/product/1")

        assert response.status_code == 200

    def test_get_by_rating_success(self, client):
        svc = Mock(name="review_service")
        svc.get_by_rating.return_value = [review_payload()]

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.get(f"{PREFIX}/rating/5")

        assert response.status_code == 200

    def test_get_by_rating_above_5(self, client):
        response = client.get(f"{PREFIX}/rating/9")
        assert_validation_error(response)

    def test_get_by_rating_zero(self, client):
        response = client.get(f"{PREFIX}/rating/0")
        assert_validation_error(response)


class TestUpdateReview:
    def test_update_success(self, client):
        svc = Mock(name="review_service")
        svc.update.return_value = review_payload(rating=4, comment="Muito bom")

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.patch(
                f"{PREFIX}/update/1?user_id=1", json={"rating": 4, "comment": "Muito bom"}
            )

        assert response.status_code == 200
        assert response.json()["rating"] == 4

    def test_update_not_found(self, client):
        svc = Mock(name="review_service")
        svc.update.side_effect = NotFoundException(
            "No review found with id 999", code="REVIEW_NOT_FOUND"
        )

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.patch(f"{PREFIX}/update/999?user_id=1", json={"rating": 3})

        assert_error(response, 404, "REVIEW_NOT_FOUND")

    def test_update_rating_invalid(self, client):
        response = client.patch(f"{PREFIX}/update/1?user_id=1", json={"rating": 7})
        assert_validation_error(response)


class TestDeleteReview:
    def test_delete_success(self, client):
        svc = Mock(name="review_service")
        svc.delete.return_value = review_payload()

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.delete(f"{PREFIX}/delete/1?user_id=1")

        assert response.status_code == 200
        assert response.json()["id"] == 1

    def test_delete_not_found(self, client):
        svc = Mock(name="review_service")
        svc.delete.side_effect = NotFoundException(
            "No review found with id 999", code="REVIEW_NOT_FOUND"
        )

        with patch("app.api.v1.reviews.get_review_service", return_value=svc):
            response = client.delete(f"{PREFIX}/delete/999?user_id=1")

        assert_error(response, 404, "REVIEW_NOT_FOUND")
