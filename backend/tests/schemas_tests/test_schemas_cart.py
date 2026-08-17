import pytest
from pydantic import ValidationError

from app.schemas.cart import CartItemCreate


class TestCartItemCreate:
    def test_valid(self):
        data = CartItemCreate(product_id=1, quantity=2)

        assert data.quantity == 2

    def test_invalid_quantity(self):
        with pytest.raises(ValidationError):
            CartItemCreate(product_id=1, quantity=0)
