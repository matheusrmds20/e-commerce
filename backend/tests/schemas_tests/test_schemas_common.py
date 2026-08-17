import pytest
from pydantic import ValidationError

from app.schemas.common import PaginationParams


class TestPaginationParams:
    def test_valid(self):
        data = PaginationParams(page=1, per_page=20)

        assert data.per_page == 20

    def test_invalid_per_page(self):
        with pytest.raises(ValidationError):
            PaginationParams(per_page=101)

    def test_invalid_page(self):
        with pytest.raises(ValidationError):
            PaginationParams(page=0)
