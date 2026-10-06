from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewResponse, ReviewUpdate
from app.services.review_service import ReviewService

review_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
AuthUser = Annotated[User, Depends(get_current_user)]


def get_review_service(db: DbSession) -> ReviewService:
    return ReviewService(db)


@review_router.post(
    "/create",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma avaliação para o usuário autenticado",
)
def create_review(
    data: ReviewCreate, current_user: AuthUser, db: DbSession
) -> ReviewResponse:
    return get_review_service(db).create(current_user, data)


@review_router.get(
    "/list",
    response_model=list[ReviewResponse],
    summary="Lista as avaliações do usuário autenticado (admin pode alvejar ?user_id=)",
)
def list_reviews(
    current_user: AuthUser,
    db: DbSession,
    user_id: Annotated[
        int | None,
        Query(ge=1, description="Alvo (apenas administradores)"),
    ] = None,
) -> list:
    """Minhas avaliações. Com ``user_id``, restrito a administradores."""
    return get_review_service(db).get_by_user_id(current_user, user_id)


@review_router.get(
    "/product/{product_id}",
    response_model=list[ReviewResponse],
    summary="Lista as avaliações de um produto (público)",
)
def get_reviews_by_product(product_id: int, db: DbSession) -> list:
    return get_review_service(db).get_by_product_id(product_id)


@review_router.patch(
    "/update/{review_id}",
    response_model=ReviewResponse,
    summary="Atualiza uma avaliação (autor ou admin)",
)
def update_review(
    review_id: int,
    data: ReviewUpdate,
    current_user: AuthUser,
    db: DbSession,
) -> ReviewResponse:
    return get_review_service(db).update(review_id, data, current_user)


@review_router.delete(
    "/delete/{review_id}",
    response_model=ReviewResponse,
    summary="Exclui uma avaliação (autor ou admin)",
)
def delete_review(review_id: int, current_user: AuthUser, db: DbSession) -> ReviewResponse:
    return get_review_service(db).delete(review_id, current_user)
