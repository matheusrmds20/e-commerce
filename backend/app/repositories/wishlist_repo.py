from datetime import datetime

from sqlalchemy.orm import Session

from app.models.wishlist import Wishlist
from app.repositories.base import BaseRepository


class WishlistRepository(BaseRepository[Wishlist]):
    def __init__(self, db: Session) -> None:
        super().__init__(Wishlist, db)


    def get_by_product_id(self, product_id: int) -> list[Wishlist]:
        return self.session.query(Wishlist).filter(Wishlist.product_id == product_id).all()

    def get_by_created_at(self, created_at: datetime) -> list[Wishlist]:
        return self.session.query(Wishlist).filter(Wishlist.created_at == created_at).all()

    def get_by_updated_at(self, updated_at: datetime) -> list[Wishlist]:
        return self.session.query(Wishlist).filter(Wishlist.updated_at == updated_at).all()
