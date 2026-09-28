from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.user import (
    AdminUserCreate,
    ChangePasswordRequest,
    CustomerUserCreate,
    UserResponse,
    UserUpdate,
)
from app.services.user_service import UserService

user_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
AuthUser = Annotated[User, Depends(get_current_user)]


def get_user_service(db: DbSession) -> UserService:

    return UserService(db)


@user_router.post(
    "/create",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo usuário (restrito a administradores)",
)
def create_user(
    data: AdminUserCreate | CustomerUserCreate,
    current_user: AuthUser,
    db: DbSession,
) -> UserResponse:

    return get_user_service(db).create(data, current_user)


@user_router.get(
    "/user_id/{user_id}",
    response_model=UserResponse,
    summary="Busca um usuário pelo ID (restrito a administradores)",
)
def get_user(
    user_id: int, current_user: AuthUser, db: DbSession
) -> UserResponse:

    return get_user_service(db).get_by_id(user_id, current_user)


@user_router.get(
    "/email/{email}",
    response_model=UserResponse,
    summary="Busca um usuário pelo e-mail (restrito a administradores)",
)
def get_user_by_email(
    email: str, current_user: AuthUser, db: DbSession
) -> UserResponse:

    return get_user_service(db).get_by_email(email, current_user)


@user_router.patch(
    "/update/{user_id}",
    response_model=UserResponse,
    summary="Atualiza os dados de um usuário (dono ou admin)",
)
def update_user(
    user_id: int, data: UserUpdate, current_user: AuthUser, db: DbSession
) -> UserResponse:

    return get_user_service(db).update(user_id, data, current_user)


@user_router.post(
    "/change_password/{user_id}/change-password",
    response_model=MessageResponse,
    summary="Altera a senha do usuário (dono ou admin)",
)
def change_user_password(
    user_id: int,
    data: ChangePasswordRequest,
    current_user: AuthUser,
    db: DbSession,
) -> MessageResponse:

    return get_user_service(db).change_password(
        user_id,
        current_password=data.current_password,
        new_password=data.new_password,
        current_user=current_user,
    )


@user_router.delete(
    "/delete/{user_id}",
    response_model=UserResponse,
    summary="Desativa um usuário (soft delete) — dono ou admin",
)
def deactivate_user(
    user_id: int, current_user: AuthUser, db: DbSession
) -> UserResponse:

    return get_user_service(db).deactivate(user_id, current_user)
