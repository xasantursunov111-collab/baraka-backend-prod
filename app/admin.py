from sqladmin import ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
import os
from dotenv import load_dotenv

from app.models.user import User, UserRole
from app.models.guild import Guild, GuildMembership, Apprenticeship, Duo
from app.models.transaction import Order
from app.models.gallery import GalleryItem
from app.models.academy import Course, Lesson
from app.models.chat import ChatMessage
from app.models.market import Material, MaterialRequest, MaterialRequestItem
from app.models.sadaqa import Donation
from app.models.supplier import SupplierProduct, SupplierReview
from app.core.security import verify_password, get_password_hash
from app.core.database import SessionLocal

load_dotenv()

# Admin authentication using itsdangerous could be done, but simple session is enough 
# in sqladmin.
class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        # Basic admin login verification
        # Retrieve user from DB
        db = SessionLocal()
        user = db.query(User).filter(User.phone == username, User.role == UserRole.ADMIN).first()
        db.close()

        if user and verify_password(password, user.hashed_password):
            request.session.update({"token": user.phone})
            return True

        # Fallback to env admin (useful if no admin in DB)
        env_admin_user = os.getenv("ADMIN_USERNAME", "admin")
        env_admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")
        if username == env_admin_user and password == env_admin_pass:
            request.session.update({"token": "admin@baraka.uz"})
            return True

        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False
        return True


# --- Model Views ---

# ================= B2B MARKET VIEWS =================
class MaterialAdmin(ModelView, model=Material):
    column_list = [Material.id, Material.name, Material.price, Material.is_active]
    icon = "fa-solid fa-box"

class MaterialRequestAdmin(ModelView, model=MaterialRequest):
    column_list = [MaterialRequest.id, MaterialRequest.master_id, MaterialRequest.status, MaterialRequest.total_price]
    icon = "fa-solid fa-truck"

class MaterialRequestItemAdmin(ModelView, model=MaterialRequestItem):
    column_list = [MaterialRequestItem.id, MaterialRequestItem.request_id, MaterialRequestItem.material_id, MaterialRequestItem.quantity]
    icon = "fa-solid fa-list"

class DonationAdmin(ModelView, model=Donation):
    column_list = [Donation.id, Donation.user_id, Donation.amount, Donation.created_at]
    icon = "fa-solid fa-hand-holding-heart"

class SupplierProductAdmin(ModelView, model=SupplierProduct):
    column_list = [SupplierProduct.id, SupplierProduct.supplier_id, SupplierProduct.name, SupplierProduct.price, SupplierProduct.shop_address]
    icon = "fa-solid fa-store"

class SupplierReviewAdmin(ModelView, model=SupplierReview):
    column_list = [SupplierReview.id, SupplierReview.reviewer_id, SupplierReview.supplier_id, SupplierReview.rating]
    icon = "fa-solid fa-star-half-stroke"
# ====================================================

class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.full_name, User.phone, User.role, User.created_at]
    icon = "fa-solid fa-user"
    can_delete = True
    can_edit = True

class GuildAdmin(ModelView, model=Guild):
    column_list = [Guild.id, Guild.name, Guild.created_at]
    icon = "fa-solid fa-users"

class GuildMembershipAdmin(ModelView, model=GuildMembership):
    column_list = [GuildMembership.id, GuildMembership.user_id, GuildMembership.guild_id, GuildMembership.rank, GuildMembership.nufuz]
    icon = "fa-solid fa-id-badge"

class ApprenticeshipAdmin(ModelView, model=Apprenticeship):
    column_list = [Apprenticeship.id, Apprenticeship.master_id, Apprenticeship.apprentice_id, Apprenticeship.started_at]
    icon = "fa-solid fa-handshake"

class DuoAdmin(ModelView, model=Duo):
    column_list = [Duo.id, Duo.author_id, Duo.target_user_id, Duo.text, Duo.created_at]
    icon = "fa-solid fa-comment"

class OrderAdmin(ModelView, model=Order):
    column_list = [Order.id, Order.client_id, Order.master_id, Order.title, Order.status, Order.price]
    icon = "fa-solid fa-cart-shopping"

class GalleryItemAdmin(ModelView, model=GalleryItem):
    column_list = [GalleryItem.id, GalleryItem.user_id, GalleryItem.image_url, GalleryItem.created_at]
    icon = "fa-solid fa-image"

# Setup function to register everything
def setup_admin(admin):
    admin.add_view(UserAdmin)
    admin.add_view(GuildAdmin)
    admin.add_view(GuildMembershipAdmin)
    admin.add_view(ApprenticeshipAdmin)
    admin.add_view(DuoAdmin)
    admin.add_view(OrderAdmin)
    admin.add_view(GalleryItemAdmin)
    admin.add_view(MaterialAdmin)
    admin.add_view(MaterialRequestAdmin)
    admin.add_view(MaterialRequestItemAdmin)
    admin.add_view(DonationAdmin)
    admin.add_view(SupplierProductAdmin)
    admin.add_view(SupplierReviewAdmin)
