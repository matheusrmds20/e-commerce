from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.db.base import Base


class NewsletterSubscriber(Base):

    __tablename__ = "newsletter_subscribers"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    subscribed_at = Column(DateTime, nullable=False, default=datetime.now)

