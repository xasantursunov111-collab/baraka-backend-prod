from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    master_id = Column(Integer, ForeignKey("users.id"))
    price = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    master = relationship("User")
    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")

class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    title = Column(String)
    content = Column(Text, nullable=True)
    video_url = Column(String, nullable=True)
    sequence_number = Column(Integer, default=1)

    course = relationship("Course", back_populates="lessons")
