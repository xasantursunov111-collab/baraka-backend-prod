from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import enum
from sqlalchemy import Enum

class MaterialRequestStatus(str, enum.Enum):
    KUTILMOQDA = "KUTILMOQDA"
    YUBORILDI = "YUBORILDI"
    YETKAZIB_BERILDI = "YETKAZIB_BERILDI"
    BEKOR_QILINDI = "BEKOR_QILINDI"

class Material(Base):
    __tablename__ = "materials"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, default=0.0)
    image_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class MaterialRequest(Base):
    __tablename__ = "material_requests"
    id = Column(Integer, primary_key=True, index=True)
    master_id = Column(Integer, ForeignKey("users.id"))
    status = Column(Enum(MaterialRequestStatus), default=MaterialRequestStatus.KUTILMOQDA)
    total_price = Column(Float, default=0.0)
    delivery_address = Column(String)
    admin_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    master = relationship("User")
    items = relationship("MaterialRequestItem", back_populates="request", cascade="all, delete")

class MaterialRequestItem(Base):
    __tablename__ = "material_request_items"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("material_requests.id"))
    material_id = Column(Integer, ForeignKey("materials.id"))
    quantity = Column(Float, default=1.0)
    price = Column(Float, default=0.0) # Price at the time of order

    request = relationship("MaterialRequest", back_populates="items")
    material = relationship("Material")
