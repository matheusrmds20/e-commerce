from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.review import ReviewCreate, ReviewResponse, ReviewUpdate
from app.services.review_service import ReviewService

review_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
UserId = Annotated[int, Query(description="ID do usuário dono da avaliação")]


def get_review_service(db: DbSession) -> ReviewService:
    return ReviewService(db)


@review_router.post(
    "/create",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma avaliação",
)
def create_review(user_id: UserId, data: ReviewCreate, db: DbSession) -> ReviewResponse:
    return get_review_service(db).create(user_id, data)


@review_router.get(
    "/list",
    response_model=list[ReviewResponse],
    summary="Lista todas as avaliações",
)
def list_reviews(db: DbSession) -> list:
    return get_review_service(db).get_all()


@review_router.get(
    "/get/{review_id}",
    response_model=ReviewResponse,
    summary="Busca uma avaliação pelo ID",
)
def get_review(review_id: int, user_id: UserId, db: DbSession) -> ReviewResponse:
    return get_review_service(db).get_by_id(review_id, user_id)


@review_router.get(
    "/user/{user_id}",
    response_model=list[ReviewResponse],
    summary="Lista as avaliações de um usuário",
)
def get_reviews_by_user(user_id: int, db: DbSession) -> list:
    return get_review_service(db).get_by_user_id(user_id)


@review_router.get(
    "/product/{product_id}",
    response_model=list[ReviewResponse],
    summary="Lista as avaliações de um produto",
)
def get_reviews_by_product(product_id: int, db: DbSession) -> list:
    return get_review_service(db).get_by_product_id(product_id)


@review_router.get(
    "/rating/{rating}",
    response_model=list[ReviewResponse],
    summary="Lista avaliações por nota",
)
def get_reviews_by_rating(
    rating: Annotated[int, Path(ge=1, le=5, description="Nota da avaliação")],
    db: DbSession,
) -> list:
    return get_review_service(db).get_by_rating(rating)


@review_router.patch(
    "/update/{review_id}",
    response_model=ReviewResponse,
    summary="Atualiza uma avaliação",
)
def update_review(
    review_id: int, data: ReviewUpdate, user_id: UserId, db: DbSession
) -> ReviewResponse:
    return get_review_service(db).update(review_id, user_id, data)


@review_router.delete(
    "/delete/{review_id}",
    response_model=ReviewResponse,
    summary="Exclui uma avaliação",
)
def delete_review(review_id: int, user_id: UserId, db: DbSession) -> ReviewResponse:
    return get_review_service(db).delete(review_id, user_id)

