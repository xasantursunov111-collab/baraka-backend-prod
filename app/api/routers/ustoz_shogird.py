from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.routers.users import get_current_user
from app.models.user import User, UserRole
from app.models.guild import Apprenticeship
from app.models.transaction import Order, OrderStatus

router = APIRouter(tags=["Ustoz-Shogird tizimi"])

@router.get("/ustoz-shogird/dashboard")
def get_jamoa_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ustoz uchun Jamoa Dashboard
    Shogirdlarning ishlari va erishgan natijalari (Rizolik, Baraka) xulosasi
    """
    if current_user.role != UserRole.USTA:
        raise HTTPException(status_code=403, detail="Faqat Ustalar jamoa dashboardini ko'ra oladi")

    # Ustaning shogirdlarini topish
    apprenticeships = db.query(Apprenticeship).filter(Apprenticeship.master_id == current_user.id).all()
    
    dashboard_data = []
    
    for app_link in apprenticeships:
        shogird = db.query(User).filter(User.id == app_link.apprentice_id).first()
        if not shogird:
            continue
            
        # Shogirdning buyurtmalari
        orders = db.query(Order).filter(Order.master_id == shogird.id).all()
        
        active_orders = [o for o in orders if o.status in (OrderStatus.JARAYONDA, OrderStatus.MUDDAT_UZAYTIRILDI)]
        completed_orders = [o for o in orders if o.status == OrderStatus.YAKUNLANDI]
        
        dashboard_data.append({
            "shogird_id": shogird.id,
            "shogird_name": shogird.full_name,
            "halol_rating": shogird.halol_rating,
            "baraka_count": shogird.baraka_count,
            "active_orders_count": len(active_orders),
            "completed_orders_count": len(completed_orders),
            "recent_orders": [
                {
                    "id": o.id,
                    "title": o.title,
                    "status": o.status.value,
                    "rizolik": o.rizolik.value if o.rizolik else None,
                    "is_extended": o.is_extended
                } for o in sorted(orders, key=lambda x: x.created_at, reverse=True)[:5]
            ]
        })
        
    return {
        "ustoz": {
            "id": current_user.id,
            "name": current_user.full_name,
            "baraka_count": current_user.baraka_count,
            "shogirdlar_soni": len(dashboard_data)
        },
        "jamoa": dashboard_data
    }
