from jose import jwt, JWTError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List
from app.core import security
from app.core.config import settings

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.guild import Guild, GuildMembership, Apprenticeship, Duo
from app.schemas.schemas import (
    UserCreate, UserOut, UserUpdate,
    GuildCreate, GuildOut, GuildMembershipOut, JoinGuildRequest,
    ApprenticeshipCreate, ApprenticeshipOut,
    DuoCreate, DuoOut,
)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user


# ==================== FOYDALANUVCHILAR ====================

@router.post("/users/", response_model=UserOut, tags=["Foydalanuvchilar"])
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Yangi foydalanuvchi (mijoz, usta yoki shogird) ro'yxatdan o'tkazish"""
    existing = db.query(User).filter(User.phone == user.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu telefon raqam allaqachon ro'yxatdan o'tgan")
    db_user = User(
        full_name=user.full_name,
        phone=user.phone,
        hashed_password=security.get_password_hash(user.password),
        role=UserRole(user.role),
        bio=user.bio,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/users/", response_model=List[UserOut], tags=["Foydalanuvchilar"])
def list_users(role: str = None, db: Session = Depends(get_db)):
    """Barcha foydalanuvchilarni ko'rish, role bo'yicha filtrlash mumkin"""
    q = db.query(User)
    if role:
        q = q.filter(User.role == UserRole(role))
    return q.all()

@router.get("/users/me", response_model=UserOut, tags=["Foydalanuvchilar"])
def get_user_me(current_user: User = Depends(get_current_user)):
    """Joriy avtorizatsiyadan o'tgan foydalanuvchini olish"""
    return current_user


@router.get("/users/{user_id}", response_model=UserOut, tags=["Foydalanuvchilar"])
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Bitta foydalanuvchi profilini ko'rish"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    return user


