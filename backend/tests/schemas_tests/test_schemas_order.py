import pytest
from pydantic import ValidationError

from app.schemas.order import OrderItemCreate


class TestOrderItemCreate:
    def test_valid(self):
        data = OrderItemCreate(product_id=1, quantity=1)

        assert data.quantity == 1

    def test_invalid_quantity(self):
        with pytest.raises(ValidationError):
            OrderItemCreate(product_id=1, quantity=0)
