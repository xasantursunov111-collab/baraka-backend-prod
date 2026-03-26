from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.routers.users import get_current_user
from app.models.transaction import Order, OrderStatus, RizolikDarajasi, Estimate
from app.models.guild import GuildMembership, Apprenticeship
from app.models.user import User, UserRole
from app.schemas.schemas import (
    OrderCreate, OrderOut,
    AcceptOrderRequest, ExtendDeadlineRequest, RizolikRequest, SOSAcceptRequest,
    EstimateCreate, EstimateOut
)
from app.api.routers.users import get_current_user

router = APIRouter()

# ================== Rizolik ball hisoblash ==================

RIZOLIK_SCORES = {
    RizolikDarajasi.AJOYIB: 5.0,
    RizolikDarajasi.YAXSHI: 3.0,
    RizolikDarajasi.QONIQARLI: 1.0,
    RizolikDarajasi.YOMON: -1.0,
    RizolikDarajasi.NOROZI: -3.0,
}

RANK_THRESHOLDS = [
    (50, "Pir"),       # 50+ nufuz = Pir
    (20, "Sarusta"),   # 20+ nufuz = Sarusta
    (5, "Usta"),       # 5+  nufuz = Usta
    (0, "Shogird"),    # 0+  nufuz = Shogird
]


def _recalculate_rank(membership: GuildMembership):
    """Nufuz darajasiga qarab martabani yangilash"""
    for threshold, rank in RANK_THRESHOLDS:
        if membership.nufuz >= threshold:
            membership.rank = rank
            return


# ==================== BUYURTMALAR ====================

@router.post("/orders/", response_model=OrderOut, tags=["Buyurtmalar"])
def create_order(
    order: OrderCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Yangi buyurtma yaratish (mijoz tomonidan)"""
    if current_user.id != order.client_id:
         raise HTTPException(status_code=403, detail="Boshqa foydalanuvchi nomidan buyurtma bera olmaysiz")
    client = db.query(User).filter(User.id == order.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Mijoz topilmadi")

    db_order = Order(
        client_id=order.client_id,
        title=order.title,
        description=order.description,
        price=order.price,
        deadline=order.deadline,
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


@router.get("/orders/", response_model=List[OrderOut], tags=["Buyurtmalar"])
def list_orders(status: str = None, db: Session = Depends(get_db)):
    """Buyurtmalar ro'yxati (status bo'yicha filtrlash mumkin)"""
    q = db.query(Order)
    if status:
        q = q.filter(Order.status == OrderStatus(status))
    return q.order_by(Order.created_at.desc()).all()


@router.get("/orders/{order_id}", response_model=OrderOut, tags=["Buyurtmalar"])
def get_order(order_id: int, db: Session = Depends(get_db)):
    """Bitta buyurtmani ko'rish"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    return order


