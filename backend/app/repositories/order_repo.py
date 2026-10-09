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
        return self.session.query(OrderItem).options(selectinload(OrderItem.orders)).filter(OrderItem.order_id == id).all()

    def get_with_items_products(self, id: int) -> list[OrderItem]:
        return self.session.query(OrderItem).options(selectinload(OrderItem.products)).filter(OrderItem.order_id == id).all()

    def get_by_user_id_eager(self, user_id: int) -> list[Order]:
        """Pedidos do usuário com os itens já carregados.

        Evita o N+1 do ``/orders/list``: sem o ``selectinload``, serializar
        ``OrderResponse.order_items`` disparava 1 SELECT por pedido. Aqui são
        2 queries fixas (pedidos + itens), não O(N).
        """
        return (
            self.session.query(Order)
            .options(selectinload(Order.order_items))
            .filter(Order.user_id == user_id)
            .order_by(Order.created_at.desc(), Order.id.desc())
            .all()
        )

    def paginate_by_user_id(
        self, user_id: int, page: int, per_page: int
    ) -> tuple[list[Order], int]:
        """Pedidos do usuário paginados no banco, com itens pré-carregados.

        ``selectinload`` embutido evita o N+1 na serialização de
        ``order_items``; o ``count`` roda sobre o mesmo filtro para o
        ``total_pages`` não mentir.
        """
        query = self.session.query(Order).filter(Order.user_id == user_id)
        total = query.count()
        items = (
            query.options(selectinload(Order.order_items))
            .order_by(Order.created_at.desc(), Order.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total
