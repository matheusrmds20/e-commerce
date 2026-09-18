"""Testes HTTP da rota /api/v1/products.

Sucesso: 201/200 com payloads válidos (criação, listagem, buscas, filtros,
atualização e exclusão).
Erros: validação 422, produto/categoria inexistente 404 e conflito 409.

NOTA: o ProductService real lança ``ValueError`` (e não as exceções de domínio),
então em produção esses erros viram 500. Os testes mockam o serviço levantando
as exceções de domínio para validar o contrato das rotas — ver
RELATORIO_TESTES_HTTP.md.
"""
from unittest.mock import Mock, patch

from helpers import assert_error, assert_validation_error, product_payload

from app.api.exceptions import (
    CategoryNotFoundException,
    ConflictException,
    ProductNotFoundException,
)

PREFIX = "/api/v1/products"

CREATE_OK = {
    "category_id": 1,
    "title": "Clean Code",
    "slug": "clean-code",
    "description": "Principios e praticas do codigo limpo",
    "price": 59.9,
    "author": "Robert C. Martin",
    "isbn": "9780132350884",
    "stock_qty": 25,
}


class TestCreateProduct:
    def test_create_success(self, client):
        svc = Mock(name="product_service")
        svc.create.return_value = product_payload()

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert response.status_code == 201
        body = response.json()
        assert body["id"] == 1
        assert body["title"] == "Clean Code"
        assert body["slug"] == "clean-code"
        assert body["price"] == 59.9
        assert body["stock_qty"] == 25

    def test_create_category_not_found(self, client):
        svc = Mock(name="product_service")
        svc.create.side_effect = CategoryNotFoundException()

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert_error(response, 404, "CATEGORY_NOT_FOUND")

    def test_create_duplicate_title(self, client):
        svc = Mock(name="product_service")
        svc.create.side_effect = ConflictException(
            "Product with title 'Clean Code' already exists", code="DUPLICATE_PRODUCT"
        )

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert_error(response, 409, "DUPLICATE_PRODUCT")

    def test_create_negative_price(self, client):
        response = client.post(f"{PREFIX}/create", json={**CREATE_OK, "price": -1})
        assert_validation_error(response)

    def test_create_short_title(self, client):
        response = client.post(f"{PREFIX}/create", json={**CREATE_OK, "title": "ab"})
        assert_validation_error(response)

    def test_create_discount_pct_above_100(self, client):
        response = client.post(f"{PREFIX}/create", json={**CREATE_OK, "discount_pct": 150})
        assert_validation_error(response)

    def test_create_negative_stock(self, client):
        response = client.post(f"{PREFIX}/create", json={**CREATE_OK, "stock_qty": -2})
        assert_validation_error(response)

    def test_create_missing_required_fields(self, client):
        response = client.post(f"{PREFIX}/create", json={"title": "Só título"})
        assert_validation_error(response)


class TestListProducts:
    def test_list_success(self, client):
        svc = Mock(name="product_service")
        svc.get_all.return_value = [product_payload(), product_payload(id=2)]

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/list")

        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert len(body) == 2

    def test_list_service_error(self, client):
        """Lista vazia: o serviço real lança ValueError; no contrato, documenta-se o 500."""
        svc = Mock(name="product_service")
        svc.get_all.side_effect = ValueError("No products found")

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/list")

        assert response.status_code == 500
        assert response.json()["error"]["code"] == "INTERNAL_SERVER_ERROR"


