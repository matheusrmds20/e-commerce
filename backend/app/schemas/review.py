from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class ReviewCreate(BaseModel):

    product_id: int = Field(description="ID do produto")
    rating: int = Field(..., ge=1, le=5, description="Avaliação (1-5)")
    comment: str | None = Field(None, min_length=3, max_length=500, description="Comentário")


class ReviewUpdate(BaseModel):
    rating: int | None = Field(None, ge=1, le=5)
    comment: str | None = Field(None, min_length=3, max_length=500)


class ReviewResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    rating: int
    comment: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
