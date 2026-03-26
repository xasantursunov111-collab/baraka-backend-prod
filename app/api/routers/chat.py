from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.chat import ChatMessage
from app.models.transaction import Order
from app.models.user import User
from app.schemas.schemas import ChatMessageCreate, ChatMessageOut
from app.api.routers.users import get_current_user

router = APIRouter(
    prefix="/orders",
    tags=["Chat"]
)

@router.get("/{order_id}/messages", response_model=List[ChatMessageOut])
def get_order_messages(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    
    if current_user.id not in [order.client_id, order.master_id]:
        raise HTTPException(status_code=403, detail="Siz faqat o'zingizning buyurtmangiz chatini ko'ra olasiz")

    messages = db.query(ChatMessage).filter(ChatMessage.order_id == order_id).order_by(ChatMessage.created_at.asc()).all()
    
    # Mark which ones are mine for the frontend
    for m in messages:
        m.is_mine = (m.sender_id == current_user.id)

    return messages

@router.post("/{order_id}/messages", response_model=ChatMessageOut, status_code=status.HTTP_201_CREATED)
def send_message(
    order_id: int,
    msg_in: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not msg_in.text and not msg_in.image_url:
        raise HTTPException(status_code=400, detail="Xabar matni yoki rasm yuborilishi shart")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    
    if current_user.id not in [order.client_id, order.master_id]:
        raise HTTPException(status_code=403, detail="Siz ushbu chatga xabar yoza olmaysiz")

    receiver_id = order.master_id if current_user.id == order.client_id else order.client_id

    message = ChatMessage(
        order_id=order_id,
        sender_id=current_user.id,
        receiver_id=receiver_id,
        text=msg_in.text,
        image_url=msg_in.image_url
    )
    
    db.add(message)
    db.commit()
    db.refresh(message)
    
    # Mark as mine so the sender immediately gets the right flag back
    message.is_mine = True
    return message
