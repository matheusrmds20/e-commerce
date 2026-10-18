from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import Page
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.product_service import ProductService

product_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]


AuthUser = Annotated[User, Depends(get_current_user)]

VitrineLimit = Annotated[
    int | None,
    Query(ge=1, le=100, description="Limite de itens retornados"),
]

PageNumber = Annotated[int, Query(ge=1, description="Página (começa em 1)")]
PerPage = Annotated[
    int, Query(ge=1, le=100, description="Itens por página (max 100)")
]


def parse_exclude_ids(raw: str | None) -> list[int]:

    if not raw:
        return []
    ids = []
    for parte in raw.split(","):
        parte = parte.strip()
        if parte.isdigit():
            ids.append(int(parte))
    return ids


def get_product_service(db: DbSession) -> ProductService:
    return ProductService(db)


@product_router.post(
    "/create",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo produto",
)
def create_product(
    data: ProductCreate, current_user: AuthUser, db: DbSession
) -> ProductResponse:
    """Cria um produto. Exige admin — sem token 401, sem papel 403."""
    return get_product_service(db).create(data, current_user)


@product_router.get(
    "/list",
    response_model=Page[ProductResponse],
    summary="Lista todos os produtos (paginado)",
)
def list_products(
    db: DbSession,
    page: PageNumber = 1,
    per_page: PerPage = 20,
) -> dict:

    return get_product_service(db).get_paginated(page, per_page)


@product_router.get(
    "/paginated",
    response_model=Page[ProductResponse],
    summary="Lista o catálogo com paginação",
)
def list_products_paginated(
    db: DbSession,
    page: PageNumber = 1,
    per_page: PerPage = 20,
    category_id: Annotated[
        int | None,
        Query(ge=1, description="Filtra por categoria antes de paginar"),
    ] = None,
    search: Annotated[
        str | None,
        Query(
            max_length=100,
            description="Busca livre (título, autor ou ISBN), case-insensitive",
        ),
    ] = None,
) -> dict:

    return get_product_service(db).get_paginated(
        page, per_page, category_id, search=search
    )


@product_router.get(
    "/recommendations",
    response_model=list[ProductResponse],
    summary="Recomenda produtos para o carrinho",
)
def list_recommendations(
    db: DbSession,
    exclude: Annotated[
        str | None,
        Query(
            description="Ids a excluir, separados por vírgula (ex.: 1,2,3)",
            examples=["1,2,3"],
        ),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=50, description="Máximo de itens")] = 4,
) -> list:

    exclude_ids = parse_exclude_ids(exclude)
    return get_product_service(db).get_recommendations(exclude_ids, limit)


@product_router.get(
    "/featured",
    response_model=list[ProductResponse],
    summary="Lista os produtos em destaque da vitrine",
)
def list_featured_products(db: DbSession, limit: VitrineLimit = None) -> list:

    return get_product_service(db).get_featured(limit)


@product_router.get(
    "/bestsellers",
    response_model=list[ProductResponse],
    summary="Lista os produtos mais vendidos da vitrine",
)
def list_bestseller_products(db: DbSession, limit: VitrineLimit = None) -> list:

    return get_product_service(db).get_bestsellers(limit)


@product_router.get(
    "/get/{product_id}",
    response_model=ProductResponse,
    summary="Busca um produto pelo ID",
)
def get_product(product_id: int, db: DbSession) -> ProductResponse:
    return get_product_service(db).get_by_id(product_id)


@product_router.get(
    "/category/{category_id}",
    response_model=list[ProductResponse],
    summary="Lista produtos por categoria",
)
def get_products_by_category(category_id: int, db: DbSession) -> list:
    return get_product_service(db).get_by_category_id(category_id)


@product_router.get(
    "/discount/{discount_pct}",
    response_model=list[ProductResponse],
    summary="Lista produtos por percentual de desconto",
)
def get_products_by_discount_pct(discount_pct: int, db: DbSession) -> list:
    return get_product_service(db).get_by_discount_pct(discount_pct)


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
    product_id: int,
    data: ProductUpdate,
    current_user: AuthUser,
    db: DbSession,
) -> ProductResponse:

    return get_product_service(db).update(product_id, data, current_user)


@product_router.delete(
    "/delete/{product_id}",
    response_model=ProductResponse,
    summary="Exclui um produto",
)
def delete_product(
    product_id: int, current_user: AuthUser, db: DbSession
) -> ProductResponse:

    return get_product_service(db).delete(product_id, current_user)
