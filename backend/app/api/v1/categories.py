from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services.category_service import CategoryService

category_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]


def get_category_service(db: DbSession) -> CategoryService:
    return CategoryService(db)


@category_router.post(
    "/create",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma nova categoria",
)
def create_category(data: CategoryCreate, db: DbSession) -> CategoryResponse:
    return get_category_service(db).create(data)


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
    return get_category_service(db).get_by_id(category_id)


@category_router.get(
    "/name/{name}",
    response_model=CategoryResponse,
    summary="Busca uma categoria pelo nome",
)
def get_category_by_name(name: str, db: DbSession) -> CategoryResponse:
    return get_category_service(db).get_by_name(name)


@category_router.get(
    "/slug/{slug}",
    response_model=CategoryResponse,
    summary="Busca uma categoria pelo slug",
)
def get_category_by_slug(slug: str, db: DbSession) -> CategoryResponse:
    return get_category_service(db).get_by_slug(slug)


@category_router.patch(
    "/update/{category_id}",
    response_model=CategoryResponse,
    summary="Atualiza uma categoria",
)
def update_category(
    category_id: int, data: CategoryUpdate, db: DbSession
) -> CategoryResponse:
    return get_category_service(db).update(category_id, data)


@category_router.delete(
    "/delete/{category_id}",
    response_model=CategoryResponse,
    summary="Exclui uma categoria",
)
def delete_category(category_id: int, db: DbSession) -> CategoryResponse:
    return get_category_service(db).delete(category_id)

