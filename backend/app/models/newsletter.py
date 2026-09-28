from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.db.base import Base


class NewsletterSubscriber(Base):
    """E-mail inscrito na newsletter ("Cartas do Sebo")."""

    __tablename__ = "newsletter_subscribers"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    subscribed_at = Column(DateTime, nullable=False, default=datetime.now)

    # Sem FK para users: a newsletter aceita visitantes que ainda não têm conta.
