from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class NewsletterSubscribe(BaseModel):
    """Payload público de inscrição na newsletter."""

    email: EmailStr = Field(description="E-mail do inscrito")


class NewsletterUnsubscribe(BaseModel):
    """Payload público de cancelamento de inscrição."""

    email: EmailStr = Field(description="E-mail a remover da newsletter")


class NewsletterSubscriberResponse(BaseModel):
    id: int
    email: str
    subscribed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NewsletterMessageResponse(BaseModel):
    """Resposta simples com mensagem (usada no unsubscribe)."""

    message: str
