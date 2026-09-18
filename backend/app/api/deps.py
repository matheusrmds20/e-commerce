from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.database import SessionLocal
from app.models.user import User

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
        options = {"verify_signature": True, "verify_exp": True}

        payload = jwt.decode(
            token, settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options=options,
        )

        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nao foi possível validar o token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except JWTError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nao foi possível validar o token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err

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

    # A query acima abriu uma transação implícita (SQLAlchemy 2.x autobegin).
    # Vários services chamam `with session.begin()` no mesmo `db`; sem encerrar
    # aqui, o begin estoura "A transaction is already begun on this Session" e
    # a rota devolve 500.
    #
    # `expunge` desliga o objeto da sessão e `rollback` fecha a transação de
    # leitura. A ordem importa: sem o expunge, o rollback expira os atributos e
    # o próximo `user.id` (no router) reabriria uma transação, reproduzindo o
    # problema. O `id` já está em memória, então segue acessível.
    db.expunge(user)
    db.rollback()

    return user