@router.put("/orders/{order_id}/accept", response_model=OrderOut, tags=["Buyurtmalar"])
def accept_order(
    order_id: int, 
    req: AcceptOrderRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Usta buyurtmani qabul qiladi"""
    if current_user.id != req.master_id:
        raise HTTPException(status_code=403, detail="Buyurtmani faqat o'zingiz qabul qilishingiz mumkin")
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    if order.status != OrderStatus.YANGI:
        raise HTTPException(status_code=400, detail="Bu buyurtma allaqachon qabul qilingan")

    master = db.query(User).filter(User.id == req.master_id, User.role == UserRole.USTA).first()
    if not master:
        raise HTTPException(status_code=404, detail="Usta topilmadi")

    order.master_id = req.master_id
    order.status = OrderStatus.QABUL_QILINDI
    db.commit()
    db.refresh(order)
    return order


@router.put("/orders/{order_id}/start", response_model=OrderOut, tags=["Buyurtmalar"])
def start_order(order_id: int, db: Session = Depends(get_db)):
    """Usta ishni boshlaydi"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    if order.status != OrderStatus.QABUL_QILINDI:
        raise HTTPException(status_code=400, detail="Buyurtmani boshlash mumkin emas")
    order.status = OrderStatus.JARAYONDA
    db.commit()
    db.refresh(order)
    return order


# ==================== BAG'RIKENGLIK MODALI ====================

@router.put("/orders/{order_id}/extend", response_model=OrderOut, tags=["Bag'rikenglik"])
def extend_deadline(order_id: int, req: ExtendDeadlineRequest, db: Session = Depends(get_db)):
    """
    Bag'rikenglik modali — usta muddat so'raganda, mijoz insoniylik bilan uzaytiradi.
    Bu usta nufuziga salbiy ta'sir qilmaydi.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    if order.status not in (OrderStatus.JARAYONDA, OrderStatus.QABUL_QILINDI):
        raise HTTPException(status_code=400, detail="Muddatni uzaytirish mumkin emas")

    order.deadline = req.new_deadline
    order.is_extended = True
    order.extension_reason = req.reason
    order.status = OrderStatus.MUDDAT_UZAYTIRILDI
    
    # Ustaning bag'rikenglik so'rovlari sonini oshirish
    if order.master_id:
        master = db.query(User).filter(User.id == order.master_id).first()
        if master:
            master.bagrikenglik_requests += 1

    db.commit()
    db.refresh(order)
    return order


# ==================== BUYURTMANI YAKUNLASH ====================

@router.put("/orders/{order_id}/complete", response_model=OrderOut, tags=["Buyurtmalar"])
def complete_order(order_id: int, db: Session = Depends(get_db)):
    """Usta ishni tugatdi — endi mijoz rizolik berishi kutiladi"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    if order.status not in (OrderStatus.JARAYONDA, OrderStatus.MUDDAT_UZAYTIRILDI):
        raise HTTPException(status_code=400, detail="Buyurtmani yakunlash mumkin emas")

    order.status = OrderStatus.YAKUNLANDI
    order.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(order)
    return order


# ==================== RIZOLIK EKRANI ====================

@router.put("/orders/{order_id}/rizolik", response_model=OrderOut, tags=["Rizolik"])
def give_rizolik(order_id: int, req: RizolikRequest, db: Session = Depends(get_db)):
    """
    Rizolik ekrani — buyurtma yakunlanganda mijoz ustaga baho beradi.
    Baho ustaning gildiya nufuziga ta'sir qiladi va avtomatik martaba oshiradi.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    if order.status != OrderStatus.YAKUNLANDI:
        raise HTTPException(status_code=400, detail="Faqat yakunlangan buyurtmaga rizolik berish mumkin")
    if order.rizolik is not None:
        raise HTTPException(status_code=400, detail="Bu buyurtmaga rizolik allaqachon berilgan")

    rizolik_value = RizolikDarajasi(req.rizolik)
    order.rizolik = rizolik_value
    order.rizolik_comment = req.comment

    # Usta nufuzini va reytingini yangilash
    if order.master_id:
        master = db.query(User).filter(User.id == order.master_id).first()
        if master:
            if rizolik_value in (RizolikDarajasi.AJOYIB, RizolikDarajasi.YAXSHI):
                master.baraka_count += 1
            # Halol reyting hisobi (oddiy yondashuv: oxirgi olingan ballar ta'siri)
            score_diff = RIZOLIK_SCORES.get(rizolik_value, 0)
            master.halol_rating = min(5.0, max(0.0, master.halol_rating + (score_diff * 0.1)))

        membership = (
            db.query(GuildMembership)
            .filter(GuildMembership.user_id == order.master_id)
            .first()
        )
        if membership:
            membership.nufuz += RIZOLIK_SCORES.get(rizolik_value, 0)
            _recalculate_rank(membership)

        # "Baraka zanjiri" - Agar usta shogird bo'lsa, uning ustoziga ham ozgina nufuz beramiz
        from app.models.guild import Apprenticeship
        apprenticeship = db.query(Apprenticeship).filter(Apprenticeship.apprentice_id == order.master_id).first()
        if apprenticeship:
            ustoz_membership = (
                db.query(GuildMembership)
                .filter(GuildMembership.user_id == apprenticeship.master_id)
                .first()
            )
            if ustoz_membership:
                # Ustozga shogirdining yutug'idan 50% nufuz ulushi beriladi
                ustoz_membership.nufuz += (RIZOLIK_SCORES.get(rizolik_value, 0) * 0.5)
                _recalculate_rank(ustoz_membership)

    db.commit()
    db.refresh(order)
    return order


# ==================== SOS TIZIMI ====================

@router.put("/orders/{order_id}/sos", response_model=OrderOut, tags=["Hamkorlik SOS"])
def request_sos(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Gildiya a'zolaridan yordam so'rash (SOS)"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    if current_user.id != order.master_id:
        raise HTTPException(status_code=403, detail="Faqat buyurtmani olgan usta yordam so'rashi mumkin")
    
    order.sos_requested = True
    db.commit()
    db.refresh(order)
    return order
# ==========================================
# ELEKTRON SMETA (ESTIMATE) ROUTES
# ==========================================

@router.post("/{order_id}/estimate", response_model=EstimateOut, status_code=status.HTTP_201_CREATED)
def create_estimate(
    order_id: int,
    estimate_in: EstimateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Usta mijozga smeta yuboradi
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    
    if order.master_id != current_user.id:
        raise HTTPException(status_code=403, detail="Faqat buyurtmani olgan usta smeta yuborishi mumkin")
    
    if order.status != OrderStatus.QABUL_QILINGAN:
        raise HTTPException(status_code=400, detail="Smetani faqat qabul qilingan buyurtmaga yuborish mumkin")
    
    if order.estimate:
        raise HTTPException(status_code=400, detail="Smeta allaqachon yuborilgan")

    # JSON orDict conversion for Pydantic v2
    items_data = [item.dict() for item in estimate_in.items]
    total = sum(item["price"] for item in items_data)

    estimate = Estimate(
        order_id=order.id,
        master_id=current_user.id,
        client_id=order.client_id,
        items=items_data,
        total_price=total
    )
    db.add(estimate)
    
    # Optional: orderning narxini ham smeta summasiga tenglashtirish
    order.price = total
    
    db.commit()
    db.refresh(estimate)
    return estimate


@router.put("/{order_id}/estimate/accept", response_model=OrderOut)
def accept_estimate(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mijoz smetani tasdiqlaydi. Shundan so'ng ish jarayoni boshlanadi.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    
    if order.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Faqat mijoz smetani tasdiqlay oladi")
    
    if not order.estimate:
        raise HTTPException(status_code=404, detail="Ushbu buyurtmaga hali smeta jo'natilmagan")
        
    if order.estimate.is_accepted:
        raise HTTPException(status_code=400, detail="Smeta allaqachon tasdiqlangan")

    order.estimate.is_accepted = True
    order.status = OrderStatus.JARAYONDA
    
    db.commit()
    db.refresh(order)
    return order
@router.put("/orders/{order_id}/sos/accept", response_model=OrderOut, tags=["Hamkorlik SOS"])
def accept_sos(order_id: int, req: SOSAcceptRequest, db: Session = Depends(get_db)):
    """Boshqa usta yordam berishni qabul qilishi (Gildiya Nufuzini oshiradi)"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    if not order.sos_requested:
        raise HTTPException(status_code=400, detail="Ushbu buyurtmaga yordam so'ralmagan")
    
    helper = db.query(User).filter(User.id == req.helper_id).first()
    if not helper:
        raise HTTPException(status_code=404, detail="Yordamchi usta topilmadi")
    
    order.sos_requested = False
    order.sos_helper_id = req.helper_id
    
    # Yordam bergan usta (helper) nufuzini oshirish (+5 nufuz)
    helper_membership = db.query(GuildMembership).filter(GuildMembership.user_id == req.helper_id).first()
    if helper_membership:
        helper_membership.nufuz += 5.0
        _recalculate_rank(helper_membership)

    db.commit()
    db.refresh(order)
    return order

# ==================== STATISTIKA ====================

@router.get("/masters/{master_id}/stats", tags=["Statistika"])
def get_master_stats(master_id: int, db: Session = Depends(get_db)):
    """Ustaning buyurtmalar statistikasi"""
    total = db.query(Order).filter(Order.master_id == master_id).count()
    completed = db.query(Order).filter(
        Order.master_id == master_id, Order.status == OrderStatus.YAKUNLANDI
    ).count()
    membership = db.query(GuildMembership).filter(GuildMembership.user_id == master_id).first()

    return {
        "master_id": master_id,
        "total_orders": total,
        "completed_orders": completed,
        "nufuz": membership.nufuz if membership else 0,
        "rank": membership.rank if membership else "Hali gildiyaga a'zo emas",
    }
