from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Category(Base):

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    slug = Column(String(120), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)


    products = relationship("Product", back_populates="categories")
