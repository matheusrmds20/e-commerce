import pytest
from pydantic import ValidationError

from app.schemas.product import ProductCreate, ProductUpdate


class TestProductSchemas:
    def valid_payload(self, **kwargs):
        fields = dict(
            category_id=1,
            title="Livro",
            slug="livro",
            description="Descrição",
            price=10.0,
            author="Autor",
            stock_qty=5,
        )
        fields.update(kwargs)
        return fields

    def test_valid(self):
        data = ProductCreate(**self.valid_payload())

        assert data.price == 10.0

    @pytest.mark.parametrize("price", [-1.0, -0.01])
    def test_negative_price(self, price):
        with pytest.raises(ValidationError):
            ProductCreate(**self.valid_payload(price=price))

    def test_discount_out_of_range(self):
        with pytest.raises(ValidationError):
            ProductCreate(**self.valid_payload(discount_pct=101))

    def test_pages_invalid(self):
        with pytest.raises(ValidationError):
            ProductCreate(**self.valid_payload(pages=0))

    def test_update_partial(self):
        data = ProductUpdate(price=20.0)

        assert data.price == 20.0
        assert data.title is None

    def test_update_invalid_year(self):
        with pytest.raises(ValidationError):
            ProductUpdate(publication_year=999)
