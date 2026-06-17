"""
BARAKA — Yangi funksiyalar API Router
Dashboard, Bildirishnomalar, Sertifikatlar, Kalendar, Smart Qidiruv
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel
import random, string, os
import edge_tts
from dotenv import load_dotenv

load_dotenv()

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.transaction import Order
from app.models.supplier import SupplierProduct, SupplierReview
from app.models.extras import Notification, Certificate, ScheduleSlot, NotificationType
from app.models.academy import Course
from app.api.routers.users import get_current_user

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

router = APIRouter(tags=["Yangi Funksiyalar"])


# ===================== SCHEMAS =====================

class NotificationOut(BaseModel):
    id: int
    type: str
    title: str
    message: Optional[str] = None
    is_read: bool = False
    link: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class CertificateOut(BaseModel):
    id: int
    user_id: int
    course_id: int
    cert_code: str
    issued_at: datetime
    course_name: Optional[str] = None
    user_name: Optional[str] = None
    class Config:
        from_attributes = True

class ScheduleSlotIn(BaseModel):
    date: date
    is_busy: bool = True
    note: Optional[str] = None

class ScheduleSlotOut(BaseModel):
    id: int
    date: date
    is_busy: bool
    note: Optional[str] = None
    class Config:
        from_attributes = True

class ChatMessageIn(BaseModel):
    role: str
    text: str

class ChatRequest(BaseModel):
    history: List[ChatMessageIn]
    new_message: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    user_name: Optional[str] = None

# ==================== DASHBOARD ====================

@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Foydalanuvchi statistikasi"""
    user_id = current_user.id
    role = current_user.role

    stats = {
        "user": {
            "id": user_id,
            "name": current_user.full_name,
            "role": role.value,
            "baraka_count": current_user.baraka_count,
            "halol_rating": current_user.halol_rating,
        }
    }

    if role == UserRole.USTA:
        total_orders = db.query(func.count(Order.id)).filter(Order.master_id == user_id).scalar() or 0
        completed = db.query(func.count(Order.id)).filter(
            and_(Order.master_id == user_id, Order.status == "YAKUNLANDI")
        ).scalar() or 0
        total_earnings = db.query(func.sum(Order.price)).filter(
            and_(Order.master_id == user_id, Order.status == "YAKUNLANDI")
        ).scalar() or 0
        stats["orders"] = {"total": total_orders, "completed": completed}
        stats["earnings"] = total_earnings

    elif role == UserRole.MIJOZ:
        total_orders = db.query(func.count(Order.id)).filter(Order.client_id == user_id).scalar() or 0
        stats["orders"] = {"total": total_orders}

    elif role == UserRole.DOKONDOR:
        total_products = db.query(func.count(SupplierProduct.id)).filter(
            SupplierProduct.supplier_id == user_id
        ).scalar() or 0
        avg_rating = db.query(func.avg(SupplierReview.rating)).filter(
            SupplierReview.supplier_id == user_id
        ).scalar()
        review_count = db.query(func.count(SupplierReview.id)).filter(
            SupplierReview.supplier_id == user_id
        ).scalar() or 0
        stats["products"] = total_products
        stats["rating"] = {"avg": round(avg_rating, 1) if avg_rating else 0, "count": review_count}

    # Bildirishnomalar soni
    unread = db.query(func.count(Notification.id)).filter(
        and_(Notification.user_id == user_id, Notification.is_read == False)
    ).scalar() or 0
    stats["unread_notifications"] = unread

    return stats


# ==================== BILDIRISHNOMALAR ====================

@router.get("/notifications", response_model=List[NotificationOut])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Foydalanuvchi bildirishnomalari"""
    return db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(desc(Notification.created_at)).limit(50).all()


@router.put("/notifications/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Barcha bildirishnomalarni o'qilgan deb belgilash"""
    db.query(Notification).filter(
        and_(Notification.user_id == current_user.id, Notification.is_read == False)
    ).update({"is_read": True})
    db.commit()
    return {"ok": True}


@router.get("/notifications/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = db.query(func.count(Notification.id)).filter(
        and_(Notification.user_id == current_user.id, Notification.is_read == False)
    ).scalar() or 0
    return {"count": count}


