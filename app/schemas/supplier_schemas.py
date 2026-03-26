from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# ===================== SUPPLIER PRODUCT =====================

class SupplierProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None
    stock_qty: Optional[int] = None
    # Manzil ixtiyoriy — profildan olinadi
    shop_address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class SupplierProductUpdate(BaseModel):
    name: Optional[str] = None
    shop_address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    description: Optional[str] = None
    price: Optional[float] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None
    stock_qty: Optional[int] = None


class SupplierProductOut(BaseModel):
    id: int
    supplier_id: int
    name: str
    shop_address: str
    lat: float
    lng: float
    description: Optional[str] = None
    price: Optional[float] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None
    stock_qty: Optional[int] = None
    created_at: datetime
    supplier_name: Optional[str] = None
    supplier_rating: Optional[float] = None

    class Config:
        from_attributes = True


# ===================== SUPPLIER REVIEW =====================

class SupplierReviewCreate(BaseModel):
    rating: int  # 1-5
    comment: Optional[str] = None


class SupplierReviewOut(BaseModel):
    id: int
    reviewer_id: int
    supplier_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    reviewer_name: Optional[str] = None

    class Config:
        from_attributes = True