class TestGetProduct:
    def test_get_by_id_success(self, client):
        svc = Mock(name="product_service")
        svc.get_by_id.return_value = product_payload()

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/get/1")

        assert response.status_code == 200
        assert response.json()["id"] == 1

    def test_get_by_id_not_found(self, client):
        svc = Mock(name="product_service")
        svc.get_by_id.side_effect = ProductNotFoundException()

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/get/999")

        assert_error(response, 404, "PRODUCT_NOT_FOUND")

    def test_get_by_title_success(self, client):
        svc = Mock(name="product_service")
        svc.get_by_title.return_value = product_payload()

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/title/Clean%20Code")

        assert response.status_code == 200

    def test_get_by_title_not_found(self, client):
        svc = Mock(name="product_service")
        svc.get_by_title.side_effect = ProductNotFoundException()

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/title/Inexistente")

        assert_error(response, 404, "PRODUCT_NOT_FOUND")

    def test_get_by_slug_success(self, client):
        svc = Mock(name="product_service")
        svc.get_by_slug.return_value = product_payload()

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/slug/clean-code")

        assert response.status_code == 200

    def test_get_by_isbn_success(self, client):
        svc = Mock(name="product_service")
        svc.get_by_isbn.return_value = product_payload()

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/isbn/9780132350884")

        assert response.status_code == 200

    def test_get_by_isbn_not_found(self, client):
        svc = Mock(name="product_service")
        svc.get_by_isbn.side_effect = ProductNotFoundException()

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/isbn/0000000000000")

        assert_error(response, 404, "PRODUCT_NOT_FOUND")


class TestProductFilters:
    def _list_endpoint(self, client, url, method="get"):
        svc = Mock(name="product_service")
        response = client.get(url) if method == "get" else client.get(url)
        return svc, response

    def test_get_by_category(self, client):
        svc = Mock(name="product_service")
        svc.get_by_category_id.return_value = [product_payload()]

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/category/1")

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_by_publisher(self, client):
        svc = Mock(name="product_service")
        svc.get_by_publisher.return_value = [product_payload()]

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/publisher/Prentice%20Hall")

        assert response.status_code == 200

    def test_get_by_publication_year(self, client):
        svc = Mock(name="product_service")
        svc.get_by_publication_year.return_value = [product_payload()]

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/year/2008")

        assert response.status_code == 200

    def test_get_by_language(self, client):
        svc = Mock(name="product_service")
        svc.get_by_language.return_value = [product_payload()]

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/language/en")

        assert response.status_code == 200

    def test_get_by_discount_pct(self, client):
        svc = Mock(name="product_service")
        svc.get_by_discount_pct.return_value = [product_payload()]

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/discount/10")

        assert response.status_code == 200

    def test_get_by_stock_qty(self, client):
        svc = Mock(name="product_service")
        svc.get_by_stock_qty.return_value = [product_payload()]

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/stock/25")

        assert response.status_code == 200

    def test_get_by_is_active(self, client):
        svc = Mock(name="product_service")
        svc.get_by_is_active.return_value = [product_payload()]

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/active/true")

        assert response.status_code == 200
        assert response.json()[0]["is_active"] is True

    def test_get_by_category_not_found(self, client):
        svc = Mock(name="product_service")
        svc.get_by_category_id.side_effect = ProductNotFoundException()

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/category/999")

        assert_error(response, 404, "PRODUCT_NOT_FOUND")


class TestUpdateProduct:
    def test_update_success(self, client):
        svc = Mock(name="product_service")
        svc.update.return_value = product_payload(price=49.9)

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.patch(f"{PREFIX}/update/1", json={"price": 49.9})

        assert response.status_code == 200
        assert response.json()["price"] == 49.9

    def test_update_not_found(self, client):
        svc = Mock(name="product_service")
        svc.update.side_effect = ProductNotFoundException()

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.patch(f"{PREFIX}/update/999", json={"price": 49.9})

        assert_error(response, 404, "PRODUCT_NOT_FOUND")

    def test_update_duplicate_title(self, client):
        svc = Mock(name="product_service")
        svc.update.side_effect = ConflictException(
            "Product with title 'Outro' already exists", code="DUPLICATE_PRODUCT"
        )

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.patch(f"{PREFIX}/update/1", json={"title": "Outro"})

        assert_error(response, 409, "DUPLICATE_PRODUCT")

    def test_update_invalid_price(self, client):
        response = client.patch(f"{PREFIX}/update/1", json={"price": -5})
        assert_validation_error(response)

    def test_update_invalid_publication_year(self, client):
        response = client.patch(f"{PREFIX}/update/1", json={"publication_year": 99})
        assert_validation_error(response)


