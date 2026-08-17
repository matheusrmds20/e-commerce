from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService

auth_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]


def get_auth_service(db: DbSession) -> AuthService:
    return AuthService(db)


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
    summary="Autentica um usuário e retorna o token de acesso",
)
def login(data: LoginRequest, db: DbSession) -> TokenResponse:
    return get_auth_service(db).login(data)


@auth_router.get(
    "/me",
    response_model=AuthResponse,
    summary="Retorna os dados do usuário autenticado",
)
def me(
    user: Annotated[User, Depends(get_current_user)],
) -> AuthResponse:
    return get_auth_service(user.db).me(user)
