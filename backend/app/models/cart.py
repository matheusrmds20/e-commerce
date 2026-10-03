from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base


class Cart(Base):

    __tablename__ = "carts"
    # Um carrinho por usuário: a service `create` já impede o segundo, e a
    # constraint é a garantia no banco (defesa em profundidade, mesmo padrão
    # da constraint (cart_id, product_id) em cart_items).
    __table_args__ = (
        UniqueConstraint("user_id", name="carts_user_id_key"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now)


    users = relationship("User", back_populates="cart")
    cart_items = relationship("CartItem", back_populates="carts")