class TestDeleteProduct:
    def test_delete_success(self, client):
        svc = Mock(name="product_service")
        svc.delete.return_value = product_payload()

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.delete(f"{PREFIX}/delete/1")

        assert response.status_code == 200
        assert response.json()["id"] == 1

    def test_delete_not_found(self, client):
        svc = Mock(name="product_service")
        svc.delete.side_effect = ProductNotFoundException()

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.delete(f"{PREFIX}/delete/999")

        assert_error(response, 404, "PRODUCT_NOT_FOUND")


class TestFeaturedProducts:
    """Rota /products/featured — vitrine de destaques da Home.

    Regra de contrato: lista vazia é 200 com [] (ausência de curadoria não é
    erro), diferente das demais listagens que devolvem 400/500 quando vazias.
    """

    def test_featured_success(self, client):
        svc = Mock(name="product_service")
        svc.get_featured.return_value = [
            product_payload(is_featured=True),
            product_payload(id=2, is_featured=True, is_bestseller=True),
        ]

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/featured")

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 2
        assert all(item["is_featured"] for item in body)

    def test_featured_empty_is_200(self, client):
        """Sem destaques marcados: 200 com lista vazia, não erro."""
        svc = Mock(name="product_service")
        svc.get_featured.return_value = []

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/featured")

        assert response.status_code == 200
        assert response.json() == []

    def test_featured_passes_limit(self, client):
        svc = Mock(name="product_service")
        svc.get_featured.return_value = [product_payload(is_featured=True)]

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/featured?limit=3")

        assert response.status_code == 200
        svc.get_featured.assert_called_once_with(3)

    def test_featured_invalid_limit(self, client):
        assert_validation_error(client.get(f"{PREFIX}/featured?limit=0"))
        assert_validation_error(client.get(f"{PREFIX}/featured?limit=101"))


class TestBestsellerProducts:
    """Rota /products/bestsellers — vitrine de mais vendidos da Home."""

    def test_bestsellers_success(self, client):
        svc = Mock(name="product_service")
        svc.get_bestsellers.return_value = [product_payload(is_bestseller=True)]

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/bestsellers")

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["is_bestseller"] is True

    def test_bestsellers_empty_is_200(self, client):
        svc = Mock(name="product_service")
        svc.get_bestsellers.return_value = []

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/bestsellers")

        assert response.status_code == 200
        assert response.json() == []

    def test_bestsellers_passes_limit(self, client):
        svc = Mock(name="product_service")
        svc.get_bestsellers.return_value = []

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/bestsellers?limit=5")

        assert response.status_code == 200
        svc.get_bestsellers.assert_called_once_with(5)

    def test_bestsellers_invalid_limit(self, client):
        assert_validation_error(client.get(f"{PREFIX}/bestsellers?limit=200"))


