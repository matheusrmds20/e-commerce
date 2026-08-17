from typing import Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], db: Session) -> None:
        self.model = model
        self.session = db

    def create(self, data) -> ModelType:


        self.session.add(data)
        self.session.flush()
        self.session.refresh(data)
        return data

    def get_by_id(self, item_id: int) -> ModelType | None:
        return self.session.query(self.model).filter(self.model.id == item_id).first()

    def get_by_user_id(self, user_id: int) -> list[ModelType]:
        return self.session.query(self.model).filter(self.model.user_id == user_id).all()

    def get_all(self) -> list[ModelType]:
        return self.session.query(self.model).all()

    def update(self, item) -> ModelType:
        
        self.session.add(item)
        self.session.flush()
        self.session.refresh(item)
        return item

    def delete(self, item) -> ModelType | None:

        return self.session.delete(item)

    def count(self) -> int:
        return self.session.query(self.model).count()

    def paginate(self, page: int, per_page: int) -> tuple[list[ModelType], int]:
        total = self.count()
        items = (
            self.session.query(self.model)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total
