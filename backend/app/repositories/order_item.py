from sqlalchemy.orm import Session

from app.models.order_item import OrderItem
from app.repositories.base import BaseRepository


class OrderItemRepository(BaseRepository[OrderItem]):
    def __init__(self, db: Session) -> None:
        super().__init__(OrderItem, db)


    def create_order_item(self, product_id: int, quantity: int, price: float) -> OrderItem:
        order_item = OrderItem(product_id=product_id, quantity=quantity, price=price)
        self.session.add(order_item)
        return order_item


    def update_quantity(self, item_id: int, quantity: int) -> OrderItem:
        order_item = self.get_by_id(item_id)

        if order_item is None:
            raise ValueError(f"No order item found with id {item_id}")

        order_item.quantity = quantity

        return order_item

    def delete_item(self, item_id: int) -> OrderItem:
        order_item = self.get_by_id(item_id)

        if order_item is not None:
            self.session.delete(order_item)

        return order_item
