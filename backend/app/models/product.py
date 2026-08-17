from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Float
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime


class Product(Base):

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    title = Column(String(255), nullable=False)
    slug = Column(String(300), nullable=False)
    description = Column(String(500), nullable=False)
    author = Column(String(255), nullable=False)
    isbn = Column(String(20), nullable=True)
    publisher = Column(String(150), nullable=True)
    publication_year = Column(Integer, nullable=True)
    pages = Column(Integer, nullable=True)
    language = Column(String(50), nullable=True)
    synopsis = Column(String(500), nullable=True)
    price = Column(Float, nullable=False)
    discount_pct = Column(Integer, nullable=True)
    stock_qty = Column(Integer, nullable=False)
    image_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now)


    categories = relationship("Category", back_populates="products")
    coupons = relationship("Coupon", back_populates="products")
    cart_items = relationship("CartItem", back_populates="product")
    reviews = relationship("Review", back_populates="products")
    order_items = relationship("OrderItem", back_populates="products")
    wishlist_items = relationship("Wishlist", back_populates="products")
    