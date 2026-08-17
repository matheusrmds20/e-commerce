from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.coupon import CouponCreate


def future():
    return datetime.now() + timedelta(days=1)


class TestCouponCreate:
    def test_valid(self):
        data = CouponCreate(code="PROMO", discount_value=10.0, valid_until=future())

        assert data.code == "PROMO"

    def test_negative_discount(self):
        with pytest.raises(ValidationError):
            CouponCreate(code="PROMO", discount_value=-1.0, valid_until=future())

    def test_short_code(self):
        with pytest.raises(ValidationError):
            CouponCreate(code="ab", discount_value=10.0, valid_until=future())
