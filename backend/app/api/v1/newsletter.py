from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
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


def _traduzir_value_error(exc: ValueError):
    """Traduz os ``ValueError`` do service em erros HTTP (senão viram 500)."""
    msg = str(exc)

    if "Admin permission required" in msg:
        return ForbiddenException(
            "Apenas administradores podem listar os inscritos da newsletter."
        )

    if "already subscribed" in msg:
        return ConflictException(msg, code="NEWSLETTER_ALREADY_SUBSCRIBED")

    return NotFoundException(msg, code="NEWSLETTER_SUBSCRIBER_NOT_FOUND")


@newsletter_router.post(
    "/subscribe",
    response_model=NewsletterSubscriberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Inscreve um e-mail na newsletter (público)",
)
def subscribe(data: NewsletterSubscribe, db: DbSession):
    try:
        return get_newsletter_service(db).subscribe(data)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@newsletter_router.post(
    "/unsubscribe",
    response_model=NewsletterMessageResponse,
    summary="Remove um e-mail da newsletter (público)",
)
def unsubscribe(data: NewsletterUnsubscribe, db: DbSession):
    try:
        get_newsletter_service(db).unsubscribe(data)
        return {"message": "Inscrição cancelada com sucesso."}
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@newsletter_router.get(
    "/list",
    response_model=list[NewsletterSubscriberResponse],
    summary="Lista todos os inscritos da newsletter (restrito a administradores)",
)
def list_subscribers(current_user: AuthUser, db: DbSession):
    try:
        return get_newsletter_service(db).list_all(current_user)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc
