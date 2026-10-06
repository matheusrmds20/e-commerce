from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.newsletter import (
    NewsletterMessageResponse,
    NewsletterSubscribe,
    NewsletterSubscriberResponse,
    NewsletterUnsubscribe,
)
from app.services.newsletter_service import NewsletterService

newsletter_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
AuthUser = Annotated[User, Depends(get_current_user)]


def get_newsletter_service(db: DbSession) -> NewsletterService:
    return NewsletterService(db)


@newsletter_router.post(
    "/subscribe",
    response_model=NewsletterSubscriberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Inscreve um e-mail na newsletter (público)",
)
def subscribe(data: NewsletterSubscribe, db: DbSession):
    return get_newsletter_service(db).subscribe(data)


@newsletter_router.post(
    "/unsubscribe",
    response_model=NewsletterMessageResponse,
    summary="Remove um e-mail da newsletter (público)",
)
def unsubscribe(data: NewsletterUnsubscribe, db: DbSession):
    get_newsletter_service(db).unsubscribe(data)
    return {"message": "Inscrição cancelada com sucesso."}


@newsletter_router.get(
    "/list",
    response_model=list[NewsletterSubscriberResponse],
    summary="Lista todos os inscritos da newsletter (restrito a administradores)",
)
def list_subscribers(current_user: AuthUser, db: DbSession):
    return get_newsletter_service(db).list_all(current_user)
