from unittest.mock import patch

import pytest

from app.api.exceptions import (
    ForbiddenException,
    OrderNotFoundException,
    ShippingCalculationException,
)
from app.models.order import Order, OrderStatus
from app.services import shipping_service as mod


def make_order(**kwargs):
    fields = dict(
        id=1,
        user_id=1,
        address_id=1,
        subtotal=100.0,
        discount_amount=10.0,
        shipping_cost=0.0,
        total=90.0,
        status=OrderStatus.PENDING,
    )
    fields.update(kwargs)
    return Order(**fields)


def make_address(**kwargs):
    class _Address:
        def __init__(self, zip_code):
            self.zip_code = zip_code

    return _Address(kwargs.get("zip_code", "01310-100"))


def make_item(product=None, quantity=1, price=50.0):
    class _Item:
        def __init__(self):
            self.products = product
            self.quantity = quantity
            self.price = price

    return _Item()


def make_product(**kwargs):
    fields = dict(
        id=1,
        title="Livro",
        weight_kg=0.3,
        height_cm=17,
        width_cm=11,
        length_cm=15,
    )
    fields.update(kwargs)
    return type("_Product", (), fields)()


# Ajusta o módulo de settings para controlar a config de frete.
@pytest.fixture(autouse=True)
def _patch_settings():
    """Por padrão, sem token/CEP (fallback). Cada teste ajusta conforme precisa."""
    with patch.object(
        mod.settings,
        "MELHOR_ENVIO_API_TOKEN",
        "",
    ), patch.object(
        mod.settings,
        "MELHOR_ENVIO_ORIGIN_ZIP",
        "",
    ):
        yield


class TestOwnedOrder:
    def test_order_not_found(self, shipping_service, order_repo):
        order_repo.get_by_id.return_value = None
        with pytest.raises(OrderNotFoundException):
            shipping_service._get_owned_order(99, 1)

    def test_order_forbidden(self, shipping_service, order_repo):
        order_repo.get_by_id.return_value = make_order(user_id=2)
        with pytest.raises(ForbiddenException):
            shipping_service._get_owned_order(1, 1)


class TestCalculate:
    def test_not_configured_returns_fallback(self, shipping_service, order_repo, address_repo):
        order_repo.get_by_id.return_value = make_order()
        address_repo.get_by_id.return_value = make_address()

        res = shipping_service.calculate(1, 1)

        assert res["is_real"] is False
        assert res["offers"] == []
        assert "não configurado" in res["fallback_reason"]

    def test_product_without_dimensions_returns_fallback(
        self, shipping_service, order_repo, address_repo
    ):
        order_repo.get_by_id.return_value = make_order()
        address_repo.get_by_id.return_value = make_address()
        with patch.object(
            mod.settings, "MELHOR_ENVIO_API_TOKEN", "tok"
        ), patch.object(mod.settings, "MELHOR_ENVIO_ORIGIN_ZIP", "01001000"):
            shipping_service.order_repo.get_with_items_products.return_value = [
                make_item(product=make_product(weight_kg=None))
            ]
            res = shipping_service.calculate(1, 1)

        assert res["is_real"] is False
        assert "peso/dimensões" in res["fallback_reason"]

    def test_calculate_returns_best_offer(
        self, shipping_service, order_repo, address_repo, shipping_gateway
    ):
        order_repo.get_by_id.return_value = make_order()
        address_repo.get_by_id.return_value = make_address()
        shipping_service.order_repo.get_with_items_products.return_value = [
            make_item(product=make_product())
        ]
        # Duas ofertas; a segunda é a mais barata.
        shipping_gateway.calculate_shipping.return_value = [
            {"id": "1", "name": "PAC", "price": 30.0},
            {"id": "2", "name": "SEDEX", "custom_price": 12.0, "delivery_time": 3},
        ]
        with patch.object(
            mod.settings, "MELHOR_ENVIO_API_TOKEN", "tok"
        ), patch.object(mod.settings, "MELHOR_ENVIO_ORIGIN_ZIP", "01001000"):
            res = shipping_service.calculate(1, 1)

        assert res["is_real"] is True
        assert res["best_offer_index"] == 1
        assert res["offers"][1]["price"] == 12.0
        shipping_gateway.calculate_shipping.assert_called_once()

    def test_calculate_gateway_error_raises(
        self, shipping_service, order_repo, address_repo, shipping_gateway
    ):
        order_repo.get_by_id.return_value = make_order()
        address_repo.get_by_id.return_value = make_address()
        shipping_service.order_repo.get_with_items_products.return_value = [
            make_item(product=make_product())
        ]
        shipping_gateway.calculate_shipping.side_effect = RuntimeError("boom")
        with patch.object(
            mod.settings, "MELHOR_ENVIO_API_TOKEN", "tok"
        ), patch.object(mod.settings, "MELHOR_ENVIO_ORIGIN_ZIP", "01001000"):
            with pytest.raises(ShippingCalculationException):
                shipping_service.calculate(1, 1)


class TestApplyToOrder:
    def test_apply_updates_cost_and_total(self, shipping_service, order_repo):
        order = make_order(subtotal=100.0, discount_amount=10.0, total=90.0)
        order_repo.get_by_id.return_value = order

        res = shipping_service.apply_to_order(1, 1, price=12.5)

        assert res["shipping_cost"] == 12.5
        # total = subtotal - desconto + frete = 100 - 10 + 12.5 = 102.5
        assert res["total"] == 102.5
        assert res["status"] == "pending"

    def test_apply_with_status(self, shipping_service, order_repo):
        order = make_order()
        order_repo.get_by_id.return_value = order

        res = shipping_service.apply_to_order(
            1, 1, price=5.0, status=OrderStatus.PROCESSING
        )

        assert order.status == OrderStatus.PROCESSING
        assert res["status"] == "processing"


class TestSubmitOrder:
    def test_normalize_offer_custom_price(self, shipping_service):
        of = shipping_service._normalize_offer(
            {
                "id": "1",
                "name": "PAC",
                "company": {"name": "Correios"},
                "price": 40.0,
                "custom_price": 27.5,
                "delivery_time": 5,
                "custom_delivery_time": 3,
            }
        )
        assert of["price"] == 27.5
        assert of["delivery_time"] == 3
        assert of["company_name"] == "Correios"

    def test_normalize_offer_fallback_price(self, shipping_service):
        of = shipping_service._normalize_offer(
            {"id": "1", "name": "PAC", "price": 40.0}
        )
        assert of["price"] == 40.0
        assert of["delivery_time"] is None

    def test_best_offer_index(self, shipping_service):
        ofertas = [
            {"price": 30.0},
            {"price": 12.0},
            {"price": 20.0},
        ]
        assert shipping_service._best_offer_index(ofertas) == 1

    def test_normalize_zip(self, shipping_service):
        assert shipping_service._normalize_zip("01310-100") == "01310100"
