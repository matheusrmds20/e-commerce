from datetime import datetime

from app.models.user import User, UserRole
from app.models.wishlist import Wishlist
from app.repositories.product_repo import ProductRepository
from app.repositories.user_repo import UserRepository
from app.repositories.wishlist_repo import WishlistRepository


class WishlistService:
    """Regras da lista de desejos.

    SEGURANÇA: o dono da wishlist NÃO vem mais da query string (`user_id`), e
    sim do usuário autenticado (`current_user`, resolvido do token pela rota).
    Um cliente comum só enxerga/altera a própria wishlist; administradores
    podem operar sobre qualquer usuário. Qualquer violação vira
    ``WishlistForbiddenException`` na camada de API.
    """

    def __init__(self, db):
        self.repo = WishlistRepository(db)
        self.user_repo = UserRepository(db)
        self.product_repo = ProductRepository(db)
        self.session = db

    @staticmethod
    def _is_admin(current_user: User) -> bool:
        return current_user.role == UserRole.ADMIN

    def _ensure_owner_or_admin(self, current_user: User, user_id: int) -> None:
        """Garante que o autenticado só acesse a própria wishlist (ou seja admin)."""
        if self._is_admin(current_user):
            return
        if current_user.id != user_id:
            raise ValueError("Wishlist item is not owned by user")

    def get_by_id(self, wishlist_id: int, current_user: User) -> dict:
        wishlist_item = self.repo.get_by_id(wishlist_id)

        if wishlist_item is None:
            raise ValueError(f"No wishlist item found with id {wishlist_id}")

        self._ensure_owner_or_admin(current_user, wishlist_item.user_id)

        return wishlist_item

    def get_by_user_id(
        self, current_user: User, user_id: int | None = None
    ) -> list:
        """Lista a wishlist do usuário.

        Sem ``user_id`` devolve a do próprio autenticado. Com ``user_id``
        diferente, só administradores são aceitos.
        """
        alvo = current_user.id if user_id is None else user_id
        self._ensure_owner_or_admin(current_user, alvo)

        user = self.user_repo.get_by_id(alvo)

        if user is None:
            raise ValueError(f"No user found with id {alvo}")

        wishlist_items = user.wishlist_items

        if not wishlist_items:
            raise ValueError(f"No wishlist items found with user_id {alvo}")

        return wishlist_items

    def get_by_product_id(self, product_id: int, current_user: User) -> list:
        """Itens de wishlist de um produto.

        Clientes comuns recebem apenas o próprio item (se existir); admins
        recebem todos. Assim o endpoint serve ao "já está nos desejos?" do
        detalhe do produto sem vazar wishlists alheias.
        """
        product = self.product_repo.get_by_id(product_id)

        if product is None:
            raise ValueError(f"No product found with id {product_id}")

        wishlist_items = self.repo.get_by_product_id(product_id)

        if not self._is_admin(current_user):
            wishlist_items = [
                item
                for item in wishlist_items
                if item.user_id == current_user.id
            ]

        if not wishlist_items:
            raise ValueError(f"No wishlist items found with product_id {product_id}")

        return wishlist_items

    def get_by_created_at(self, created_at: datetime) -> list:
        wishlist_items = self.repo.get_by_created_at(created_at)

        if not wishlist_items:
            raise ValueError(f"No wishlist items found with created_at {created_at}")

        return wishlist_items

    def get_by_updated_at(self, updated_at: datetime) -> list:
        wishlist_items = self.repo.get_by_updated_at(updated_at)

        if not wishlist_items:
            raise ValueError(f"No wishlist items found with updated_at {updated_at}")

        return wishlist_items

    def get_all(self, current_user: User) -> list:
        if not self._is_admin(current_user):
            raise ValueError("Admin permission required to list all wishlists")

        wishlist_items = self.repo.get_all()

        if not wishlist_items:
            raise ValueError("No wishlist items found")

        return wishlist_items

    def create(self, data, current_user: User) -> dict:
        with self.session.begin():

            user_id = current_user.id

            user = self.user_repo.get_by_id(user_id)

            if user is None:
                raise ValueError(f"No user found with id {user_id}")

            product = self.product_repo.get_by_id(data.product_id)

            if product is None:
                raise ValueError(f"No product found with id {data.product_id}")

            existing_items = self.repo.get_by_user_id(user_id)

            for existing_item in existing_items:
                if existing_item.product_id == data.product_id:
                    raise ValueError(
                        f"User {user_id} already has product {data.product_id} "
                        f"in wishlist"
                    )

            wishlist_item = self.repo.create(
                Wishlist(
                    user_id=user_id,
                    product_id=data.product_id,
                )
            )

            return wishlist_item

    def update(self, wishlist_id: int, data, current_user: User) -> dict:
        with self.session.begin():

            wishlist_item = self.repo.get_by_id(wishlist_id)

            if wishlist_item is None:
                raise ValueError(f"No wishlist item found with id {wishlist_id}")

            self._ensure_owner_or_admin(current_user, wishlist_item.user_id)

            user_id = wishlist_item.user_id

            if data.product_id is not None:
                product = self.product_repo.get_by_id(data.product_id)

                if product is None:
                    raise ValueError(f"No product found with id {data.product_id}")

                existing_items = self.repo.get_by_user_id(user_id)

                for existing_item in existing_items:
                    if (existing_item.product_id == data.product_id
                            and existing_item.id != wishlist_id):
                        raise ValueError(
                            f"User {user_id} already has product {data.product_id} "
                            f"in wishlist"
                        )

            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(wishlist_item, field, value)

            self.repo.update(wishlist_item)

            return wishlist_item

    def delete(self, wishlist_id: int, current_user: User) -> dict:
        with self.session.begin():

            wishlist_item = self.repo.get_by_id(wishlist_id)

            if wishlist_item is None:
                raise ValueError(f"No wishlist item found with id {wishlist_id}")

            self._ensure_owner_or_admin(current_user, wishlist_item.user_id)

            self.repo.delete(wishlist_item)
            return wishlist_item
