from sqlalchemy.exc import IntegrityError

from app.api.exceptions import (
    CartAlreadyExistsException,
    CartItemNotFoundException,
    CartNotFoundException,
    ForbiddenException,
    InsufficientStockException,
    ProductNotFoundException,
    UserNotFoundException,
)
from app.models.cart import Cart
from app.repositories.cart_item_repo import CartItemRepository
from app.repositories.cart_repo import CartRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.user_repo import UserRepository
from app.schemas.cart import CartCreate, CartItemCreate, CartItemResponse

MAX_ADD_ITEM_TENTATIVAS = 2


class CartService:
    def __init__(self, db):
        self.cart_repo = CartRepository(db)
        self.cart_item_repo = CartItemRepository(db)
        self.product_repo = ProductRepository(db)
        self.user_repo = UserRepository(db)
        self.session = db


    def _update_cart(self, cart_item, quantity):
        cart_item.quantity = quantity

        self.session.flush()
        self.session.refresh(cart_item)
        return cart_item

    def _to_response(self, cart_item):
        """Materializa um ``CartItemResponse`` a partir do ORM ainda vivo.

        Usado nos fluxos que DELETAM o item antes de responder (remover, e
        ``update_item`` com quantidade 0). Devolver o ORM deletado faria o
        pydantic tentar lazy-load de ``product`` após o commit com a sessão
        expirada e dispararia ``DetachedInstanceError``. Capturamos tudo agora.
        """
        return CartItemResponse(
            id=cart_item.id,
            cart_id=cart_item.cart_id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            product=cart_item.product,
        )

    def _remove_item(self, cart_item):

        self.cart_item_repo.delete(cart_item)


    def get_by_user_id(self, user_id: int) -> dict:
        user = self.user_repo.get_by_id(user_id)

        if not user:
            raise UserNotFoundException(user_id=user_id)

        cart = user.cart

        if cart is None:
            raise CartNotFoundException()

        return cart

    def create(self, user_id: int) -> CartCreate:
        with self.session.begin():

            user = self.user_repo.get_by_id(user_id)

            if not user:
                raise UserNotFoundException(user_id=user_id)

            existing_cart = user.cart

            if existing_cart:
                raise CartAlreadyExistsException()

            cart = Cart(user_id=user_id)

            cart_created = self.cart_repo.create(cart)

            return cart_created

    def add_item(self, cart_id: int, user_id: int, product_id: int, quantity: int) -> CartItemCreate:

        for _ in range(MAX_ADD_ITEM_TENTATIVAS):
            try:
                with self.session.begin():

                    cart = self.cart_repo.get_by_id(cart_id)

                    if not cart:
                        raise CartNotFoundException()

                    if cart.user_id != user_id:
                        raise ForbiddenException(
                            "Este carrinho pertence a outro usuário.",
                            code="CART_FORBIDDEN",
                        )

                    product = self.product_repo.get_by_id_for_update(product_id)

                    if not product:
                        raise ProductNotFoundException()

                    cart_item = self.cart_item_repo.get_by_cart_and_product(cart_id, product_id)

                    quantidade_atual = cart_item.quantity if cart_item else 0
                    quantidade_total = quantidade_atual + quantity

                    if product.stock_qty < quantidade_total:
                        raise InsufficientStockException(
                            product.title, product.stock_qty
                        )

                    if cart_item:
                        return self._update_cart(cart_item, quantidade_total)

                    cart_item_added = self.cart_item_repo.add_item(cart_id, product_id, quantity)

                    return cart_item_added
            except IntegrityError as exc:
                ultimo_erro = exc

        raise ultimo_erro


    def update_item(self, cart_id: int, user_id: int, item_id: int, quantity: int):
        with self.session.begin():

            cart = self.cart_repo.get_by_id(cart_id)

            if not cart:
                raise CartNotFoundException()

            if cart.user_id != user_id:
                raise ForbiddenException(
                    "Este carrinho pertence a outro usuário.",
                    code="CART_FORBIDDEN",
                )

            cart_item = self.cart_item_repo.get_by_id(item_id)

            if not cart_item:
                raise CartItemNotFoundException()

            if quantity <= 0:

                resposta = self._to_response(cart_item)
                self.cart_item_repo.delete(cart_item)
                return resposta

            if quantity > cart_item.quantity:
                product = self.product_repo.get_by_id_for_update(cart_item.product_id)

                if product and product.stock_qty < quantity:
                    raise InsufficientStockException(
                        product.title, product.stock_qty
                    )

            self.cart_item_repo.update_quantity(cart_item, quantity)

            return cart_item



    def remove_item(self,cart_id: int, user_id: int, item_id: int):
        with self.session.begin():

            cart = self.cart_repo.get_by_id(cart_id)

            if not cart:
                raise CartNotFoundException()

            if cart.user_id != user_id:
                raise ForbiddenException(
                    "Este carrinho pertence a outro usuário.",
                    code="CART_FORBIDDEN",
                )

            cart_item = self.cart_item_repo.get_by_id(item_id)

            if not cart_item:
                raise CartItemNotFoundException()


            resposta = self._to_response(cart_item)
            self.cart_item_repo.delete(cart_item)
            return resposta

    def clear(self, cart_id: int, user_id: int):
        with self.session.begin():

            cart = self.cart_repo.get_by_id(cart_id)

            if not cart:
                raise CartNotFoundException()

            if cart.user_id != user_id:
                raise ForbiddenException(
                    "Este carrinho pertence a outro usuário.",
                    code="CART_FORBIDDEN",
                )

            items = self.cart_repo.get_with_items(cart_id)

            for item in items:
                self._remove_item(item)

            return cart
