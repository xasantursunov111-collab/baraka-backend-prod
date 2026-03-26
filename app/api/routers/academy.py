from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.academy import Course, Lesson
from app.models.user import User, UserRole
from app.schemas.schemas import CourseCreate, CourseOut, LessonCreate, LessonOut
from app.api.routers.users import get_current_user

router = APIRouter(
    prefix="/courses",
    tags=["Akademiya"]
)

@router.post("/", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(
    course_in: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.USTA, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Faqat ustalar kurs yarata oladi")
    
    course = Course(
        title=course_in.title,
        description=course_in.description,
        price=course_in.price,
        master_id=current_user.id
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course

@router.get("/", response_model=List[CourseOut])
def get_all_courses(db: Session = Depends(get_db)):
    courses = db.query(Course).all()
    # Simple formatting logic if needed
    for c in courses:
        if c.master:
            c.master_name = c.master.full_name
    return courses

@router.get("/{course_id}", response_model=CourseOut)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Kurs topilmadi")
    if course.master:
        course.master_name = course.master.full_name
    return course

@router.post("/{course_id}/lessons/", response_model=LessonOut, status_code=status.HTTP_201_CREATED)
def add_lesson(
    course_id: int,
    lesson_in: LessonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Kurs topilmadi")
    
    if course.master_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Siz faqat o'z kursingizga dars qo'sha olasiz")
    
    lesson = Lesson(
        course_id=course_id,
        title=lesson_in.title,
        content=lesson_in.content,
        video_url=lesson_in.video_url,
        sequence_number=lesson_in.sequence_number
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson
