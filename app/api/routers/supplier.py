from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional

from app.core.database import get_db
from app.models.supplier import SupplierProduct, SupplierReview
from app.models.user import User, UserRole
from app.schemas.supplier_schemas import (
    SupplierProductCreate, SupplierProductUpdate, SupplierProductOut,
    SupplierReviewCreate, SupplierReviewOut,
)
from app.api.routers.users import get_current_user

router = APIRouter(
    prefix="/suppliers",
    tags=["Ta'minot Do'konlari"]
)


# ==================== MAHSULOTLAR ====================

@router.post("/products", response_model=SupplierProductOut)
def create_product(
    req: SupplierProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Do'kondor yangi mahsulot qo'shadi — manzil profildan olinadi"""
    if current_user.role != UserRole.DOKONDOR:
        raise HTTPException(403, "Faqat do'kondorlar mahsulot qo'sha oladi")

    # Manzilni profildan olish (agar mahsulotda ko'rsatilmagan bo'lsa)
    shop_address = req.shop_address or current_user.shop_address
    lat = req.lat or current_user.lat
    lng = req.lng or current_user.lng

    if not shop_address or not lat or not lng:
        raise HTTPException(400, "Avval profilingizda do'kon manzilini belgilang")

    product = SupplierProduct(
        supplier_id=current_user.id,
        name=req.name,
        shop_address=shop_address,
        lat=lat,
        lng=lng,
        description=req.description,
        price=req.price,
        brand=req.brand,
        image_url=req.image_url,
        stock_qty=req.stock_qty,
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    return _product_to_out(product, db)


@router.get("/products", response_model=List[SupplierProductOut])
def get_products(
    q: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Mahsulotlar ro'yxati (qidiruv va filtr bilan)"""
    query = db.query(SupplierProduct)
    if q:
        query = query.filter(SupplierProduct.name.ilike(f"%{q}%"))
    if category:
        query = query.filter(SupplierProduct.category == category)
    products = query.order_by(desc(SupplierProduct.created_at)).all()
    return [_product_to_out(p, db) for p in products]


@router.get("/products/me", response_model=List[SupplierProductOut])
def get_my_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Do'kondorning o'z mahsulotlari"""
    products = db.query(SupplierProduct).filter(
        SupplierProduct.supplier_id == current_user.id
    ).order_by(desc(SupplierProduct.created_at)).all()
    return [_product_to_out(p, db) for p in products]


@router.put("/products/{product_id}", response_model=SupplierProductOut)
def update_product(
    product_id: int,
    req: SupplierProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mahsulotni tahrirlash"""
    product = db.query(SupplierProduct).filter(SupplierProduct.id == product_id).first()
    if not product:
        raise HTTPException(404, "Mahsulot topilmadi")
    if product.supplier_id != current_user.id:
        raise HTTPException(403, "Faqat o'z mahsulotingizni tahrirlashingiz mumkin")

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return _product_to_out(product, db)


@router.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mahsulotni o'chirish"""
    product = db.query(SupplierProduct).filter(SupplierProduct.id == product_id).first()
    if not product:
        raise HTTPException(404, "Mahsulot topilmadi")
    if product.supplier_id != current_user.id:
        raise HTTPException(403, "Faqat o'z mahsulotingizni o'chirishingiz mumkin")

    db.delete(product)
    db.commit()
    return {"ok": True}


@router.get("/feed", response_model=List[SupplierProductOut])
def get_feed(db: Session = Depends(get_db)):
    """Yangi e'lonlar lentasi (oxirgi 50 ta)"""
    products = db.query(SupplierProduct).order_by(
        desc(SupplierProduct.created_at)
    ).limit(50).all()
    return [_product_to_out(p, db) for p in products]


# ==================== SHARHLAR / REYTING ====================

@router.post("/{supplier_id}/reviews", response_model=SupplierReviewOut)
def create_review(
    supplier_id: int,
    req: SupplierReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ustaning do'kondorga baho berishi"""
    if req.rating < 1 or req.rating > 5:
        raise HTTPException(400, "Baho 1 dan 5 gacha bo'lishi kerak")

    supplier = db.query(User).filter(User.id == supplier_id).first()
    if not supplier:
        raise HTTPException(404, "Do'kondor topilmadi")

    review = SupplierReview(
        reviewer_id=current_user.id,
        supplier_id=supplier_id,
        rating=req.rating,
        comment=req.comment,
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    out = SupplierReviewOut.model_validate(review)
    out.reviewer_name = current_user.full_name
    return out


@router.get("/{supplier_id}/reviews", response_model=List[SupplierReviewOut])
def get_reviews(supplier_id: int, db: Session = Depends(get_db)):
    """Do'kondor sharhlari"""
    reviews = db.query(SupplierReview).filter(
        SupplierReview.supplier_id == supplier_id
    ).order_by(desc(SupplierReview.created_at)).all()

    result = []
    for r in reviews:
        out = SupplierReviewOut.model_validate(r)
        reviewer = db.query(User).filter(User.id == r.reviewer_id).first()
        out.reviewer_name = reviewer.full_name if reviewer else "Noma'lum"
        result.append(out)
    return result


@router.get("/top")
def get_top_suppliers(db: Session = Depends(get_db)):
    """Eng halol do'konlar reytingi"""
    results = db.query(
        SupplierReview.supplier_id,
        func.avg(SupplierReview.rating).label("avg_rating"),
        func.count(SupplierReview.id).label("review_count"),
    ).group_by(SupplierReview.supplier_id).order_by(
        desc("avg_rating")
    ).limit(20).all()

    top = []
    for supplier_id, avg_rating, review_count in results:
        user = db.query(User).filter(User.id == supplier_id).first()
        if user:
            top.append({
                "supplier_id": supplier_id,
                "name": user.full_name,
                "avg_rating": round(avg_rating, 1),
                "review_count": review_count,
                "shop_address": None,
            })
            # Get shop address from their first product
            product = db.query(SupplierProduct).filter(
                SupplierProduct.supplier_id == supplier_id
            ).first()
            if product:
                top[-1]["shop_address"] = product.shop_address
    return top


# ==================== HELPER ====================

def _product_to_out(product: SupplierProduct, db: Session) -> SupplierProductOut:
    """Convert product model to output schema with supplier info"""
    out = SupplierProductOut.model_validate(product)

    supplier = db.query(User).filter(User.id == product.supplier_id).first()
    out.supplier_name = supplier.full_name if supplier else "Noma'lum"

    # Calculate average rating
    avg = db.query(func.avg(SupplierReview.rating)).filter(
        SupplierReview.supplier_id == product.supplier_id
    ).scalar()
    out.supplier_rating = round(avg, 1) if avg else None

    return out
