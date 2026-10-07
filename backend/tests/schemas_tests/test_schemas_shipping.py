import pytest
from pydantic import ValidationError

from app.schemas.shipping import (
    ShippingApplyRequest,
    ShippingCalculateResponse,
    ShippingOffer,
)


class TestShippingOffer:
    def test_valid_complete(self):
        oferta = ShippingOffer(
            service_id="1",
            name="PAC",
            company_name="Correios",
            price=27.5,
            delivery_time=4,
            delivery_time_text="4 dias úteis",
        )
        assert oferta.service_id == "1"
        assert oferta.price == 27.5
        assert oferta.delivery_time == 4

    def test_optional_fields_default_none(self):
        oferta = ShippingOffer(service_id="2", name="SEDEX", price=40.0)
        assert oferta.company_name is None
        assert oferta.delivery_time is None
        assert oferta.delivery_time_text is None

    def test_requires_service_id(self):
        with pytest.raises(ValidationError):
            ShippingOffer(name="PAC", price=10.0)

    def test_requires_name(self):
        with pytest.raises(ValidationError):
            ShippingOffer(service_id="1", price=10.0)


class TestShippingCalculateResponse:
    def test_defaults(self):
        resp = ShippingCalculateResponse(order_id=7)
        assert resp.offers == []
        assert resp.best_offer_index is None
        assert resp.is_real is True

    def test_complete(self):
        resp = ShippingCalculateResponse(
            order_id=7,
            offers=[ShippingOffer(service_id="1", name="PAC", price=1.0)],
            best_offer_index=0,
            is_real=False,
        )
        assert resp.is_real is False


class TestShippingApplyRequest:
    def test_valid(self):
        req = ShippingApplyRequest(order_id=1, price=12.5)
        assert req.price == 12.5
        assert req.delivery_time is None

    def test_negative_price_invalid(self):
        with pytest.raises(ValidationError):
            ShippingApplyRequest(order_id=1, price=-1)

    def test_zero_price_ok(self):
        # frete gratuito/fallback é permitido
        req = ShippingApplyRequest(order_id=1, price=0)
        assert req.price == 0
