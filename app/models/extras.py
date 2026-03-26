"""
BARAKA — Yangi modellar: Bildirishnoma, Sertifikat, Kalendar
"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Date, ForeignKey, Boolean, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


# ==================== BILDIRISHNOMALAR ====================

class NotificationType(str, enum.Enum):
    ORDER = "ORDER"
    REVIEW = "REVIEW"
    SYSTEM = "SYSTEM"
    CHAT = "CHAT"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(SAEnum(NotificationType), default=NotificationType.SYSTEM)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False)
    link = Column(String(300), nullable=True)  # sahifaga yo'naltirish uchun
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================== SERTIFIKATLAR ====================

class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    cert_code = Column(String(50), unique=True, nullable=False)  # BARAKA-2026-00001
    issued_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="certificates")
    course = relationship("Course", backref="certificates")


# ==================== USTA KALENDARI ====================

class ScheduleSlot(Base):
    __tablename__ = "schedule_slots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    is_busy = Column(Boolean, default=True)
    note = Column(String(200), nullable=True)  # "Buyurtma bor", "Dam olish kuni"

    user = relationship("User", backref="schedule_slots")
