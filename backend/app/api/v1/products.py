from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.product_service import ProductService

product_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]


def get_product_service(db: DbSession) -> ProductService:
    return ProductService(db)


@product_router.post(
    "/create",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo produto",
)
def create_product(data: ProductCreate, db: DbSession) -> ProductResponse:
    return get_product_service(db).create(data)


@product_router.get(
    "/list",
    response_model=list[ProductResponse],
    summary="Lista todos os produtos",
)
def list_products(db: DbSession) -> list:
    return get_product_service(db).get_all()


@product_router.get(
    "/get/{product_id}",
    response_model=ProductResponse,
    summary="Busca um produto pelo ID",
)
def get_product(product_id: int, db: DbSession) -> ProductResponse:
    return get_product_service(db).get_by_id(product_id)


@product_router.get(
    "/title/{title}",
    response_model=ProductResponse,
    summary="Busca um produto pelo título",
)
def get_product_by_title(title: str, db: DbSession) -> ProductResponse:
    return get_product_service(db).get_by_title(title)


@product_router.get(
    "/slug/{slug}",
    response_model=ProductResponse,
    summary="Busca um produto pelo slug",
)
def get_product_by_slug(slug: str, db: DbSession) -> ProductResponse:
    return get_product_service(db).get_by_slug(slug)


@product_router.get(
    "/isbn/{isbn}",
    response_model=ProductResponse,
    summary="Busca um produto pelo ISBN",
)
def get_product_by_isbn(isbn: str, db: DbSession) -> ProductResponse:
    return get_product_service(db).get_by_isbn(isbn)


@product_router.get(
    "/category/{category_id}",
    response_model=list[ProductResponse],
    summary="Lista produtos por categoria",
)
def get_products_by_category(category_id: int, db: DbSession) -> list:
    return get_product_service(db).get_by_category_id(category_id)


@product_router.get(
    "/publisher/{publisher}",
    response_model=list[ProductResponse],
    summary="Lista produtos por editora",
)
def get_products_by_publisher(publisher: str, db: DbSession) -> list:
    return get_product_service(db).get_by_publisher(publisher)


@product_router.get(
    "/year/{publication_year}",
    response_model=list[ProductResponse],
    summary="Lista produtos por ano de publicação",
)
def get_products_by_publication_year(
    publication_year: int, db: DbSession
) -> list:
    return get_product_service(db).get_by_publication_year(publication_year)


@product_router.get(
    "/language/{language}",
    response_model=list[ProductResponse],
    summary="Lista produtos por idioma",
)
def get_products_by_language(language: str, db: DbSession) -> list:
    return get_product_service(db).get_by_language(language)


@product_router.get(
    "/discount/{discount_pct}",
    response_model=list[ProductResponse],
    summary="Lista produtos por percentual de desconto",
)
def get_products_by_discount_pct(discount_pct: int, db: DbSession) -> list:
    return get_product_service(db).get_by_discount_pct(discount_pct)


@product_router.get(
    "/stock/{stock_qty}",
    response_model=list[ProductResponse],
    summary="Lista produtos por quantidade de estoque",
)
def get_products_by_stock_qty(stock_qty: int, db: DbSession) -> list:
    return get_product_service(db).get_by_stock_qty(stock_qty)


@product_router.get(
    "/active/{is_active}",
    response_model=list[ProductResponse],
    summary="Lista produtos por status de ativação",
)
def get_products_by_is_active(is_active: bool, db: DbSession) -> list:
    return get_product_service(db).get_by_is_active(is_active)


@product_router.patch(
    "/update/{product_id}",
    response_model=ProductResponse,
    summary="Atualiza um produto",
)
def update_product(
    product_id: int, data: ProductUpdate, db: DbSession
) -> ProductResponse:
    return get_product_service(db).update(product_id, data)


@product_router.delete(
    "/delete/{product_id}",
    response_model=ProductResponse,
    summary="Exclui um produto",
)
def delete_product(product_id: int, db: DbSession) -> ProductResponse:
    return get_product_service(db).delete(product_id)
