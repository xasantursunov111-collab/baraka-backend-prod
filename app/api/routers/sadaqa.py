from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.core.database import get_db
from app.models.sadaqa import Donation
from app.models.user import User
from app.schemas.sadaqa import DonationCreate, DonationOut
from app.api.routers.users import get_current_user

router = APIRouter(
    prefix="/sadaqa",
    tags=["Sadaqai Joriya"]
)

@router.post("/donations", response_model=DonationOut)
def create_donation(
    req: DonationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Baraka xazinasiga inoyat qilish"""
    donation = Donation(user_id=current_user.id, amount=req.amount)
    db.add(donation)
    db.commit()
    db.refresh(donation)
    return donation

@router.get("/total")
def get_total_donations(db: Session = Depends(get_db)):
    """Jami yig'ilgan xazina miqdorini olish"""
    total = db.query(func.sum(Donation.amount)).scalar()
    return {"total": total or 0.0}
