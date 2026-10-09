from sqlalchemy.orm import Session

from app.api.exceptions import (
    BadRequestException,
    EmailAlreadyExistsException,
    ForbiddenException,
    InsufficientPermissionException,
    UserNotFoundException,
)
from app.core.security import hash_password, verify_password
from app.db.transaction import transacao
from app.models.user import User, UserRole
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

    def _ensure_owner_or_admin(self, current_user: User, user_id: int) -> None:
        """Garante que o usuário autenticado só acesse os próprios dados.

        Administradores podem operar sobre qualquer usuário. Qualquer outra
        tentativa vira 403 ``USER_FORBIDDEN``.
        """
        if current_user.role == UserRole.ADMIN:
            return
        if current_user.id != user_id:
            raise ForbiddenException(
                "Você não tem permissão para acessar os dados de outro usuário.",
                code="USER_FORBIDDEN",
            )

    def _ensure_admin(self, current_user: User) -> None:
        """Restringe a operação a administradores (403 ``INSUFFICIENT_PERMISSION``)."""
        if current_user.role != UserRole.ADMIN:
            raise InsufficientPermissionException()

    def create(
        self, data: AdminUserCreate | CustomerUserCreate, current_user: User
    ) -> UserResponse:
        # `transacao` evita o InvalidRequestError quando a sessão já iniciou
        # transação ao ler atributos de `current_user` (autobegin).
        with transacao(self.session):
            self._ensure_admin(current_user)

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

    def get_by_id(self, user_id: int, current_user: User) -> UserResponse:
        self._ensure_admin(current_user)
        user = self.user_repo.get_by_id(user_id)

        if user is None:
            raise UserNotFoundException(user_id=user_id)

        return user

    def get_by_email(self, email: str, current_user: User) -> UserResponse:
        self._ensure_admin(current_user)
        user = self.user_repo.get_by_email(email)

        if user is None:
            raise UserNotFoundException(user_id=email)

        return user

    def update(
        self, user_id: int, data: UserUpdate, current_user: User
    ) -> UserResponse:
        # `transacao` reaproveita a transação já aberta pelo autobegin (ex.: ao
        # ler atributos de `current_user`), evitando o
        # "A transaction is already begun on this Session".
        with transacao(self.session):
            self._ensure_owner_or_admin(current_user, user_id)
            user = self.user_repo.get_by_id(user_id)

            if user is None:
                raise UserNotFoundException(user_id=user_id)

            self._check_email_available(data.email, exclude_user_id=user_id)

            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(user, field, value)

            user = self.user_repo.update(user)

            return user

    def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
        current_user: User,
    ) -> MessageResponse:
        with transacao(self.session):
            self._ensure_owner_or_admin(current_user, user_id)
            user = self.user_repo.get_by_id(user_id)

            if user is None:
                raise UserNotFoundException(user_id=user_id)

            if not verify_password(current_password, user.password_hash):
                raise BadRequestException(
                    "A senha atual informada está incorreta.", code="INVALID_CURRENT_PASSWORD"
                )

            self.user_repo.change_password(user_id, hash_password(new_password))

            return MessageResponse(message="Senha alterada com sucesso.")

    def deactivate(self, user_id: int, current_user: User) -> UserResponse:
        with transacao(self.session):
            self._ensure_owner_or_admin(current_user, user_id)
            user = self.user_repo.get_by_id(user_id)

            if user is None:
                raise UserNotFoundException(user_id=user_id)

            user_deactivated = self.user_repo.deactivate(user_id)

            return user_deactivated
