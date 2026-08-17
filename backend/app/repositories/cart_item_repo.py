
from sqlalchemy.orm import Session

from app.models.cart_item import CartItem
from app.repositories.base import BaseRepository


class CartItemRepository(BaseRepository[CartItem]):
    def __init__(self, db: Session) -> None:
        super().__init__(CartItem, db)

    def get_by_cart_and_product(self, cart_id: int, product_id: int) -> CartItem | None:

        return (
            self.session.query(CartItem)
            .filter(CartItem.cart_id == cart_id, CartItem.product_id == product_id)
            .first()
        )

    def add_item(self, cart_id: int, product_id: int, quantity: int) -> CartItem:

        cart_item = CartItem(cart_id=cart_id, product_id=product_id, quantity=quantity)


        self.session.add(cart_item)
        self.session.flush()
        self.session.refresh(cart_item)
        return cart_item






    def decrease_quantity(self, cart_item, quantity: int) -> CartItem:

        cart_item.quantity -= quantity

        self.session.add(cart_item)
        self.session.flush()
        self.session.refresh(cart_item)
        return cart_item

    def update_quantity(self, cart_item, quantity: int) -> CartItem:
        cart_item.quantity = quantity


        self.session.add(cart_item)
        self.session.flush()
        self.session.refresh(cart_item)
        return cart_item





    def delete(self, cart_item) -> None:


        self.session.delete(cart_item)
