from sqlalchemy import Column, Float, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime


from app.db.base import Base



class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    provider = Column(String(255), nullable=False)
    provider_payment_id = Column(String(255), nullable=True)
    provider_preference_id = Column(String(255), nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now)


    orders = relationship("Order", back_populates="payments")