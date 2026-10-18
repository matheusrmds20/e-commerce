
from sqlalchemy.orm import Session, selectinload

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.user import User
from app.repositories.base import BaseRepository


class CartRepository(BaseRepository[Cart]):
    def __init__(self, db: Session) -> None:
        super().__init__(Cart, db)

    def create_with_items(self, data, items) -> Cart:
        cart = data
        cart.cart_items = items


        self.session.add(cart)

        return cart

    def get_by_user_id_cart_items(self, user_id: int) -> list[CartItem]:

        user = (
            self.session.query(User)
            .options(selectinload(User.cart))
            .filter(User.id == user_id)
            .first()
        )
        if user is None or user.cart is None:
            return []
        return self.get_with_items(user.cart.id)

    def get_with_items(self, id: int) -> list[CartItem]:
        return self.session.query(CartItem).options(selectinload(CartItem.carts), selectinload(CartItem.product)).filter(CartItem.cart_id == id).all()

    def clear(self, cart_id: int) -> int:

        removidos = (
            self.session.query(CartItem)
            .filter(CartItem.cart_id == cart_id)
            .delete(synchronize_session=False)
        )
        return removidos
