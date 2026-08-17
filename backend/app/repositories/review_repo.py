
from sqlalchemy.orm import Session

from app.models.review import Review
from app.repositories.base import BaseRepository


class ReviewRepository(BaseRepository[Review]):
    def __init__(self, db: Session) -> None:
        super().__init__(Review, db)

    def get_by_user_id_and_product_id(self, user_id: int, product_id: int) -> Review | None:
        return self.session.query(Review).filter(
            Review.user_id == user_id, Review.product_id == product_id
        ).first()

    def get_by_product_id(self, product_id: int) -> list[Review]:
        return self.session.query(Review).filter(Review.product_id == product_id).all()

    def get_by_rating(self, rating: int) -> list[Review]:
        return self.session.query(Review).filter(Review.rating == rating).all()