class TestPaginatedProducts:
    """Rota /products/paginated — envelope { data, meta } (PageMeta)."""

    def test_paginated_success(self, client):
        svc = Mock(name="product_service")
        svc.get_paginated.return_value = {
            "data": [product_payload()],
            "meta": {"page": 1, "per_page": 20, "total": 1, "total_pages": 1},
        }

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/paginated")

        assert response.status_code == 200
        body = response.json()
        assert len(body["data"]) == 1
        assert body["meta"]["total"] == 1
        assert body["meta"]["total_pages"] == 1

    def test_paginated_defaults(self, client):
        svc = Mock(name="product_service")
        svc.get_paginated.return_value = {
            "data": [],
            "meta": {"page": 1, "per_page": 20, "total": 0, "total_pages": 0},
        }

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            client.get(f"{PREFIX}/paginated")

        svc.get_paginated.assert_called_once_with(1, 20, None)

    def test_paginated_passes_params(self, client):
        svc = Mock(name="product_service")
        svc.get_paginated.return_value = {
            "data": [],
            "meta": {"page": 3, "per_page": 5, "total": 0, "total_pages": 0},
        }

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/paginated?page=3&per_page=5")

        assert response.status_code == 200
        svc.get_paginated.assert_called_once_with(3, 5, None)

    def test_paginated_with_category_filter(self, client):
        """`category_id` deve chegar ao serviço para filtrar antes de paginar."""
        svc = Mock(name="product_service")
        svc.get_paginated.return_value = {
            "data": [],
            "meta": {"page": 1, "per_page": 20, "total": 0, "total_pages": 0},
        }

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/paginated?category_id=7")

        assert response.status_code == 200
        svc.get_paginated.assert_called_once_with(1, 20, 7)

    def test_paginated_invalid_category_id(self, client):
        assert_validation_error(client.get(f"{PREFIX}/paginated?category_id=0"))

    def test_paginated_category_not_found(self, client):
        """Categoria inexistente é 404 (erro do cliente), não lista vazia."""
        svc = Mock(name="product_service")
        svc.get_paginated.side_effect = ValueError("No category found with id 999")

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/paginated?category_id=999")

        assert_error(response, 404, "CATEGORY_NOT_FOUND")

    def test_paginated_empty_is_200(self, client):
        """Catálogo vazio: 200 com data [] e meta zerado, não erro."""
        svc = Mock(name="product_service")
        svc.get_paginated.return_value = {
            "data": [],
            "meta": {"page": 1, "per_page": 20, "total": 0, "total_pages": 0},
        }

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/paginated")

        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_paginated_invalid_page(self, client):
        assert_validation_error(client.get(f"{PREFIX}/paginated?page=0"))

    def test_paginated_per_page_above_limit(self, client):
        assert_validation_error(client.get(f"{PREFIX}/paginated?per_page=101"))


class TestRecommendations:
    """Rota /products/recommendations — usada pelo carrinho."""

    def test_recommendations_success(self, client):
        svc = Mock(name="product_service")
        svc.get_recommendations.return_value = [product_payload()]

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/recommendations")

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_recommendations_parses_exclude(self, client):
        """`exclude=1,2,3` deve virar [1, 2, 3] para o serviço."""
        svc = Mock(name="product_service")
        svc.get_recommendations.return_value = []

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/recommendations?exclude=1,2,3&limit=4")

        assert response.status_code == 200
        svc.get_recommendations.assert_called_once_with([1, 2, 3], 4)

    def test_recommendations_ignores_garbage_in_exclude(self, client):
        """Ids inválidos não podem derrubar a chamada."""
        svc = Mock(name="product_service")
        svc.get_recommendations.return_value = []

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/recommendations?exclude=1,abc,3")

        assert response.status_code == 200
        svc.get_recommendations.assert_called_once_with([1, 3], 4)

    def test_recommendations_without_exclude(self, client):
        svc = Mock(name="product_service")
        svc.get_recommendations.return_value = []

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            client.get(f"{PREFIX}/recommendations")

        svc.get_recommendations.assert_called_once_with([], 4)

    def test_recommendations_empty_is_200(self, client):
        svc = Mock(name="product_service")
        svc.get_recommendations.return_value = []

        with patch("app.api.v1.products.get_product_service", return_value=svc):
            response = client.get(f"{PREFIX}/recommendations")

        assert response.status_code == 200
        assert response.json() == []

    def test_recommendations_invalid_limit(self, client):
        assert_validation_error(client.get(f"{PREFIX}/recommendations?limit=0"))
        assert_validation_error(client.get(f"{PREFIX}/recommendations?limit=51"))
