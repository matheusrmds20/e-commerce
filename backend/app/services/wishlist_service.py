from datetime import datetime

from app.models.wishlist import Wishlist
from app.repositories.product_repo import ProductRepository
from app.repositories.user_repo import UserRepository
from app.repositories.wishlist_repo import WishlistRepository


class WishlistService:
    def __init__(self, db):
        self.repo = WishlistRepository(db)
        self.user_repo = UserRepository(db)
        self.product_repo = ProductRepository(db)
        self.session = db

    def get_by_id(self, wishlist_id: int, user_id: int) -> dict:
        wishlist_item = self.repo.get_by_id(wishlist_id)

        if wishlist_item is None:
            raise ValueError(f"No wishlist item found with id {wishlist_id}")

        if wishlist_item.user_id != user_id:
            raise ValueError("Wishlist item is not owned by user")

        return wishlist_item

    def get_by_user_id(self, user_id: int) -> list:
        user = self.user_repo.get_by_id(user_id)

        if user is None:
            raise ValueError(f"No user found with id {user_id}")

        wishlist_items = user.wishlist_items

        if not wishlist_items:
            raise ValueError(f"No wishlist items found with user_id {user_id}")

        return wishlist_items

    def get_by_product_id(self, product_id: int) -> list:
        product = self.product_repo.get_by_id(product_id)

        if product is None:
            raise ValueError(f"No product found with id {product_id}")

        wishlist_items = self.repo.get_by_product_id(product_id)

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

    def get_all(self) -> list:
        wishlist_items = self.repo.get_all()

        if not wishlist_items:
            raise ValueError("No wishlist items found")

        return wishlist_items



    def create(self, user_id: int, data) -> dict:
        with self.session.begin():

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

    def update(self, wishlist_id: int, user_id: int, data) -> dict:
        with self.session.begin():

            wishlist_item = self.repo.get_by_id(wishlist_id)

            if wishlist_item is None:
                raise ValueError(f"No wishlist item found with id {wishlist_id}")

            if wishlist_item.user_id != user_id:
                raise ValueError("Wishlist item is not owned by user")

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

    def delete(self, wishlist_id: int, user_id: int) -> dict:
        with self.session.begin():

            wishlist_item = self.repo.get_by_id(wishlist_id)

            if wishlist_item is None:
                raise ValueError(f"No wishlist item found with id {wishlist_id}")

            if wishlist_item.user_id != user_id:
                raise ValueError("Wishlist item is not owned by user")

            self.repo.delete(wishlist_item)
            return wishlist_item

