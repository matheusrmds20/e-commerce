from datetime import datetime
from enum import StrEnum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class OrderStatus(StrEnum):

    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class Order(Base):

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    address_id = Column(Integer, ForeignKey("addresses.id"), nullable=False)
    coupon_id = Column(Integer, ForeignKey("coupons.id"), nullable=True)
    notes = Column(String(500), nullable=True)
    status = Column(
        Enum(OrderStatus, values_callable=lambda x: [e.value for e in x]),
        default=OrderStatus.PENDING,
        nullable=False,
    )
    subtotal = Column(Float, nullable=False)
    discount_amount = Column(Float, nullable=False)
    shipping_cost = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now)



    users = relationship("User", back_populates="orders")
    addresses = relationship("Address", back_populates="orders")
    coupon = relationship("Coupon", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="orders")
