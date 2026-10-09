from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class DiscountType(StrEnum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"

class Coupon(Base):

    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    code = Column(String(50), nullable=False, unique=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    discount_type = Column(
        Enum(DiscountType, values_callable=lambda x: [e.value for e in x]),
        default=DiscountType.PERCENTAGE,
        nullable=False,
    )
    discount_value = Column(Float, nullable=False)
    min_purchase = Column(Float, nullable=True)
    max_discount = Column(Float, nullable=True)
    valid_until = Column(DateTime, nullable=False)
    max_uses = Column(Integer, nullable=True)
    # Quando True, cada usuário só pode usar o cupom UMA vez (padrão de cupom
    # pessoal). O limite global `max_uses` continua valendo em paralelo.
    single_use_per_user = Column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    # Quantas vezes o cupom já foi efetivamente aplicado a um pedido.
    # Antes não existia contador: `max_uses` era gravado mas nunca lido, então
    # um cupom podia ser reutilizado indefinidamente. Incrementado dentro da
    # transação do checkout, com a linha do cupom travada (FOR UPDATE).
    used_count = Column(
        Integer, nullable=False, default=0, server_default="0"
    )
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now)


    products = relationship("Product", back_populates="coupons")
    orders = relationship("Order", back_populates="coupon")
    users = relationship(
        "UserCoupon",
        back_populates="coupons",
        cascade="all, delete-orphan",
    )
