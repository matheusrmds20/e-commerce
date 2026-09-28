from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.exceptions import (
    CategoryNotFoundException,
    ConflictException,
    InsufficientPermissionException,
)
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services.category_service import CategoryService

category_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
AuthUser = Annotated[User, Depends(get_current_user)]


def get_category_service(db: DbSession) -> CategoryService:
    return CategoryService(db)


def _traduzir_value_error(exc: ValueError):
    """Traduz os ``ValueError`` do service em erros HTTP (senão viram 500)."""
    msg = str(exc)

    if "Admin permission required" in msg:
        return InsufficientPermissionException()

    if "already exists" in msg:
        return ConflictException(msg, code="DUPLICATE_CATEGORY")

    return CategoryNotFoundException()


@category_router.post(
    "/create",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma nova categoria (restrito a administradores)",
)
def create_category(
    data: CategoryCreate, current_user: AuthUser, db: DbSession
) -> CategoryResponse:
    try:
        return get_category_service(db).create(data, current_user)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@category_router.get(
    "/list",
    response_model=list[CategoryResponse],
    summary="Lista todas as categorias",
)
def list_categories(db: DbSession) -> list:
    return get_category_service(db).get_all()


@category_router.get(
    "/get/{category_id}",
    response_model=CategoryResponse,
    summary="Busca uma categoria pelo ID",
)
def get_category(category_id: int, db: DbSession) -> CategoryResponse:
    try:
        return get_category_service(db).get_by_id(category_id)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@category_router.get(
    "/name/{name}",
    response_model=CategoryResponse,
    summary="Busca uma categoria pelo nome",
)
def get_category_by_name(name: str, db: DbSession) -> CategoryResponse:
    try:
        return get_category_service(db).get_by_name(name)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@category_router.get(
    "/slug/{slug}",
    response_model=CategoryResponse,
    summary="Busca uma categoria pelo slug",
)
def get_category_by_slug(slug: str, db: DbSession) -> CategoryResponse:
    try:
        return get_category_service(db).get_by_slug(slug)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@category_router.patch(
    "/update/{category_id}",
    response_model=CategoryResponse,
    summary="Atualiza uma categoria (restrito a administradores)",
)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    current_user: AuthUser,
    db: DbSession,
) -> CategoryResponse:
    try:
        return get_category_service(db).update(category_id, data, current_user)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@category_router.delete(
    "/delete/{category_id}",
    response_model=CategoryResponse,
    summary="Exclui uma categoria (restrito a administradores)",
)
def delete_category(
    category_id: int, current_user: AuthUser, db: DbSession
) -> CategoryResponse:
    try:
        return get_category_service(db).delete(category_id, current_user)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc
