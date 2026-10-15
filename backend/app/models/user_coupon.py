from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base


class UserCoupon(Base):

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
