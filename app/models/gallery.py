from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class GalleryItem(Base):
    """Usta ishlari galereyasi — har bir rasm usta profiliga bog'langan"""
    __tablename__ = "gallery_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    image_url = Column(String(500), nullable=False)
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", backref="gallery_items")

    def __repr__(self):
        return f"<GalleryItem #{self.id} user={self.user_id}>"
