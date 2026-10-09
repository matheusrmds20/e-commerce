
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

    def paginate_by_product_id(
        self, product_id: int, page: int, per_page: int
    ) -> tuple[list[Review], int]:
        """Avaliações de um produto com paginação no banco.

        Ordena por ``created_at`` desc (mais recentes primeiro) com desempate
        por ``id`` para a ordem ser estável entre páginas.
        """
        query = self.session.query(Review).filter(Review.product_id == product_id)
        total = query.count()
        items = (
            query.order_by(Review.created_at.desc(), Review.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    def paginate_by_user_id(
        self, user_id: int, page: int, per_page: int
    ) -> tuple[list[Review], int]:
        """Avaliações de um usuário com paginação no banco."""
        query = self.session.query(Review).filter(Review.user_id == user_id)
        total = query.count()
        items = (
            query.order_by(Review.created_at.desc(), Review.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total


