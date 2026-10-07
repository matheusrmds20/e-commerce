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
    # ``product`` vem quando a relação é serializável (leitura/criação). Pode
    # ser None em fluxos que deletam a linha e respondem a partir de um objeto
    # que já não suporta lazy-load (ex.: remover da sacola), evitando
    # DetachedInstanceError. O front sempre trata ``product`` vazio.
    product: ProductResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class CartCreate(BaseModel):


    user_id: int = Field(description="ID do usuário")
    cart_items: list[CartItemCreate] = Field(default_factory=list)



class CartUpdate(BaseModel):

    cart_items: list[CartItemCreate] | None = None


class CartResponse(BaseModel):
    id: int
    user_id: int
    cart_items: list[CartItemResponse]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
