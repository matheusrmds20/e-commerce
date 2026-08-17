from app.models.cart import Cart
from app.repositories.cart_item_repo import CartItemRepository
from app.repositories.cart_repo import CartRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.user_repo import UserRepository
from app.schemas.cart import CartItemCreate, CartCreate


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


    def _remove_item(self, cart_item):

        self.cart_item_repo.delete(cart_item)
        

    def get_by_id(self, cart_id: int, user_id: int) -> dict:
        cart = self.cart_repo.get_by_id(cart_id)

        if not cart:
            raise ValueError(f"No cart found with id {cart_id}")

        if cart.user_id != user_id:
            raise ValueError("Cart is not owned by user")

        return cart

    def get_by_user_id(self, user_id: int) -> dict:
        user = self.user_repo.get_by_id(user_id)

        if not user:
            raise ValueError(f"No user found with id {user_id}")

        cart = user.cart

        if not cart:
            raise ValueError(f"No cart found with user_id {user_id}")

        return cart

    def get_with_items(self, cart_id: int, user_id: int) -> list:
        cart = self.cart_repo.get_by_id(cart_id)

        if not cart:
            raise ValueError(f"No cart found with id {cart_id}")

        if cart.user_id != user_id:
            raise ValueError("Cart is not owned by user")

        items = self.cart_repo.get_with_items(cart_id)

        if not items:
            raise ValueError(f"No items found in cart with id {cart_id}")

        return items


    def create(self, user_id: int) -> CartCreate:
        with self.session.begin():

            user = self.user_repo.get_by_id(user_id)

            if not user:
                raise ValueError(f"No user found with id {user_id}")

            existing_cart = user.cart

            if existing_cart:
                raise ValueError(f"User {user_id} already has a cart")

            cart = Cart(user_id=user_id)

            cart_created = self.cart_repo.create(cart)

            return cart_created

    def add_item(self, cart_id: int, user_id: int, product_id: int, quantity: int) -> CartItemCreate:
        with self.session.begin():


            cart = self.cart_repo.get_by_id(cart_id)

            if not cart:
                raise ValueError(f"No cart found with id {cart_id}")

            if cart.user_id != user_id:
                raise ValueError("Cart is not owned by user")

            product = self.product_repo.get_by_id(product_id)

            if not product:
                raise ValueError(f"No product found with id {product_id}")

            if product.stock_qty < quantity:
                raise ValueError(f"Insufficient stock for product {product_id}")

            cart_item = self.cart_item_repo.get_by_cart_and_product(cart_id, product_id)

            if cart_item:
                return self._update_cart(cart_item, cart_item.quantity + quantity)

            cart_item_added = self.cart_item_repo.add_item(cart_id, product_id, quantity)

            return cart_item_added


    def update_item(self, cart_id: int, user_id: int, item_id: int, quantity: int):
        with self.session.begin():

            cart = self.cart_repo.get_by_id(cart_id)

            if not cart:
                raise ValueError(f"No cart found with id {cart_id}")

            if cart.user_id != user_id:
                raise ValueError("Cart is not owned by user")

            cart_item = self.cart_item_repo.get_by_id(item_id)

            if not cart_item:
                raise ValueError(f"No cart item found with id {item_id}")
            

            self.cart_item_repo.update_quantity(cart_item, quantity)

            return cart_item

    def decrease_item(self, cart_id: int, user_id: int, item_id: int, quantity: int):
        with self.session.begin():

            cart = self.cart_repo.get_by_id(cart_id)

            if not cart:
                raise ValueError(f"No cart found with id {cart_id}")

            if cart.user_id != user_id:
                raise ValueError("Cart is not owned by user")

            cart_item = self.cart_item_repo.get_by_id(item_id)

            if not cart_item:
                raise ValueError(f"No cart item found with id {item_id}")


            self.cart_item_repo.decrease_quantity(cart_item, quantity)

            return cart_item


    def remove_item(self, cart_id: int, user_id: int, item_id: int):
        with self.session.begin():

            cart = self.cart_repo.get_by_id(cart_id)

            if not cart:
                raise ValueError(f"No cart found with id {cart_id}")

            if cart.user_id != user_id:
                raise ValueError("Cart is not owned by user")

            cart_item = self.cart_item_repo.get_by_id(item_id)

            if not cart_item:
                raise ValueError(f"No cart item found with id {item_id}")



            self.cart_item_repo.delete(cart_item)
            return cart_item

    def clear(self, cart_id: int, user_id: int):
        with self.session.begin():

            cart = self.cart_repo.get_by_id(cart_id)

            if not cart:
                raise ValueError(f"No cart found with id {cart_id}")

            if cart.user_id != user_id:
                raise ValueError("Cart is not owned by user")

            items = self.cart_repo.get_with_items(cart_id)

            for item in items:
                self._remove_item(item)

            return cart

    def delete(self, cart_id: int, user_id: int):
        with self.session.begin():

            cart = self.cart_repo.get_by_id(cart_id)

            if cart is None:
                raise ValueError(f"No cart found with id {cart_id}")

            if cart.user_id != user_id:
                raise ValueError("Cart is not owned by user")

            self.cart_repo.delete(cart)
            return cart

