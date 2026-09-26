from fastapi import APIRouter
from app.api.v1.categories import category_router
from app.api.v1.users import user_router
from app.api.v1.products import product_router
from app.api.v1.orders import order_router
from app.api.v1.cart import cart_router
from app.api.v1.addresses import address_router
from app.api.v1.coupons import coupon_router
from app.api.v1.wishlist import wishlist_router
from app.api.v1.auth import auth_router
from app.api.v1.reviews import review_router
from app.api.v1.admin import admin_router
from app.api.v1.user_coupons import user_coupon_router

router = APIRouter()

router.include_router(category_router, prefix="/categories", tags=["categories"])
router.include_router(user_router, prefix="/users", tags=["users"])
router.include_router(product_router, prefix="/products", tags=["products"])
router.include_router(order_router, prefix="/orders", tags=["orders"])
router.include_router(cart_router, prefix="/cart", tags=["cart"])
router.include_router(address_router, prefix="/addresses", tags=["addresses"])
router.include_router(coupon_router, prefix="/coupons", tags=["coupons"])
router.include_router(wishlist_router, prefix="/wishlists", tags=["wishlists"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(review_router, prefix="/reviews", tags=["reviews"])
router.include_router(admin_router, prefix="/admin", tags=["admin"])
router.include_router(user_coupon_router, prefix="/user-coupons", tags=["user-coupons"])
