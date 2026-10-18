from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class NewsletterSubscribe(BaseModel):

    email: EmailStr = Field(description="E-mail do inscrito")


class NewsletterUnsubscribe(BaseModel):

    email: EmailStr = Field(description="E-mail a remover da newsletter")


class NewsletterSubscriberResponse(BaseModel):
    id: int
    email: str
    subscribed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NewsletterMessageResponse(BaseModel):

    message: str
