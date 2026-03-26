from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.market import Material, MaterialRequest, MaterialRequestItem
from app.models.user import User, UserRole
from app.schemas.schemas import MaterialOut, MaterialRequestCreate, MaterialRequestOut
from app.api.routers.users import get_current_user

router = APIRouter(
    prefix="/market",
    tags=["Xom-ashyo Bozori"]
)

@router.get("/materials", response_model=List[MaterialOut])
def get_materials(db: Session = Depends(get_db)):
    """Aktiv materiallar ro'yxati (Ustalar uchun vitrina)"""
    return db.query(Material).filter(Material.is_active == True).all()


@router.post("/requests", response_model=MaterialRequestOut, status_code=status.HTTP_201_CREATED)
def create_material_request(
    req_in: MaterialRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Savatdagi mahsulotlarni adminga yetkazib berish uchun jo'natish (Faqat Ustalar uchun)"""
    if current_user.role != UserRole.USTA:
        raise HTTPException(status_code=403, detail="Xarid qilish faqat ustalar uchun yopiq bozordir")
    
    if not req_in.items:
        raise HTTPException(status_code=400, detail="Savat bo'sh")

    total = 0.0
    db_items = []
    
    # Yangi so'rov yaratish
    db_request = MaterialRequest(
        master_id=current_user.id,
        delivery_address=req_in.delivery_address,
        total_price=0.0
    )
    db.add(db_request)
    db.flush() # ID olish uchun
    
    for item_in in req_in.items:
        material = db.query(Material).filter(Material.id == item_in.material_id, Material.is_active == True).first()
        if not material:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Material ID {item_in.material_id} mavjud emas yoki noaktiv")
        
        cost = item_in.quantity * material.price
        total += cost
        
        db_item = MaterialRequestItem(
            request_id=db_request.id,
            material_id=material.id,
            quantity=item_in.quantity,
            price=material.price
        )
        db.add(db_item)
        db_items.append(db_item)

    db_request.total_price = total
    db.commit()
    db.refresh(db_request)
    return db_request


@router.get("/requests/me", response_model=List[MaterialRequestOut])
def get_my_material_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """O'zimning buyurtmalarim tarixini ko'rish"""
    return db.query(MaterialRequest).filter(MaterialRequest.master_id == current_user.id).order_by(MaterialRequest.created_at.desc()).all()
