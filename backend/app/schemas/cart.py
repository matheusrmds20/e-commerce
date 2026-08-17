from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.product import ProductResponse


class CartItemCreate(BaseModel):
    product_id: int = Field(description="ID do produto")
    quantity: int = Field(..., ge=1, description="Quantidade")


class CartItemUpdate(BaseModel):
    quantity: int | None = Field(None, ge=1, description="Nova quantidade")


class CartItemResponse(BaseModel):
    id: int
    cart_id: int
    product_id: int
    quantity: int
    product: ProductResponse

    model_config = ConfigDict(from_attributes=True)


class CartCreate(BaseModel):


    user_id: int = Field(description="ID do usuário")
    items: list[CartItemCreate] = Field(default_factory=list)



class CartUpdate(BaseModel):

    items: list[CartItemCreate] | None = None


class CartResponse(BaseModel):
    id: int
    user_id: int
    items: list[CartItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
