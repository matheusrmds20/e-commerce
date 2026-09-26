from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class UserRole(StrEnum):

    CUSTOMER = "customer"
    ADMIN = "admin"


class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x]),
        default=UserRole.CUSTOMER,
        nullable=False,
    )
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now)





    addresses = relationship(
        "Address",
        back_populates="users",
        cascade="all, delete-orphan",
    )
    cart = relationship(
        "Cart",
        back_populates="users",
        cascade="all, delete-orphan",
        uselist=False,
    )
    orders = relationship(
        "Order",
        back_populates="users",
    )
    reviews = relationship(
        "Review",
        back_populates="users",
        cascade="all, delete-orphan",
    )
    wishlist_items = relationship(
        "Wishlist",
        back_populates="users",
        cascade="all, delete-orphan",
    )
    coupons = relationship(
        "UserCoupon",
        back_populates="users",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Representação legível do usuário."""
        return f"<User id={self.id} email={self.email!r} role={self.role.value}>"
