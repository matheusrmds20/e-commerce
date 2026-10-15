from jose import ExpiredSignatureError, JWTError
from sqlalchemy.orm import Session

from app.api.exceptions import (
    EmailAlreadyExistsException,
    InactiveUserException,
    InvalidCredentialsException,
    InvalidTokenException,
    TokenExpiredException,
    UserNotFoundException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import AuthResponse, TokenResponse


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
        user = self.user_repo.get_by_email(data.username)

        if user is None or not verify_password(data.password, user.password_hash):
            raise InvalidCredentialsException()

        if not user.is_active:
            raise InactiveUserException()

        return self._issue_tokens(user.id)

    def _issue_tokens(self, user_id: int) -> TokenResponse:

        access_token = create_access_token({"sub": str(user_id)})
        refresh_token = create_refresh_token({"sub": str(user_id)})
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    def refresh(self, refresh_token: str) -> TokenResponse:

        if not refresh_token:
            raise InvalidTokenException()

        try:
            payload = decode_token(refresh_token)
        except ExpiredSignatureError as err:
            raise TokenExpiredException() from err
        except JWTError as err:
            raise InvalidTokenException() from err

        if payload.get("type") != "refresh":
            raise InvalidTokenException()

        user_id = payload.get("sub")
        if user_id is None:
            raise InvalidTokenException()

        user = self.user_repo.get_by_id(int(user_id))
        if user is None or not user.is_active:
            raise InvalidTokenException()

        return self._issue_tokens(user.id)

    def logout(self) -> None:

        return None

    def me(self, user: User) -> AuthResponse:
        if user is None:
            raise UserNotFoundException()
        return user
