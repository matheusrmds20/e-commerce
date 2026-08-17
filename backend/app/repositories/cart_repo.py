from typing import Any

from sqlalchemy.orm import Session, selectinload

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.repositories.base import BaseRepository


class CartRepository(BaseRepository[Cart]):
    def __init__(self, db: Session) -> None:
        super().__init__(Cart, db)

    def create_with_items(self, data, items) -> Cart:
        cart = data
        cart.cart_items = items


        self.session.add(cart)

        return cart

    def get_with_items(self, id: int) -> list[CartItem]:
        return self.session.query(CartItem).options(selectinload(CartItem.carts), selectinload(CartItem.product)).filter(CartItem.cart_id == id).all()
