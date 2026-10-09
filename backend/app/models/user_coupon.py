from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base


class UserCoupon(Base):
    """Vínculo N:N entre usuários e cupons (ownership).

    Representa os cupons que um usuário *possui* — por exemplo, um cupom de
    fidelidade ou de aniversário entregue a um cliente específico. Um mesmo
    cupom pode ser atribuído a vários usuários, e um usuário pode acumular
    vários cupons.

    A restrição única (user_id, coupon_id) impede atribuir o mesmo cupom duas
    vezes ao mesmo usuário — o service trata isso como conflito.

    `used_at` marca quando o usuário efetivamente usou o cupom num pedido.
    Permite modelar cupom de **uso único por cliente** (o padrão de cupom
    pessoal: "R$20 off, válido uma vez") sem depender do limite global
    `Coupon.max_uses`, que é compartilhado entre todos os usuários. Fica em
    NULL enquanto não usado.
    """

    __tablename__ = "user_coupons"

    __table_args__ = (
        UniqueConstraint("user_id", "coupon_id", name="uq_user_coupon"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    coupon_id = Column(Integer, ForeignKey("coupons.id"), nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now)

    users = relationship("User", back_populates="coupons")
    coupons = relationship("Coupon", back_populates="users")
