import pytest
from pydantic import ValidationError

from app.schemas.category import CategoryCreate


class TestCategoryCreate:
    def test_valid(self):
        data = CategoryCreate(name="Ficção", slug="ficcao")

        assert data.is_active is True

    def test_short_name(self):
        with pytest.raises(ValidationError):
            CategoryCreate(name="ab", slug="ficcao")
