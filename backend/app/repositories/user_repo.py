
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

    def deactivate(self, user_id: int) -> User | None:
        """Marca o usuário como inativo (soft delete).

        NÃO abre transação própria: quem orquestra é o service, que já está
        dentro de um ``with session.begin()``. Abrir um segundo ``begin()``
        aqui lançava ``InvalidRequestError: A transaction is already begun``
        (SQLAlchemy 2.0, autocommit=False) e quebrava o
        ``DELETE /users/delete/{id}``. Um repositório não deve gerenciar
        fronteira de transação — apenas o service.
        """
        self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_active=False)
        )

        return self.session.get(User, user_id)





