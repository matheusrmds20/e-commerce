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
from fastapi.security import OAuth2PasswordRequestForm

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
    response_model=None,
    summary="Autentica um usuário e retorna o token de acesso",
)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: DbSession = None) -> TokenResponse:
    return get_auth_service(db).login(form_data)



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
