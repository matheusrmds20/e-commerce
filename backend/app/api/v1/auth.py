from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import get_settings
from app.core.security import REFRESH_COOKIE_NAME
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    MessageResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService

auth_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]



def get_auth_service(db: DbSession) -> AuthService:
    return AuthService(db)

def _set_refresh_cookie(response: Response, request: Request, token: str) -> None:
    """Grava o refresh token em cookie httpOnly.

    - `Path=/auth` limita o envio às rotas de autenticação (refresca/logout).
    - `Secure` aplicado só quando a request chega por HTTPS — em dev local
      (http://localhost) fica desligado para o cookie funcionar no navegador.
    - `SameSite=Lax` protege contra CSRF cross-site mantendo a sessão ao
      navegar via link externo ("lembrar-me").
    """
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
        path="/auth",
        max_age=get_settings().REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

def _expire_refresh_cookie(response: Response, request: Request) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
        path="/auth",
    )


@auth_router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registra um novo usuário",
)
def register(data: RegisterRequest, db: DbSession) -> AuthResponse:
    return get_auth_service(db).register(data)


@auth_router.post(
    "/login",
    response_model=TokenResponse,
    summary="Autentica um usuário e retorna o access token (refresh em cookie)",
)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
    response: Response,
    request: Request,
) -> TokenResponse:
    result = get_auth_service(db).login(form_data)
    if result.refresh_token:
        _set_refresh_cookie(response, request, result.refresh_token)
    return result


@auth_router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="Renova o access token a partir do refresh token (rotação)",
)
def refresh(
    db: DbSession,
    request: Request,
    response: Response,
    data: RefreshRequest | None = None,
) -> RefreshResponse:
    # Preferência por cookie (fluxo navegador). Body é fallback.
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME) or (
        data.refresh_token if data else None
    )
    result = get_auth_service(db).refresh(refresh_token)
    if result.refresh_token:
        _set_refresh_cookie(response, request, result.refresh_token)
    return RefreshResponse(access_token=result.access_token)


@auth_router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Encerra a sessão (apaga o cookie de refresh)",
)
def logout(
    db: DbSession,
    request: Request,
    response: Response,
) -> MessageResponse:
    get_auth_service(db).logout()
    _expire_refresh_cookie(response, request)
    return MessageResponse(message="Sessão encerrada.")


@auth_router.get(
    "/me",
    response_model=AuthResponse,
    summary="Retorna os dados do usuário autenticado",
)
def me(
    user: Annotated[User, Depends(get_current_user)],
    db: DbSession,
) -> AuthResponse:
    return get_auth_service(db).me(user)
