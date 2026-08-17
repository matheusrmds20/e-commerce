from sqlalchemy.orm import Session

from app.api.exceptions import (
    EmailAlreadyExistsException,
    InactiveUserException,
    InvalidCredentialsException,
    UserNotFoundException,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, TokenResponse


class AuthService:
    def __init__(self, db: Session) -> None:
        self.user_repo = UserRepository(db)
        self.session = db

    def register(self, data) -> AuthResponse:
        with self.session.begin():

            email_already_exists = self.user_repo.get_by_email(data.email)

            if email_already_exists is not None:
                raise EmailAlreadyExistsException()

            new_user = self.user_repo.create(
                User(
                    email=data.email,
                    full_name=data.full_name,
                    password_hash=hash_password(data.password),
                )
            )

            return new_user


    def login(self, data) -> TokenResponse:
        user = self.user_repo.get_by_email(data.email)
        
        if user is None or not verify_password(data.password, user.password_hash):
            raise InvalidCredentialsException()

        if not user.is_active:
            raise InactiveUserException()

        access_token = create_access_token({"sub": str(user.id)})
        return TokenResponse(access_token=access_token)

    def me(self, user: User) -> AuthResponse:
        if user is None:
            raise UserNotFoundException()
        return user
