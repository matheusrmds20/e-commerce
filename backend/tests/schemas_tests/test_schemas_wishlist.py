from app.schemas.wishlist import WishlistCreate


class TestWishlistCreate:
    def test_valid(self):
        data = WishlistCreate(product_id=1)

        assert data.product_id == 1
