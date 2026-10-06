from app.api.exceptions import (
    ConflictException,
    ForbiddenException,
    NewsletterSubscriberNotFoundException,
)
from app.models.newsletter import NewsletterSubscriber
from app.models.user import User, UserRole
from app.repositories.newsletter_repo import NewsletterRepository


class NewsletterService:
    """Regras da newsletter.

    Público: ``subscribe`` (idempotente para o cliente — já inscrito vira
    ``ConflictException`` traduzido para 409) e ``unsubscribe``.
    Administrador: ``list_all`` (base da aba Newsletter do painel).
    """

    def __init__(self, db):
        self.repo = NewsletterRepository(db)
        self.session = db

    def subscribe(self, data) -> dict:
        with self.session.begin():
            email = data.email.lower().strip()

            existing = self.repo.get_by_email(email)

            if existing is not None:
                raise ConflictException(
                    "Este e-mail já está inscrito na newsletter.",
                    code="NEWSLETTER_ALREADY_SUBSCRIBED",
                )

            subscriber = self.repo.create(
                NewsletterSubscriber(email=email)
            )

            return subscriber

    def unsubscribe(self, data) -> dict:
        with self.session.begin():
            email = data.email.lower().strip()

            subscriber = self.repo.get_by_email(email)

            if subscriber is None:
                raise NewsletterSubscriberNotFoundException()

            self.repo.delete(subscriber)

            return subscriber

    def list_all(self, current_user: User) -> list:
        if current_user.role != UserRole.ADMIN:
            raise ForbiddenException(
                "Apenas administradores podem listar os inscritos da newsletter."
            )

        return self.repo.get_all()
