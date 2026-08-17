import pytest
from pydantic import ValidationError

from app.schemas.review import ReviewCreate


class TestReviewCreate:
    def test_valid(self):
        data = ReviewCreate(product_id=1, rating=5)

        assert data.rating == 5

    @pytest.mark.parametrize("rating", [0, 6])
    def test_invalid_rating(self, rating):
        with pytest.raises(ValidationError):
            ReviewCreate(product_id=1, rating=rating)
