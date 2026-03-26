# ===================== SADAQAI JORIYA =====================
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DonationCreate(BaseModel):
    amount: float

class DonationOut(BaseModel):
    id: int
    user_id: int
    amount: float
    created_at: datetime

    class Config:
        from_attributes = True
