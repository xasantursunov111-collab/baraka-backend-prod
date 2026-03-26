from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class SupplierProduct(Base):
    """Do'kondor tomonidan qo'shilgan mahsulot"""
    __tablename__ = "supplier_products"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Majburiy maydonlar
    name = Column(String(200), nullable=False)
    shop_address = Column(String(300), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)

    # Ixtiyoriy maydonlar
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=True)
    brand = Column(String(100), nullable=True)
    image_url = Column(String(500), nullable=True)
    stock_qty = Column(Integer, nullable=True)  # Ombordagi qoldiq
    category = Column(String(100), nullable=True)  # Kategoriya: Petla, MDF, Furnitura...

    created_at = Column(DateTime, default=datetime.utcnow)

    supplier = relationship("User")


class SupplierReview(Base):
    """Ustaning do'kondorga bergan bahosi (Halol Savdo Reytingi)"""
    __tablename__ = "supplier_reviews"

    id = Column(Integer, primary_key=True, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    reviewer = relationship("User", foreign_keys=[reviewer_id])
    supplier = relationship("User", foreign_keys=[supplier_id])
