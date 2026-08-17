from sqlalchemy.orm import Session

from app.api.exceptions import (
    BadRequestException,
    EmailAlreadyExistsException,
    UserNotFoundException,
)
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import MessageResponse
from app.schemas.user import (
    AdminUserCreate,
    CustomerUserCreate,
    UserResponse,
    UserUpdate,
)


class UserService:
    def __init__(self, db: Session) -> None:
        self.user_repo = UserRepository(db)
        self.session = db

    def _check_email_available(self, email: str, exclude_user_id: int | None = None) -> None:
        existing = self.user_repo.get_by_email(email)
        if existing is not None and existing.id != exclude_user_id:
            raise EmailAlreadyExistsException()

    def create(self, data: AdminUserCreate | CustomerUserCreate) -> UserResponse:
        with self.session.begin():

            self._check_email_available(data.email)

            user = self.user_repo.create(
                User(
                    email=data.email,
                    full_name=data.full_name,
                    role=data.role,
                    password_hash=hash_password(data.password),
                )
            )

            return user

    def get_by_id(self, user_id: int) -> UserResponse:
        user = self.user_repo.get_by_id(user_id)

        if user is None:
            raise UserNotFoundException(user_id=user_id)

        return user

    def get_by_email(self, email: str) -> UserResponse:
        user = self.user_repo.get_by_email(email)

        if user is None:
            raise UserNotFoundException(user_id=email)

        return user

    def update(self, user_id: int, data: UserUpdate) -> UserResponse:
        with self.session.begin():
            user = self.user_repo.get_by_id(user_id)

            if user is None:
                raise UserNotFoundException(user_id=user_id)

            self._check_email_available(data.email, exclude_user_id=user_id)



            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(user, field, value)

            user = self.user_repo.update(user)

            return user

    def change_password(self, user_id: int, current_password: str, new_password: str) -> MessageResponse:
        with self.session.begin():
            user = self.user_repo.get_by_id(user_id)

            if user is None:
                raise UserNotFoundException(user_id=user_id)

            if not verify_password(current_password, user.password_hash):
                raise BadRequestException(
                    "A senha atual informada está incorreta.", code="INVALID_CURRENT_PASSWORD"
                )

            self.user_repo.change_password(user_id, hash_password(new_password))

            return MessageResponse(message="Senha alterada com sucesso.")

    def deactivate(self, user_id: int) -> UserResponse:
        with self.session.begin():
            user = self.user_repo.get_by_id(user_id)

            if user is None:
                raise UserNotFoundException(user_id=user_id)


            user_deactivated = self.user_repo.deactivate(user_id)

            return user_deactivated
