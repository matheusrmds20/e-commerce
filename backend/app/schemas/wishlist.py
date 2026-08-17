from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class WishlistCreate(BaseModel):

    product_id: int = Field(description="ID do produto")


class WishlistUpdate(BaseModel):
    product_id: int | None = Field(None, description="Novo ID do produto")


class WishlistResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
