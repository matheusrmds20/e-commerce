from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from app.models.coupon import DiscountType


class CouponCreate(BaseModel):
    code: str = Field(..., min_length=3, max_length=50, description="Código do cupom")
    product_id: int | None = Field(None, description="ID do produto")
    discount_type: DiscountType = Field(DiscountType.PERCENTAGE, description="Tipo de desconto")
    discount_value: float = Field(..., ge=0, description="Valor do desconto")
    min_purchase: float | None = Field(None, description="Valor mínimo de compra")
    max_discount: float | None = Field(None, description="Valor máximo de desconto")
    valid_until: datetime = Field(..., description="Validade do cupom")
    max_uses: int | None = Field(None, description="Quantidade máxima de usos")
    is_active: bool = Field(True, description="Ativo")

    @field_validator("discount_value")
    @classmethod
    def validate_discount(cls, discount_value: int) -> int:
        if discount_value < 0:
            raise ValueError("O desconto deve ser positivo.")
        return discount_value


class CouponUpdate(BaseModel):
    code: str | None = Field(None, min_length=3, max_length=50)
    product_id: int | None = None
    discount_type: DiscountType | None = None
    discount_value: float | None = Field(None, ge=0)
    min_purchase: int | None = None
    max_discount: int | None = None
    valid_until: datetime | None = None
    max_uses: int | None = None
    is_active: bool | None = None


class CouponResponse(BaseModel):
    id: int
    code: str
    product_id: int | None
    discount_type: DiscountType
    discount_value: float
    min_purchase: int | None
    max_discount: int | None
    valid_until: datetime
    max_uses: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
