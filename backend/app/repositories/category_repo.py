
from sqlalchemy.orm import Session

from app.models.category import Category
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    def __init__(self, db: Session) -> None:
        super().__init__(Category, db)

    def get_by_name(self, name: str) -> Category | None:
        return self.session.query(Category).filter(Category.name == name).first()

    def get_by_slug(self, slug: str) -> Category | None:
        return self.session.query(Category).filter(Category.slug == slug).first()


