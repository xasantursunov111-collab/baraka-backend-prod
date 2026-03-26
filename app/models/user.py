import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserRole(str, enum.Enum):
    """Foydalanuvchi roli"""
    ADMIN = "ADMIN"          # Sayt boshqaruvchisi
    MIJOZ = "MIJOZ"          # Oddiy mijoz (buyurtmachi)
    USTA = "USTA"            # Hunarmand (xizmat ko'rsatuvchi)
    SHOGIRD = "SHOGIRD"      # Ustaning shogirdi
    DOKONDOR = "DOKONDOR"    # Furnitura/material do'kon egasi


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(120), nullable=False)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)  # Nullable temporarily for existing seed data
    role = Column(Enum(UserRole), default=UserRole.MIJOZ, nullable=False)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(300), nullable=True)

    # Geo-location for Masters Map / Suppliers Map
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    shop_address = Column(String(300), nullable=True)  # DOKONDOR uchun do'kon manzili

    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Platforma qadriyatlari
    baraka_count = Column(Integer, default=0)
    halol_rating = Column(Float, default=0.0)
    bagrikenglik_requests = Column(Integer, default=0)


    # -------- Bog'lanishlar (Relationships) --------
    # Usta sifatida qilgan buyurtmalar
    orders_as_master = relationship(
        "Order", back_populates="master", foreign_keys="Order.master_id"
    )
    # Mijoz sifatida bergan buyurtmalar
    orders_as_client = relationship(
        "Order", back_populates="client", foreign_keys="Order.client_id"
    )
    # Usta ustoz sifatida — uning shogirdlari
    apprentices = relationship(
        "Apprenticeship", back_populates="master", foreign_keys="Apprenticeship.master_id"
    )
    # Shogird sifatida — uning ustozi
    master_link = relationship(
        "Apprenticeship", back_populates="apprentice", foreign_keys="Apprenticeship.apprentice_id"
    )
    # Gildiya a'zoligi
    guild_membership = relationship("GuildMembership", back_populates="user", uselist=False)
    # Duolar (ijobiy sharhlar)
    duolar = relationship("Duo", back_populates="author", foreign_keys="Duo.author_id")

    def __repr__(self):
        return f"<User {self.full_name} ({self.role.value})>"
