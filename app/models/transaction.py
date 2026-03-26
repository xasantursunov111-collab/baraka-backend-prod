import enum
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Text, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class OrderStatus(str, enum.Enum):
    """Buyurtma holatlari"""
    YANGI = "YANGI"                    # Yangi buyurtma yaratildi
    QABUL_QILINDI = "QABUL_QILINDI"  # Usta qabul qildi
    JARAYONDA = "JARAYONDA"            # Ish bajarilmoqda
    MUDDAT_UZAYTIRILDI = "MUDDAT_UZAYTIRILDI"  # Bag'rikenglik: muddat uzaytirildi
    YAKUNLANDI = "YAKUNLANDI"          # Ish tugallandi
    BEKOR_QILINDI = "BEKOR_QILINDI"  # Buyurtma bekor qilindi


class RizolikDarajasi(str, enum.Enum):
    """Mijozning rizolik darajasi"""
    AJOYIB = "AJOYIB"          # 5 yulduz — to'liq rizolik
    YAXSHI = "YAXSHI"          # 4 yulduz
    QONIQARLI = "QONIQARLI"  # 3 yulduz
    YOMON = "YOMON"            # 2 yulduz
    NOROZI = "NOROZI"          # 1 yulduz — norozilik


class Order(Base):
    """Buyurtma — mijoz va usta o'rtasidagi ish shartnomasi"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    master_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Usta keyinroq tayinlanishi mumkin
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.YANGI, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    deadline = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Bag'rikenglik: muddat uzaytirilganmi?
    is_extended = Column(Boolean, default=False)
    extension_reason = Column(Text, nullable=True)

    # Rizolik
    rizolik = Column(Enum(RizolikDarajasi), nullable=True)
    rizolik_comment = Column(Text, nullable=True)

    # SOS tizimi
    sos_requested = Column(Boolean, default=False)
    sos_helper_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relations
    client = relationship("User", back_populates="orders_as_client", foreign_keys=[client_id])
    master = relationship("User", back_populates="orders_as_master", foreign_keys=[master_id])
    sos_helper = relationship("User", foreign_keys=[sos_helper_id])
    estimate = relationship("Estimate", back_populates="order", uselist=False, cascade="all, delete-orphan")


    def __repr__(self):
        return f"<Order #{self.id} — {self.title} ({self.status.value})>"


class Estimate(Base):
    __tablename__ = "estimates"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True)
    master_id = Column(Integer, ForeignKey("users.id"))
    client_id = Column(Integer, ForeignKey("users.id"))
    items = Column(JSON, default=list)  # [{'name': 'Taxta', 'price': 200000}, ...]
    total_price = Column(Float, default=0.0)
    is_accepted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="estimate")
    master = relationship("User", foreign_keys=[master_id])
    client = relationship("User", foreign_keys=[client_id])

    def __repr__(self):
        return f"<Estimate #{self.id} for Order #{self.order_id} (Total: {self.total_price})>"
