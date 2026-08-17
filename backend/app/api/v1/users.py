
from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
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


def get_user_service(db: DbSession) -> UserService:

    return UserService(db)


@user_router.post(
    "/create",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo usuário",
)
def create_user(
    data: AdminUserCreate | CustomerUserCreate,
    db: DbSession,
) -> UserResponse:

    return get_user_service(db).create(data)


@user_router.get(
    "/user_id/{user_id}",
    response_model=UserResponse,
    summary="Busca um usuário pelo ID",
)
def get_user(user_id: int, db: DbSession) -> UserResponse:

    return get_user_service(db).get_by_id(user_id)


@user_router.get(
    "/email/{email}",
    response_model=UserResponse,
    summary="Busca um usuário pelo e-mail",
)
def get_user_by_email(email: str, db: DbSession) -> UserResponse:

    return get_user_service(db).get_by_email(email)


@user_router.patch(
    "/update/{user_id}",
    response_model=UserResponse,
    summary="Atualiza os dados de um usuário",
)
def update_user(user_id: int, data: UserUpdate, db: DbSession) -> UserResponse:

    return get_user_service(db).update(user_id, data)


@user_router.post(
    "/change_password/{user_id}/change-password",
    response_model=MessageResponse,
    summary="Altera a senha do usuário",
)
def change_user_password(
    user_id: int,
    data: ChangePasswordRequest,
    db: DbSession,
) -> MessageResponse:

    return get_user_service(db).change_password(
        user_id,
        current_password=data.current_password,
        new_password=data.new_password,
    )


@user_router.delete(
    "/delete/{user_id}",
    response_model=UserResponse,
    summary="Desativa um usuário (soft delete)",
)
def deactivate_user(user_id: int, db: DbSession) -> UserResponse:

    return get_user_service(db).deactivate(user_id)

