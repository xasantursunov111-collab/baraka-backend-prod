from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


# ===================== USER SCHEMAS =====================

class UserCreate(BaseModel):
    full_name: str
    phone: str
    password: str
    role: Optional[str] = "MIJOZ"
    bio: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    shop_address: Optional[str] = None


class UserOut(BaseModel):
    id: int
    full_name: str
    phone: str
    role: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    shop_address: Optional[str] = None
    baraka_count: int = 0
    halol_rating: float = 0.0
    bagrikenglik_requests: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


# ===================== GUILD SCHEMAS =====================

class GuildCreate(BaseModel):
    name: str
    description: Optional[str] = None


class GuildOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GuildMembershipOut(BaseModel):
    id: int
    user_id: int
    guild_id: int
    rank: str
    nufuz: float
    joined_at: datetime

    class Config:
        from_attributes = True


class JoinGuildRequest(BaseModel):
    user_id: int
    guild_id: int


# ===================== APPRENTICESHIP SCHEMAS =====================

class ApprenticeshipCreate(BaseModel):
    master_id: int
    apprentice_id: int
    notes: Optional[str] = None


class ApprenticeshipOut(BaseModel):
    id: int
    master_id: int
    apprentice_id: int
    started_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ===================== DUO (SHARH) SCHEMAS =====================

class DuoCreate(BaseModel):
    author_id: int
    target_user_id: int
    text: str


class DuoOut(BaseModel):
    id: int
    author_id: int
    target_user_id: int
    text: str
    created_at: datetime

    class Config:
        from_attributes = True


# ===================== ORDER SCHEMAS =====================

class OrderCreate(BaseModel):
    client_id: int
    title: str
    description: Optional[str] = None
    price: Optional[float] = None
    deadline: Optional[datetime] = None


class EstimateItemSchema(BaseModel):
    name: str
    price: float

class EstimateOut(BaseModel):
    id: int
    order_id: int
    items: List[EstimateItemSchema]
    total_price: float
    is_accepted: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class EstimateCreate(BaseModel):
    items: List[EstimateItemSchema]


class OrderOut(BaseModel):
    id: int
    client_id: int
    master_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    price: Optional[float] = None
    status: str
    created_at: datetime
    deadline: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    is_extended: bool
    rizolik: Optional[str] = None
    rizolik_comment: Optional[str] = None
    sos_requested: bool = False
    sos_helper_id: Optional[int] = None
    estimate: Optional[EstimateOut] = None

    class Config:
        from_attributes = True


class AcceptOrderRequest(BaseModel):
    master_id: int


class ExtendDeadlineRequest(BaseModel):
    """Bag'rikenglik modali — muddat uzaytirish so'rovi"""
    new_deadline: datetime
    reason: str


class RizolikRequest(BaseModel):
    rizolik: str  # AJOYIB, YAXSHI, QONIQARLI, YOMON, NOROZI
    comment: Optional[str] = None


class SOSAcceptRequest(BaseModel):
    helper_id: int


# ===================== AUTH SCHEMAS =====================

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None


# ===================== HUNAR AKADEMIYASI =====================

class LessonCreate(BaseModel):
    title: str
    content: Optional[str] = None
    video_url: Optional[str] = None
    sequence_number: int = 1

class LessonOut(BaseModel):
    id: int
    course_id: int
    title: str
    content: Optional[str] = None
    video_url: Optional[str] = None
    sequence_number: int

    class Config:
        from_attributes = True

class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    price: float = 0.0

class CourseOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    master_id: int
    price: float
    created_at: datetime
    lessons: List[LessonOut] = []

    class Config:
        from_attributes = True

# ===================== XAVFSIZ RIZOLIK CHATI =====================

class ChatMessageCreate(BaseModel):
    text: Optional[str] = None
    image_url: Optional[str] = None

class ChatMessageOut(BaseModel):
    id: int
    order_id: int
    sender_id: int
    receiver_id: Optional[int] = None
    text: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime
    is_mine: Optional[bool] = None

    class Config:
        from_attributes = True
# ===================== XOM-ASHYO BOZORI (B2B MARKET) =====================

class MaterialOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class RequestItemSchema(BaseModel):
    material_id: int
    quantity: float

class MaterialRequestCreate(BaseModel):
    delivery_address: str
    items: List[RequestItemSchema]

class MaterialRequestItemOut(BaseModel):
    id: int
    material: MaterialOut
    quantity: float
    price: float

    class Config:
        from_attributes = True

class MaterialRequestOut(BaseModel):
    id: int
    master_id: int
    status: str
    total_price: float
    delivery_address: str
    admin_notes: Optional[str] = None
    created_at: datetime
    items: List[MaterialRequestItemOut] = []

    class Config:
        from_attributes = True
