from app.repositories.address_repo import AddressRepository as AddressRepository
from app.repositories.base import BaseRepository as BaseRepository
from app.repositories.cart_item_repo import CartItemRepository as CartItemRepository
from app.repositories.cart_repo import CartRepository as CartRepository
from app.repositories.category_repo import CategoryRepository as CategoryRepository
from app.repositories.coupon_repo import CouponRepository as CouponRepository
from app.repositories.order_item import OrderItemRepository as OrderItemRepository
from app.repositories.order_repo import OrderRepository as OrderRepository
from app.repositories.product_repo import ProductRepository as ProductRepository
from app.repositories.review_repo import ReviewRepository as ReviewRepository
from app.repositories.user_repo import UserRepository as UserRepository
from app.repositories.wishlist_repo import WishlistRepository as WishlistRepository

__all__ = [
    "AddressRepository",
    "BaseRepository",
    "CartItemRepository",
    "CartRepository",
    "CategoryRepository",
    "CouponRepository",
    "OrderItemRepository",
    "OrderRepository",
    "ProductRepository",
    "ReviewRepository",
    "UserRepository",
    "WishlistRepository",
]
