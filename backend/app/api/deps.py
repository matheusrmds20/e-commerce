from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.api.exceptions import InsufficientPermissionException
from app.core.config import get_settings
from app.core.security import decode_token
from app.db.database import SessionLocal
from app.models.user import User, UserRole

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[str, Depends(oauth2_scheme)],
):
    try:
        payload = decode_token(token)
    except JWTError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nao foi possível validar o token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err

    # Só access tokens autenticam em endpoints protegidos. Recusa refresh
    # token (que deve ir apenas para /auth/refresh).
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido para este recurso",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nao foi possível validar o token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(
        User.id == int(user_id),
        User.is_active.is_(True),
    ).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db.expunge(user)
    db.rollback()

    return user


async def get_current_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Exige que o usuário autenticado seja administrador.

    401 quando não há token válido (via ``get_current_user``); 403 quando o
    usuário está autenticado mas não tem o papel ``admin``. Usada como
    dependência de router nas áreas administrativas, de cupons e de vínculos
    usuário-cupom.
    """
    if user.role != UserRole.ADMIN:
        # Usa a exceção de domínio para responder no envelope padronizado
        # `{"error": {"code": "INSUFFICIENT_PERMISSION", ...}}`, igual às
        # checagens de admin dentro dos services.
        raise InsufficientPermissionException()
    return user
