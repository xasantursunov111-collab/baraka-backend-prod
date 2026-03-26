import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.user import User
from app.models.gallery import GalleryItem

router = APIRouter()

# Rasmlar saqlanadigan papka
UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def _save_file(file: UploadFile) -> str:
    """Faylni saqlash va URL qaytarish"""
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Faqat rasm fayllari ruxsat etilgan: {', '.join(ALLOWED_EXTENSIONS)}")

    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / unique_name
    content = file.file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Fayl hajmi 5 MB dan oshmasligi kerak")

    with open(file_path, "wb") as f:
        f.write(content)

    return f"/uploads/{unique_name}"


# ==================== UMUMIY FAYL YUKLASH ====================

@router.post("/upload", tags=["Rasm yuklash"])
def upload_general_file(file: UploadFile = File(...)):
    """Istalgan joy uchun umumiy fayl yuklash (Smeta, Product, va h.k.)"""
    url = _save_file(file)
    return {"url": url}


# ==================== AVATAR YUKLASH ====================

@router.post("/users/{user_id}/avatar", tags=["Rasm yuklash"])
def upload_avatar(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Foydalanuvchi avatarini yuklash"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

    url = _save_file(file)
    user.avatar_url = url
    db.commit()
    db.refresh(user)

    return {"message": "Avatar muvaffaqiyatli yuklandi", "avatar_url": url}


# ==================== GALERIYA ====================

@router.post("/gallery/", tags=["Galeriya"])
def upload_gallery_item(
    user_id: int = Form(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Usta ishlari galereyasiga yangi rasm qo'shish"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

    url = _save_file(file)

    item = GalleryItem(
        user_id=user_id,
        image_url=url,
        title=title,
        description=description,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return {
        "id": item.id,
        "user_id": item.user_id,
        "image_url": item.image_url,
        "title": item.title,
        "description": item.description,
        "created_at": item.created_at.isoformat(),
    }


@router.get("/gallery/user/{user_id}", tags=["Galeriya"])
def get_user_gallery(user_id: int, db: Session = Depends(get_db)):
    """Foydalanuvchining barcha galeriya rasmlarini olish"""
    items = db.query(GalleryItem).filter(GalleryItem.user_id == user_id).order_by(GalleryItem.created_at.desc()).all()
    return [
        {
            "id": i.id,
            "image_url": i.image_url,
            "title": i.title,
            "description": i.description,
            "created_at": i.created_at.isoformat(),
        }
        for i in items
    ]


@router.delete("/gallery/{item_id}", tags=["Galeriya"])
def delete_gallery_item(item_id: int, db: Session = Depends(get_db)):
    """Galeriya rasmini o'chirish"""
    item = db.query(GalleryItem).filter(GalleryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Rasm topilmadi")

    # Faylni diskdan o'chirish
    file_path = UPLOAD_DIR / Path(item.image_url).name
    if file_path.exists():
        os.remove(file_path)

    db.delete(item)
    db.commit()
    return {"message": "Rasm muvaffaqiyatli o'chirildi"}
