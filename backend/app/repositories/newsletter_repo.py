from sqlalchemy.orm import Session

from app.models.newsletter import NewsletterSubscriber
from app.repositories.base import BaseRepository


class NewsletterRepository(BaseRepository[NewsletterSubscriber]):
    def __init__(self, db: Session) -> None:
        super().__init__(NewsletterSubscriber, db)

    def get_by_email(self, email: str) -> NewsletterSubscriber | None:
        return (
            self.session.query(NewsletterSubscriber)
            .filter(NewsletterSubscriber.email == email)
            .first()
        )
