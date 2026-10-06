from datetime import UTC, datetime, timedelta
from uuid import uuid4

from jose import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

settings = get_settings()

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


password_hash = PasswordHash.recommended()


# Nome do cookie httpOnly onde o refresh token é entregue ao frontend.
REFRESH_COOKIE_NAME = "papiro_refresh"


def hash_password(password):
    return password_hash.hash(password)


def verify_password(password, hashed_password):
    return password_hash.verify(password, hashed_password)


def _create_jwt(data: dict, expires_delta: timedelta, token_type: str) -> str:
    """Gera um JWT com claims de segurança (sub, jti, type, iat, exp)."""
    to_encode = data.copy()
    now = datetime.now(UTC)
    to_encode.update(
        {
            # `jti` identifica cada token individualmente — base da futura
            # blacklist (redis) quando implementada.
            "jti": str(uuid4()),
            "type": token_type,  # "access" | "refresh"
            "iat": now,
            "exp": now + expires_delta,
        }
    )
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(data: dict, expires_delta: timedelta = None):
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_jwt(data, expires_delta, token_type="access")


def create_refresh_token(data: dict, expires_delta: timedelta = None):
    if expires_delta is None:
        expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_jwt(data, expires_delta, token_type="refresh")


def decode_token(token: str) -> dict:
    """Decodifica e valida um JWT (assinatura + exp). Levanta jose.JWTError.

    Retorna o payload. A checagem de `type` (access vs refresh) fica a cargo
    do chamador, para que cada fluxo exija o tipo correto.
    """
    options = {"verify_signature": True, "verify_exp": True}
    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
        options=options,
    )
