from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCouponCreate(BaseModel):
    """Atribui (resgata) um cupom para um usuário."""

    user_id: int = Field(..., description="ID do usuário que recebe o cupom")
    coupon_id: int = Field(..., description="ID do cupom atribuído")


class UserCouponResponse(BaseModel):
    id: int
    user_id: int
    coupon_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
