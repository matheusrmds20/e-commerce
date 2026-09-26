import os
from unittest.mock import MagicMock, Mock, patch

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault(
    "SECRET_KEY",
    "test-secret-key-0123456789-0123456789-0123456789-0123456789",
)


@pytest.fixture
def db():
    return MagicMock(name="db")


@pytest.fixture
def user_repo():
    return Mock(name="user_repo")


@pytest.fixture
def product_repo():
    """Mock do ProductRepository com semântica de estoque real.

    - ``get_by_id_for_update`` (leitura com ``FOR UPDATE``) é um alias de
      ``get_by_id``: nos testes o banco é mockado e não há transação real, então
      o lock é irrelevante.
    - ``decrement_stock`` / ``restock`` **de fato alteram** ``stock_qty`` do
      produto recebido. Sem isso os testes de baixa de estoque passariam sem
      provar nada (um Mock que não muta o objeto esconde regressões).
    """
    repo = Mock(name="product_repo")
    repo.get_by_id_for_update.side_effect = lambda product_id: (
        repo.get_by_id(product_id)
    )

    def _decrement(product, quantity):
        if product.stock_qty < quantity:
            raise ValueError(
                f"Estoque insuficiente para baixa: disponível "
                f"{product.stock_qty}, solicitado {quantity}"
            )
        product.stock_qty -= quantity
        return product

    def _restock(product, quantity):
        product.stock_qty += quantity
        return product

    repo.decrement_stock.side_effect = _decrement
    repo.restock.side_effect = _restock
    return repo


@pytest.fixture
def category_repo():
    return Mock(name="category_repo")


@pytest.fixture
def coupon_repo():
    return Mock(name="coupon_repo")


@pytest.fixture
def cart_repo():
    return Mock(name="cart_repo")


@pytest.fixture
def cart_item_repo():
    return Mock(name="cart_item_repo")


@pytest.fixture
def address_repo():
    return Mock(name="address_repo")


@pytest.fixture
def review_repo():
    return Mock(name="review_repo")


@pytest.fixture
def wishlist_repo():
    return Mock(name="wishlist_repo")


@pytest.fixture
def user_coupon_repo():
    return Mock(name="user_coupon_repo")


@pytest.fixture
def order_repo():
    return Mock(name="order_repo")


@pytest.fixture
def order_item_repo():
    return Mock(name="order_item_repo")


@pytest.fixture
def auth_service(db, user_repo):
    with (
        patch("app.services.auth_service.UserRepository", return_value=user_repo),
        patch("app.services.auth_service.hash_password", return_value="hashed-password"),
        patch("app.services.auth_service.verify_password", return_value=True),
        patch("app.services.auth_service.create_access_token", return_value="access-token"),
    ):
        from app.services.auth_service import AuthService

        yield AuthService(db)


@pytest.fixture
def user_service(db, user_repo):
    with (
        patch("app.services.user_service.UserRepository", return_value=user_repo),
        patch("app.services.user_service.hash_password", return_value="hashed-password"),
        patch("app.services.user_service.verify_password", return_value=True),
    ):
        from app.services.user_service import UserService

        yield UserService(db)


@pytest.fixture
def product_service(db, product_repo, category_repo):
    with (
        patch("app.services.product_service.ProductRepository", return_value=product_repo),
        patch("app.services.product_service.CategoryRepository", return_value=category_repo),
    ):
        from app.services.product_service import ProductService

        yield ProductService(db)


@pytest.fixture
def category_service(db, category_repo):
    with (
        patch("app.services.category_service.CategoryRepository", return_value=category_repo),
    ):
        from app.services.category_service import CategoryService

        yield CategoryService(db)


@pytest.fixture
def coupon_service(db, coupon_repo, product_repo):
    with (
        patch("app.services.coupon_service.CouponRepository", return_value=coupon_repo),
        patch("app.services.coupon_service.ProductRepository", return_value=product_repo),
    ):
        from app.services.coupon_service import CouponService

        yield CouponService(db)


@pytest.fixture
def cart_service(db, cart_repo, cart_item_repo, product_repo, user_repo):
    with (
        patch("app.services.cart_service.CartRepository", return_value=cart_repo),
        patch("app.services.cart_service.CartItemRepository", return_value=cart_item_repo),
        patch("app.services.cart_service.ProductRepository", return_value=product_repo),
        patch("app.services.cart_service.UserRepository", return_value=user_repo),
    ):
        from app.services.cart_service import CartService

        yield CartService(db)


@pytest.fixture
def order_service(
    db,
    order_repo,
    order_item_repo,
    address_repo,
    coupon_repo,
    product_repo,
    user_repo,
    cart_repo,
    user_coupon_repo,
):
    with (
        patch("app.services.order_service.OrderRepository", return_value=order_repo),
        patch("app.services.order_service.OrderItemRepository", return_value=order_item_repo),
        patch("app.services.order_service.AddressRepository", return_value=address_repo),
        patch("app.services.order_service.CouponRepository", return_value=coupon_repo),
        patch("app.services.order_service.UserCouponRepository", return_value=user_coupon_repo),
        patch("app.services.order_service.ProductRepository", return_value=product_repo),
        patch("app.services.order_service.UserRepository", return_value=user_repo),
        patch("app.services.order_service.CartRepository", return_value=cart_repo),
    ):
        from app.services.order_service import OrderService

        yield OrderService(db)


@pytest.fixture
def address_service(db, address_repo, user_repo):
    with (
        patch("app.services.address_service.AddressRepository", return_value=address_repo),
        patch("app.services.address_service.UserRepository", return_value=user_repo),
    ):
        from app.services.address_service import AddressService

        yield AddressService(db)


@pytest.fixture
def review_service(db, review_repo, user_repo, product_repo):
    with (
        patch("app.services.review_service.ReviewRepository", return_value=review_repo),
        patch("app.services.review_service.UserRepository", return_value=user_repo),
        patch("app.services.review_service.ProductRepository", return_value=product_repo),
    ):
        from app.services.review_service import ReviewService

        yield ReviewService(db)


@pytest.fixture
def wishlist_service(db, wishlist_repo, user_repo, product_repo):
    with (
        patch("app.services.wishlist_service.WishlistRepository", return_value=wishlist_repo),
        patch("app.services.wishlist_service.UserRepository", return_value=user_repo),
        patch("app.services.wishlist_service.ProductRepository", return_value=product_repo),
    ):
        from app.services.wishlist_service import WishlistService

        yield WishlistService(db)


@pytest.fixture
def user_coupon_service(db, user_coupon_repo, user_repo, coupon_repo):
    with (
        patch("app.services.user_coupon_service.UserCouponRepository", return_value=user_coupon_repo),
        patch("app.services.user_coupon_service.UserRepository", return_value=user_repo),
        patch("app.services.user_coupon_service.CouponRepository", return_value=coupon_repo),
    ):
        from app.services.user_coupon_service import UserCouponService

        yield UserCouponService(db)
