from sqlalchemy.orm import Session, selectinload

from app.models.order import Order
from app.models.order_item import OrderItem
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    def __init__(self, db: Session) -> None:
        super().__init__(Order, db)

    def create_with_items(self, data, items: list[OrderItem]) -> Order:
        order = data
        order.order_items = items

        self.session.add(order)
        return order

    def get_with_items(self, id: int) -> list[OrderItem]:
        return self.session.query(OrderItem).options(selectinload(OrderItem.order)).filter(OrderItem.order_id == id).all()