@router.put("/users/me", response_model=UserOut, tags=["Foydalanuvchilar"])
def update_my_profile(
    update_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """O'z profilini yangilash (lokatsiya, ism, bio)"""
    if update_data.full_name is not None:
        current_user.full_name = update_data.full_name
    if update_data.bio is not None:
        current_user.bio = update_data.bio
    if update_data.avatar_url is not None:
        current_user.avatar_url = update_data.avatar_url
    if update_data.lat is not None:
        current_user.lat = update_data.lat
    if update_data.lng is not None:
        current_user.lng = update_data.lng
    if update_data.shop_address is not None:
        current_user.shop_address = update_data.shop_address

    db.commit()
    db.refresh(current_user)
    return current_user


# ==================== USTA PROFILI ====================

@router.get("/masters/{user_id}/profile", tags=["Usta Profili"])
def get_master_profile(user_id: int, db: Session = Depends(get_db)):
    """
    Usta profili — gildiya o'rni, nufuz, shogirdlar va duolar bilan birga
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

    membership = db.query(GuildMembership).filter(GuildMembership.user_id == user_id).first()
    apprentices = db.query(Apprenticeship).filter(Apprenticeship.master_id == user_id).all()
    duolar = db.query(Duo).filter(Duo.target_user_id == user_id).all()

    return {
        "user": UserOut.model_validate(user),
        "guild": {
            "guild_id": membership.guild_id if membership else None,
            "rank": membership.rank if membership else None,
            "nufuz": membership.nufuz if membership else 0,
        },
        "shogirdlar_soni": len(apprentices),
        "duolar": [DuoOut.model_validate(d) for d in duolar],
    }


# ==================== GILDIYALAR ====================

@router.post("/guilds/", response_model=GuildOut, tags=["Gildiyalar"])
def create_guild(guild: GuildCreate, db: Session = Depends(get_db)):
    """Yangi gildiya yaratish"""
    db_guild = Guild(name=guild.name, description=guild.description)
    db.add(db_guild)
    db.commit()
    db.refresh(db_guild)
    return db_guild


@router.get("/guilds/", response_model=List[GuildOut], tags=["Gildiyalar"])
def list_guilds(db: Session = Depends(get_db)):
    """Barcha gildiyalar ro'yxati"""
    return db.query(Guild).all()


@router.post("/guilds/join", response_model=GuildMembershipOut, tags=["Gildiyalar"])
def join_guild(
    req: JoinGuildRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Foydalanuvchi gildiyaga a'zo bo'ladi"""
    if current_user.id != req.user_id:
        raise HTTPException(status_code=403, detail="Faqat o'zingizni gildiyaga qo'sha olasiz")
    guild = db.query(Guild).filter(Guild.id == req.guild_id).first()
    if not guild:
        raise HTTPException(status_code=404, detail="Gildiya topilmadi")
    existing = db.query(GuildMembership).filter(GuildMembership.user_id == req.user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Foydalanuvchi allaqachon gildiyaga a'zo")
    membership = GuildMembership(user_id=req.user_id, guild_id=req.guild_id)
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


@router.get("/guilds/{guild_id}/members", response_model=List[GuildMembershipOut], tags=["Gildiyalar"])
def list_guild_members(guild_id: int, db: Session = Depends(get_db)):
    """Gildiya a'zolarini ko'rish (reyting bo'yicha tartiblangan)"""
    return (
        db.query(GuildMembership)
        .filter(GuildMembership.guild_id == guild_id)
        .order_by(GuildMembership.nufuz.desc())
        .all()
    )


# ==================== USTOZ-SHOGIRD ====================

@router.post("/apprenticeships/", response_model=ApprenticeshipOut, tags=["Ustoz-Shogird"])
def create_apprenticeship(
    req: ApprenticeshipCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ustoz o'z shogirdini ro'yxatga oladi"""
    if current_user.id != req.master_id:
        raise HTTPException(status_code=403, detail="Faqat o'zingizga shogird qo'shishingiz mumkin")
    master = db.query(User).filter(User.id == req.master_id, User.role == UserRole.USTA).first()
    if not master:
        raise HTTPException(status_code=404, detail="Ustoz (usta) topilmadi")
    apprentice = db.query(User).filter(User.id == req.apprentice_id).first()
    if not apprentice:
        raise HTTPException(status_code=404, detail="Shogird topilmadi")

    link = Apprenticeship(
        master_id=req.master_id,
        apprentice_id=req.apprentice_id,
        notes=req.notes,
    )
    db.add(link)

    # Shogirdning rolini avtomatik o'zgartirish
    apprentice.role = UserRole.SHOGIRD
    db.commit()
    db.refresh(link)
    return link


@router.get("/apprenticeships/master/{master_id}", response_model=List[ApprenticeshipOut], tags=["Ustoz-Shogird"])
def list_apprentices(master_id: int, db: Session = Depends(get_db)):
    """Ustaning barcha shogirdlarini ko'rish"""
    return db.query(Apprenticeship).filter(Apprenticeship.master_id == master_id).all()


# ==================== DUOLAR (IJOBIY SHARHLAR) ====================

@router.post("/duolar/", response_model=DuoOut, tags=["Duolar"])
def create_duo(
    duo: DuoCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ustaga duo (ijobiy sharh) qoldirish — nufuzni oshiradi"""
    if current_user.id != duo.author_id:
        raise HTTPException(status_code=403, detail="Boshqa foydalanuvchi nomidan duo qoldira olmaysiz")
    target = db.query(User).filter(User.id == duo.target_user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

    db_duo = Duo(
        author_id=duo.author_id,
        target_user_id=duo.target_user_id,
        text=duo.text,
    )
    db.add(db_duo)

    # Nufuzni oshirish (+1 har bir duo uchun)
    membership = db.query(GuildMembership).filter(GuildMembership.user_id == duo.target_user_id).first()
    if membership:
        membership.nufuz += 1.0

    db.commit()
    db.refresh(db_duo)
    return db_duo


@router.get("/duolar/", response_model=List[DuoOut], tags=["Duolar"])
def list_global_duolar(db: Session = Depends(get_db)):
    """Ochiq duolar kitobi uchun barcha eng so'nggi duolarni chiqarib beradi"""
    return db.query(Duo).order_by(Duo.created_at.desc()).limit(100).all()


@router.get("/duolar/user/{user_id}", response_model=List[DuoOut], tags=["Duolar"])
def list_duolar_for_user(user_id: int, db: Session = Depends(get_db)):
    """Foydalanuvchiga berilgan barcha duolar"""
    return db.query(Duo).filter(Duo.target_user_id == user_id).all()
