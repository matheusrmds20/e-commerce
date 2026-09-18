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

    def clear(self, cart_id: int) -> int:
        """Remove todos os itens de um carrinho, mantendo o carrinho.

        Usado no checkout (passo 18 da seção 8.1): depois de o pedido ser
        criado, a sacola precisa esvaziar, senão uma nova compra repetiria os
        mesmos itens.

        Devolve quantas linhas foram removidas. Usa `synchronize_session=False`
        porque a deleção em massa não precisa reconciliar objetos já carregados
        na sessão — evita um SELECT extra.
        """
        removidos = (
            self.session.query(CartItem)
            .filter(CartItem.cart_id == cart_id)
            .delete(synchronize_session=False)
        )
        return removidos
