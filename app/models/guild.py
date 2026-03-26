from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from app.core.database import Base


class Guild(Base):
    """Gildiya — ustalar uyushmasi (masalan: Yog'ochsozlik, Zargarlik, Tikuvchilik)"""
    __tablename__ = "guilds"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    icon_url = Column(String(300), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("GuildMembership", back_populates="guild")

    def __repr__(self):
        return f"<Guild {self.name}>"


class GuildMembership(Base):
    """Gildiya a'zoligi — usta gildiyaga qo'shilganda yaratiladi"""
    __tablename__ = "guild_memberships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    guild_id = Column(Integer, ForeignKey("guilds.id"), nullable=False)
    rank = Column(String(50), default="Shogird")  # Shogird -> Usta -> Sarusta -> Pir
    nufuz = Column(Float, default=0.0)  # Reputatsiya bali
    joined_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="guild_membership")
    guild = relationship("Guild", back_populates="members")

    def __repr__(self):
        return f"<GuildMembership user={self.user_id} guild={self.guild_id} rank={self.rank}>"


class Apprenticeship(Base):
    """Ustoz-Shogird bog'lanishi"""
    __tablename__ = "apprenticeships"

    id = Column(Integer, primary_key=True, index=True)
    master_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    apprentice_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)

    master = relationship("User", back_populates="apprentices", foreign_keys=[master_id])
    apprentice = relationship("User", back_populates="master_link", foreign_keys=[apprentice_id])

    def __repr__(self):
        return f"<Apprenticeship master={self.master_id} -> apprentice={self.apprentice_id}>"


class Duo(Base):
    """Duo — ijobiy sharh / duo (usta haqida yaxshi so'zlar)"""
    __tablename__ = "duolar"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    author = relationship("User", back_populates="duolar", foreign_keys=[author_id])

    def __repr__(self):
        return f"<Duo from={self.author_id} to={self.target_user_id}>"
