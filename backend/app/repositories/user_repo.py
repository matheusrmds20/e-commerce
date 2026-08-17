
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session) -> None:
        super().__init__(User, db)

    def get_by_email(self, email: str) -> User | None:
        return self.session.query(User).filter(User.email == email).first()

    def change_password(self, user_id: int, password: str) -> User:
        self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(password_hash=password)
        )

    def deactivate(self, user_id: int) -> User:
        with self.session.begin():

            self.session.execute(
                update(User)
                .where(User.id == user_id)
                .values(is_active=False)
            )

            user = self.session.get(User, user_id)

        return user





