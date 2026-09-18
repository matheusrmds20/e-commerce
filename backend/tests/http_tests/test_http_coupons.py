"""Testes HTTP da rota /api/v1/coupons.

Sucesso: 201/200 com payloads válidos (criação, listagem, buscas por id/código/
produto/validade/uso/tipo/valor e update/delete).
Erros: validação 422, cupom/produto inexistente 404 e código duplicado 409.

NOTA: o CouponService real lança ``ValueError`` em vez das exceções de domínio
— em produção esses erros viram 500. Ver RELATORIO_TESTES_HTTP.md.
"""
from unittest.mock import Mock, patch

from helpers import assert_error, assert_validation_error, coupon_payload

from app.api.exceptions import (
    ConflictException,
    NotFoundException,
    ProductNotFoundException,
)

PREFIX = "/api/v1/coupons"

CREATE_OK = {
    "code": "PROMO10",
    "discount_type": "percentage",
    "discount_value": 10.0,
    "valid_until": "2025-12-31T23:59:59",
}


class TestCreateCoupon:
    def test_create_success(self, client):
        svc = Mock(name="coupon_service")
        svc.create.return_value = coupon_payload()

        with patch("app.api.v1.coupons.get_coupon_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert response.status_code == 201
        body = response.json()
        assert body["code"] == "PROMO10"
        assert body["discount_type"] == "percentage"
        assert body["discount_value"] == 10.0

    def test_create_duplicate_code(self, client):
        svc = Mock(name="coupon_service")
        svc.create.side_effect = ConflictException(
            "Coupon with code 'PROMO10' already exists", code="DUPLICATE_COUPON"
        )

        with patch("app.api.v1.coupons.get_coupon_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json=CREATE_OK)

        assert_error(response, 409, "DUPLICATE_COUPON")

    def test_create_product_not_found(self, client):
        svc = Mock(name="coupon_service")
        svc.create.side_effect = ProductNotFoundException()

        with patch("app.api.v1.coupons.get_coupon_service", return_value=svc):
            response = client.post(f"{PREFIX}/create", json={**CREATE_OK, "product_id": 999})

        assert_error(response, 404, "PRODUCT_NOT_FOUND")

    def test_create_short_code(self, client):
        response = client.post(f"{PREFIX}/create", json={**CREATE_OK, "code": "ab"})
        assert_validation_error(response)

    def test_create_negative_discount_value(self, client):
        response = client.post(f"{PREFIX}/create", json={**CREATE_OK, "discount_value": -5})
        assert_validation_error(response)

    def test_create_invalid_discount_type(self, client):
        response = client.post(f"{PREFIX}/create", json={**CREATE_OK, "discount_type": "total"})
        assert_validation_error(response)

    def test_create_missing_valid_until(self, client):
        payload = {k: v for k, v in CREATE_OK.items() if k != "valid_until"}
        response = client.post(f"{PREFIX}/create", json=payload)
        assert_validation_error(response)


class TestListCoupons:
    def test_list_success(self, client):
        svc = Mock(name="coupon_service")
        svc.get_all.return_value = [coupon_payload(), coupon_payload(id=2, code="PROMO20")]

        with patch("app.api.v1.coupons.get_coupon_service", return_value=svc):
            response = client.get(f"{PREFIX}/list")

        assert response.status_code == 200
        assert len(response.json()) == 2


class TestGetCoupon:
    def test_get_by_id_success(self, client):
        svc = Mock(name="coupon_service")
        svc.get_by_id.return_value = coupon_payload()

        with patch("app.api.v1.coupons.get_coupon_service", return_value=svc):
            response = client.get(f"{PREFIX}/get/1")

        assert response.status_code == 200
        assert response.json()["id"] == 1

    def test_get_by_id_not_found(self, client):
        svc = Mock(name="coupon_service")
        svc.get_by_id.side_effect = NotFoundException(
            "No coupon found with id 999", code="COUPON_NOT_FOUND"
        )

        with patch("app.api.v1.coupons.get_coupon_service", return_value=svc):
            response = client.get(f"{PREFIX}/get/999")

        assert_error(response, 404, "COUPON_NOT_FOUND")

    def test_get_by_code_success(self, client):
        svc = Mock(name="coupon_service")
        svc.get_by_code.return_value = coupon_payload()

        with patch("app.api.v1.coupons.get_coupon_service", return_value=svc):
            response = client.get(f"{PREFIX}/code/PROMO10")

        assert response.status_code == 200

    def test_get_by_product_id_success(self, client):
        svc = Mock(name="coupon_service")
        svc.get_by_product_id.return_value = [coupon_payload()]

        with patch("app.api.v1.coupons.get_coupon_service", return_value=svc):
            response = client.get(f"{PREFIX}/product/1")

        assert response.status_code == 200
        assert len(response.json()) == 1


class TestCouponFilters:
    def test_get_by_valid_until(self, client):
        svc = Mock(name="coupon_service")
        svc.get_by_valid_until.return_value = [coupon_payload()]

        with patch("app.api.v1.coupons.get_coupon_service", return_value=svc):
            response = client.get(f"{PREFIX}/valid-until/2025-12-31T00:00:00")

        assert response.status_code == 200

    def test_get_by_max_uses(self, client):
        svc = Mock(name="coupon_service")
        svc.get_by_max_uses.return_value = [coupon_payload()]

        with patch("app.api.v1.coupons.get_coupon_service", return_value=svc):
            response = client.get(f"{PREFIX}/max-uses/100")

        assert response.status_code == 200

    def test_get_by_discount_type(self, client):
        svc = Mock(name="coupon_service")
        svc.get_by_discount_type.return_value = [coupon_payload()]

        with patch("app.api.v1.coupons.get_coupon_service", return_value=svc):
            response = client.get(f"{PREFIX}/discount-type/percentage")

        assert response.status_code == 200

    def test_get_by_discount_value(self, client):
        svc = Mock(name="coupon_service")
        svc.get_by_discount_value.return_value = [coupon_payload()]

        with patch("app.api.v1.coupons.get_coupon_service", return_value=svc):
            response = client.get(f"{PREFIX}/discount-value/10.0")

        assert response.status_code == 200

    def test_get_by_min_purchase(self, client):
        svc = Mock(name="coupon_service")
        svc.get_by_min_purchase.return_value = [coupon_payload()]

        with patch("app.api.v1.coupons.get_coupon_service", return_value=svc):
            response = client.get(f"{PREFIX}/min-purchase/50.0")

        assert response.status_code == 200

    def test_get_by_max_discount(self, client):
        svc = Mock(name="coupon_service")
        svc.get_by_max_discount.return_value = [coupon_payload()]

        with patch("app.api.v1.coupons.get_coupon_service", return_value=svc):
            response = client.get(f"{PREFIX}/max-discount/30.0")

        assert response.status_code == 200


class TestUpdateCoupon:
    def test_update_success(self, client):
        svc = Mock(name="coupon_service")
        svc.update.return_value = coupon_payload(discount_value=15.0)

        with patch("app.api.v1.coupons.get_coupon_service", return_value=svc):
            response = client.patch(f"{PREFIX}/update/1", json={"discount_value": 15.0})

        assert response.status_code == 200
        assert response.json()["discount_value"] == 15.0

    def test_update_invalid_discount_value(self, client):
        response = client.patch(f"{PREFIX}/update/1", json={"discount_value": -1})
        assert_validation_error(response)

    def test_update_short_code(self, client):
        response = client.patch(f"{PREFIX}/update/1", json={"code": "ab"})
        assert_validation_error(response)


class TestDeleteCoupon:
    def test_delete_success(self, client):
        svc = Mock(name="coupon_service")
        svc.delete.return_value = coupon_payload()

        with patch("app.api.v1.coupons.get_coupon_service", return_value=svc):
            response = client.delete(f"{PREFIX}/delete/1")

        assert response.status_code == 200
        assert response.json()["id"] == 1

    def test_delete_not_found(self, client):
        svc = Mock(name="coupon_service")
        svc.delete.side_effect = NotFoundException(
            "No coupon found with id 999", code="COUPON_NOT_FOUND"
        )

        with patch("app.api.v1.coupons.get_coupon_service", return_value=svc):
            response = client.delete(f"{PREFIX}/delete/999")

        assert_error(response, 404, "COUPON_NOT_FOUND")