# ==================== SERTIFIKATLAR ====================

@router.post("/certificates/{course_id}")
def issue_certificate(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Kursni tugatgandan keyin sertifikat olish"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(404, "Kurs topilmadi")

    # Allaqachon sertifikat bor-yo'qligini tekshirish
    existing = db.query(Certificate).filter(
        and_(Certificate.user_id == current_user.id, Certificate.course_id == course_id)
    ).first()
    if existing:
        raise HTTPException(400, "Siz bu kurs bo'yicha allaqachon sertifikat olgansiz")

    code = f"BARAKA-{datetime.utcnow().year}-{''.join(random.choices(string.digits, k=5))}"
    cert = Certificate(
        user_id=current_user.id,
        course_id=course_id,
        cert_code=code,
    )
    db.add(cert)

    # Bildirishnoma yaratish
    notif = Notification(
        user_id=current_user.id,
        type=NotificationType.SYSTEM,
        title="Sertifikat olindi! 🎓",
        message=f"\"{course.title}\" kursi bo'yicha sertifikat: {code}",
        link="/profile",
    )
    db.add(notif)

    db.commit()
    db.refresh(cert)
    return {"cert_code": code, "course": course.title, "issued_at": cert.issued_at}


@router.get("/certificates/me")
def my_certificates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mening sertifikatlarim"""
    certs = db.query(Certificate).filter(
        Certificate.user_id == current_user.id
    ).order_by(desc(Certificate.issued_at)).all()

    result = []
    for c in certs:
        course = db.query(Course).filter(Course.id == c.course_id).first()
        result.append({
            "id": c.id,
            "cert_code": c.cert_code,
            "course_name": course.title if course else "Noma'lum",
            "issued_at": c.issued_at,
        })
    return result


# ==================== USTA KALENDARI ====================

@router.get("/schedule/{user_id}", response_model=List[ScheduleSlotOut])
def get_schedule(
    user_id: int,
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Ustaning ish jadvali"""
    query = db.query(ScheduleSlot).filter(ScheduleSlot.user_id == user_id)
    if month and year:
        from sqlalchemy import extract
        query = query.filter(
            and_(
                extract('month', ScheduleSlot.date) == month,
                extract('year', ScheduleSlot.date) == year,
            )
        )
    return query.order_by(ScheduleSlot.date).all()


@router.post("/schedule", response_model=ScheduleSlotOut)
def add_schedule_slot(
    slot: ScheduleSlotIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Jadvalga kun qo'shish"""
    existing = db.query(ScheduleSlot).filter(
        and_(ScheduleSlot.user_id == current_user.id, ScheduleSlot.date == slot.date)
    ).first()
    if existing:
        existing.is_busy = slot.is_busy
        existing.note = slot.note
        db.commit()
        db.refresh(existing)
        return existing

    new_slot = ScheduleSlot(
        user_id=current_user.id,
        date=slot.date,
        is_busy=slot.is_busy,
        note=slot.note,
    )
    db.add(new_slot)
    db.commit()
    db.refresh(new_slot)
    return new_slot


@router.delete("/schedule/{slot_id}")
def delete_schedule_slot(
    slot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    slot = db.query(ScheduleSlot).filter(
        and_(ScheduleSlot.id == slot_id, ScheduleSlot.user_id == current_user.id)
    ).first()
    if not slot:
        raise HTTPException(404, "Topilmadi")
    db.delete(slot)
    db.commit()
    return {"ok": True}


# ==================== SMART QIDIRUV / AI TAVSIYA ====================

def generate_ai_answer(q: str) -> Optional[str]:
    """Qoidalar asosida yoki Gemini yordamida har qanday savollarga javob berish"""
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    if HAS_GENAI and gemini_key:
        try:
            genai.configure(api_key=gemini_key)
            # Use gemini-2.5-flash for general fast text tasks
            model = genai.GenerativeModel('gemini-2.5-flash')
            system_prompt = "Sen BARAKA mebel va hunarmandlar platformasining sun'iy intellekt maslahatchisisan. Sen qisqa, tushunarli va do'stona tarzda faqat o'zbek tilida javob berasan. Usta topish, ustoz-shogirdlik va mebel mavzularini qo'llab quvvatlaysan, lekin foydalanuvchining *har qanday* savoliga bemalol javob berishing mumkin."
            response = model.generate_content(f"{system_prompt}\n\nMijoz savoli: {q}")
            if response.text:
                return response.text
        except Exception as e:
            print("Gemini API Error:", e)
            pass # Fall back to rule-based 

    q_lower = q.lower()
    
    # 1. Platforma haqida
    if any(k in q_lower for k in ["baraka nima", "bu qanday platforma", "sayt qanday ishlaydi", "maqsadi nima"]):
        return "BARAKA — bu ustalar va mijozlar o'rtasida ishonch, halollik va milliy hunarmandchilik qadriyatlarini tiklovchi raqamli ekotizim. Bu yerda siz tom ma'nodagi halol ustani topishingiz yoki o'z hunaringizni halol sota olishingiz mumkin. Boshqa mavzular bo'yicha ham javob berishim uchun .env faylida GEMINI_API_KEY sozlanishi kerak."
    
    # 2. Rizolik tizimi
    if any(k in q_lower for k in ["rizolik nima", "rizolik qanday ishlaydi", "rozi bo'lish", "buyurtmani yakunlash"]):
        return "Rizolik tizimi — buyurtma yakunida mijozning ustadan qanchalik rozi bo'lganligini anglatadi. Yaxshi Rizolik olgan ustaning 'Baraka' va 'Nufuz' darajasi oshadi. Agar shogirdi bo'lsa, xatto ustoziga ham nufuz qo'shiladi."
    
    # 3. Gildiya (Kasabalar)
    if any(k in q_lower for k in ["gildiya nima", "kasabalar", "nufuz nima", "reyting qanday"]):
        return "Gildiyalar — bu ustalar birlashmasi. Gildiya a'zolari bir-biriga kafillik beradi. Ustaning Nufuzi (reytingi) u olgan Rizoliklar hamda gildiyadagi faolligi asosida oshirib boriladi."
        
    # 4. Ustoz-Shogird
    if any(k in q_lower for k in ["shogird qanday", "ustoz nima", "shogird tushish", "shogird qo'shish"]):
        return "Ustoz-Shogird an'anasida usta o'z profiliga shogirdlarini qo'shadi. Shogird yetishib chiqib yaxshi ish qilganda olgan Rizoligi uning ustoziga ham obro' (Baraka Zanjiri) olib keladi."
        
    # 5. Sadaqai Joriya
    if any(k in q_lower for k in ["sadaqa nima", "xazina", "ehson", "yordam puli"]):
        return "Sadaqai Joriya xazinasi ixtiyoriy ehsonlar hisobidan shakllanadi. U betob yoki yordamga muhtoj ustalar va ularning oilalariga ko'mak berish uchun ishlatiladi."
        
    # 6. Do'konlar va Bozor
    if any(k in q_lower for k in ["do'kon qanday", "dokondor", "mahsulot sotish", "material olish"]):
        return "Tizimda 'Do'kondor' maxsus maqomi bor. Siz o'z do'koningizni xaritada belgilab, tovarlaringiz (furnitura, materiallar)ni yuklashingiz mumkin. Ustalarga kerakli materialni to'g'ridan to'g'ri sotish imkonini beradi."
    
    # 7. Oddiy salomlashish
    if any(k in q_lower for k in ["salom", "assalom", "qalay"]):
        return "Assalomu alaykum! BARAKA platformasiga xush kelibsiz! Sizga qanday yordam bera olaman?"
        
    return "Sizning so'rovingiz bo'yicha bazamizdan quyidagi maqbul usta va qiziqarli do'konlarni qidirib topdim. Ro'yxat bilan tanishib chiqing!"

@router.get("/recommend")
def get_recommendations(
    q: str,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    db: Session = Depends(get_db),
):
    """Aqlli qidiruv — mos ustalar va materiallar"""
    search = f"%{q}%"

    # Mos ustalar
    masters = db.query(User).filter(
        and_(User.role == UserRole.USTA, User.bio.ilike(search))
    ).order_by(desc(User.halol_rating)).limit(5).all()

    master_list = []
    for m in masters:
        distance = None
        if lat and lng and m.lat and m.lng:
            distance = round(((m.lat - lat)**2 + (m.lng - lng)**2)**0.5 * 111, 1)  # km (approximate)
        master_list.append({
            "id": m.id, "name": m.full_name, "bio": m.bio,
            "rating": m.halol_rating, "baraka": m.baraka_count,
            "distance_km": distance,
        })

    # Mos mahsulotlar
    products = db.query(SupplierProduct).filter(
        SupplierProduct.name.ilike(search)
    ).order_by(desc(SupplierProduct.created_at)).limit(5).all()

    product_list = [{
        "id": p.id, "name": p.name, "price": p.price,
        "shop_address": p.shop_address, "brand": p.brand,
    } for p in products]
    
    # Platforma bo'yicha aqlli javob
    ai_answer = generate_ai_answer(q)
    
    # Agar AI javob ham yo'q, va hech narsa topilmasa
    tip = f"'{q}' bo'yicha {len(master_list)} ta usta va {len(product_list)} ta mahsulot topildi."
    if ai_answer:
        tip = "Sizni qiziqtirgan savolga javob berishga harakat qildim."

    return {
        "query": q,
        "ai_answer": ai_answer,
        "masters": master_list,
        "products": product_list,
        "tip": tip
    }


@router.post("/ai-chat")
def ai_chat_endpoint(
    req: ChatRequest,
    db: Session = Depends(get_db),
):
    """Kontekstni saqlaydigan haqiqiy AI chat endpointi"""
    q = req.new_message
    
    # 1. Mahsulot va ustalarni oddiy matnli izlash (faqat oxirgi xabardan)
    search = f"%{q}%"
    masters = db.query(User).filter(
        and_(User.role == UserRole.USTA, User.bio.ilike(search))
    ).order_by(desc(User.halol_rating)).limit(3).all()

    master_list = []
    for m in masters:
        master_list.append({
            "id": m.id, "name": m.full_name, "bio": m.bio,
            "rating": m.halol_rating
        })

    products = db.query(SupplierProduct).filter(
        SupplierProduct.name.ilike(search)
    ).order_by(desc(SupplierProduct.created_at)).limit(3).all()

    product_list = [{
        "id": p.id, "name": p.name, "price": p.price,
        "shop_address": p.shop_address, "brand": p.brand,
    } for p in products]
    
    # 2. AI chat 
    ai_answer = ""
    gemini_key = os.getenv("GEMINI_API_KEY")
    if HAS_GENAI and gemini_key:
        try:
            genai.configure(api_key=gemini_key)
            
            # Tarixni moslashtirish
            formatted_history = []
            for msg in req.history:
                formatted_history.append({
                    "role": "model" if msg.role == "model" else "user",
                    "parts": [msg.text]
                })

            # Haqiqiy bazadagi holatni olish
            total_masters = db.query(func.count(User.id)).filter(User.role == UserRole.USTA).scalar() or 0
            best_master = db.query(User).filter(User.role == UserRole.USTA).order_by(desc(User.halol_rating)).first()
            best_master_info = f"Eng zo'r usta: {best_master.full_name} (Reytingi {round(best_master.halol_rating, 1)}). " if best_master else ""
            total_products = db.query(func.count(SupplierProduct.id)).scalar() or 0
            total_orders = db.query(func.count(Order.id)).scalar() or 0
            
            user_ctx = f"Mijozning ismi: {req.user_name}. Unga albatta o'z ismi bilan do'stona murojaat qil." if req.user_name else "Mijoz tizimga kirmagan mehmon."
            
            sys_info = f"Sening isming Hasan. Sen BARAKA platformasining AI yordamchisisan. {user_ctx} Tizimda: {total_masters} ta usta, {total_products} ta mahsulot bor. VAZIFANG: Foydalanuvchiga O'TA XUSHMUOMALA, yuksak ehtirom bilan, doimo 'Siz' deb murojaat qilib, sof o'zbek adabiy tilida qisqa javob berish. Aslo 'sen' deb sansiramagin! Suhbat davomida samimiy va hurmat bilan suhbatdosh bo'l. Hech qanday rus yoki ingliz so'zlarini ishlatma, suhbat kontekstini ulab ket."
            model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=sys_info)
            chat = model.start_chat(history=formatted_history)
            response = chat.send_message(q)
            
            if response.text:
                ai_answer = response.text
        except Exception as e:
            err_str = str(e).lower()
            if "429" in err_str or "quota" in err_str:
                # Limit tugaganda ham tabiiy javob bilan uzilishsiz ishlash
                ai_answer = "Kechirasiz, rosti hozir ozgina charchab qoldim. Keling, hozircha siz so'ragan narsalarni tizimimizdan shunchaki oddiy qidirib beraman."
            else:
                ai_answer = generate_ai_answer(q) # Fallback to user-friendly local logic
    else:
        ai_answer = generate_ai_answer(q)
        
    return {
        "answer": ai_answer,
        "masters": master_list,
        "products": product_list
    }


@router.get("/tts")
async def synthesize_speech(text: str):
    """
    Microsoft Edge Neural TTS yordamida haqiqiy inson kabi gapiruvchi audio generatsiya qiladi.
    Audio MP3 formatida qaytariladi.
    """
    try:
        text = text.replace("0 ta", "nol ta").replace(" 0 ", " nol ").replace("0", "nol")
        
        # Collect all audio chunks into memory (Vercel serverless doesn't support true streaming)
        communicate = edge_tts.Communicate(text, "uz-UZ-SardorNeural")
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        if not audio_data:
            raise HTTPException(status_code=500, detail="Audio generatsiya qilinmadi")
        
        from fastapi.responses import Response
        return Response(content=audio_data, media_type="audio/mpeg")
    except Exception as e:
        print("TTS Error:", e)
        raise HTTPException(status_code=500, detail="Ovozli xatolik yuz berdi")



# ==================== YAQIN USTALAR (GEO) ====================

@router.get("/nearby-masters")
def nearby_masters(
    lat: float,
    lng: float,
    radius: float = 10,  # km
    db: Session = Depends(get_db),
):
    """Yaqin atrofdagi ustalar (GPS koordinatalari bo'yicha)"""
    masters = db.query(User).filter(
        and_(User.role == UserRole.USTA, User.lat.isnot(None), User.lng.isnot(None))
    ).all()

    nearby = []
    for m in masters:
        dist = ((m.lat - lat)**2 + (m.lng - lng)**2)**0.5 * 111  # approximate km
        if dist <= radius:
            nearby.append({
                "id": m.id, "name": m.full_name, "bio": m.bio,
                "lat": m.lat, "lng": m.lng,
                "distance_km": round(dist, 1),
                "rating": m.halol_rating, "baraka": m.baraka_count,
            })

    nearby.sort(key=lambda x: x["distance_km"])
    return nearby[:20]


# ==================== KENGAYTIRILGAN QIDIRUV ====================

@router.get("/search/masters")
def search_masters(
    q: Optional[str] = None,
    sort: Optional[str] = "rating",  # rating, baraka, name
    min_rating: Optional[float] = None,
    db: Session = Depends(get_db),
):
    """Kengaytirilgan usta qidiruv + filtrlar"""
    query = db.query(User).filter(User.role == UserRole.USTA)

    if q:
        search = f"%{q}%"
        query = query.filter(
            (User.full_name.ilike(search)) | (User.bio.ilike(search))
        )

    if min_rating:
        query = query.filter(User.halol_rating >= min_rating)

    if sort == "rating":
        query = query.order_by(desc(User.halol_rating))
    elif sort == "baraka":
        query = query.order_by(desc(User.baraka_count))
    elif sort == "name":
        query = query.order_by(User.full_name)
    else:
        query = query.order_by(desc(User.halol_rating))

    masters = query.limit(50).all()
    return [{
        "id": m.id, "name": m.full_name, "bio": m.bio,
        "rating": m.halol_rating, "baraka": m.baraka_count,
        "lat": m.lat, "lng": m.lng, "avatar_url": m.avatar_url,
    } for m in masters]
