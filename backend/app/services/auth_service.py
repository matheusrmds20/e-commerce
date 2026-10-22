import hashlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from jose import ExpiredSignatureError, JWTError
from sqlalchemy.orm import Session

from app.api.exceptions import (
    AccountLockedException,
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
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_token_repo import RefreshTokenRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import AuthResponse, MessageResponse, TokenResponse
from app.services import login_lockout


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class AuthService:
    def __init__(self, db: Session) -> None:
        self.user_repo = UserRepository(db)
        self.refresh_repo = RefreshTokenRepository(db)
        self.session = db

    def register(self, data) -> MessageResponse:
        with self.session.begin():
            if self.user_repo.get_by_email(data.email) is not None:
                return MessageResponse(message="Cadastro realizado com sucesso.")

            self.user_repo.create(
                User(
                    email=data.email,
                    full_name=data.full_name,
                    password_hash=hash_password(data.password),
                )
            )

            return MessageResponse(message="Cadastro realizado com sucesso.")

    def login(self, data) -> TokenResponse:
        decision = login_lockout.check(data.username)
        if not decision.allowed:
            raise AccountLockedException(decision.retry_after)

        user = self.user_repo.get_by_email(data.username)

        credentials_ok = user is not None and verify_password(
            data.password, user.password_hash
        )

        if not credentials_ok:
            fail_decision = login_lockout.record_failure(data.username)
            if not fail_decision.allowed:
                raise AccountLockedException(fail_decision.retry_after)
            raise InvalidCredentialsException()

        if not user.is_active:
            raise InactiveUserException()

        login_lockout.record_success(data.username)

        return self._issue_tokens(user.id)

    def _issue_tokens(
        self,
        user_id: int,
        family_id: str | None = None,
    ) -> TokenResponse:
        """Emite access + refresh e persiste o refresh token (para revogação)."""
        user_id = int(user_id)

        if family_id is None:
            family_id = str(uuid4())

        refresh_jti = str(uuid4())
        refresh_token = create_refresh_token(
            {"sub": str(user_id)},
            jti=refresh_jti,
        )

        expires_at = datetime.now(UTC) + RefreshTokenRepository.expire_days()

        self.session.add(
            RefreshToken(
                user_id=user_id,
                jti=refresh_jti,
                token_hash=_token_hash(refresh_token),
                family_id=family_id,
                expires_at=expires_at,
            )
        )
        self.session.flush()

        access_token = create_access_token({"sub": str(user_id)})
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
        jti = payload.get("jti")
        if user_id is None or jti is None:
            raise InvalidTokenException()

        user = self.user_repo.get_by_id(int(user_id))
        if user is None or not user.is_active:
            raise InvalidTokenException()

        stored = self.refresh_repo.get_by_token_hash(_token_hash(refresh_token))
        if stored is None:
            raise InvalidTokenException()

        if stored.revoked:
            self.refresh_repo.revoke_family(stored.family_id)
            self.session.commit()
            raise TokenExpiredException()

        if stored.expires_at < datetime.now(UTC):
            self.refresh_repo.revoke(stored)
            self.session.commit()
            raise TokenExpiredException()

        if stored.jti != jti or stored.user_id != int(user_id):
            raise InvalidTokenException()

        self.refresh_repo.revoke(stored)
        result = self._issue_tokens(user.id, family_id=stored.family_id)
        self.session.commit()
        return result

    def logout(self, refresh_token: str | None) -> None:
        """Revoga o refresh token apresentado e, em troca de senha, todos os tokens."""
        if not refresh_token:
            return

        stored = self.refresh_repo.get_by_token_hash(_token_hash(refresh_token))
        if stored is not None and not stored.revoked:
            self.refresh_repo.revoke(stored)
            self.session.commit()

    def revoke_all_for_user(self, user_id: int) -> None:
        """Invalida todos os refresh tokens do usuário (ex.: troca de senha)."""
        self.refresh_repo.revoke_all_for_user(user_id)
        self.session.commit()

    def me(self, user: User) -> AuthResponse:
        if user is None:
            raise UserNotFoundException()
        return user