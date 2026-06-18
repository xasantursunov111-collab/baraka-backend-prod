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
    name = "Material"
    name_plural = "Materiallar"
    column_list = [Material.id, Material.name, Material.price, Material.is_active]
    icon = "fa-solid fa-box"
    column_labels = {Material.name: "Nomi", Material.description: "Tavsif", Material.price: "Narxi", Material.image_url: "Rasm URL", Material.is_active: "Faolmi"}

class MaterialRequestAdmin(ModelView, model=MaterialRequest):
    name = "Material So'rovi"
    name_plural = "Material So'rovlari"
    column_list = [MaterialRequest.id, MaterialRequest.master_id, MaterialRequest.status, MaterialRequest.total_price]
    icon = "fa-solid fa-truck"

class MaterialRequestItemAdmin(ModelView, model=MaterialRequestItem):
    name = "So'rov Qismi"
    name_plural = "So'rov Qismlari"
    column_list = [MaterialRequestItem.id, MaterialRequestItem.request_id, MaterialRequestItem.material_id, MaterialRequestItem.quantity]
    icon = "fa-solid fa-list"

class DonationAdmin(ModelView, model=Donation):
    name = "Ehson (Sadaqa)"
    name_plural = "Ehsonlar"
    column_list = [Donation.id, Donation.user_id, Donation.amount, Donation.created_at]
    icon = "fa-solid fa-hand-holding-heart"

class SupplierProductAdmin(ModelView, model=SupplierProduct):
    name = "Do'kon Mahsuloti"
    name_plural = "Do'kon Mahsulotlari"
    column_list = [SupplierProduct.id, SupplierProduct.supplier_id, SupplierProduct.name, SupplierProduct.price, SupplierProduct.shop_address]
    icon = "fa-solid fa-store"

class SupplierReviewAdmin(ModelView, model=SupplierReview):
    name = "Do'kon Sharhi"
    name_plural = "Do'kon Sharhlari"
    column_list = [SupplierReview.id, SupplierReview.reviewer_id, SupplierReview.supplier_id, SupplierReview.rating]
    icon = "fa-solid fa-star-half-stroke"
# ====================================================

class UserAdmin(ModelView, model=User):
    name = "Foydalanuvchi"
    name_plural = "Foydalanuvchilar"
    column_list = [User.id, User.full_name, User.phone, User.role, User.created_at]
    icon = "fa-solid fa-user"
    can_delete = True
    can_edit = True
    
    # Ortiqcha maydonlarni yaratish/tahrirlash oynasidan olib tashlash
    form_excluded_columns = [
        User.orders_as_master,
        User.orders_as_client,
        User.apprentices,
        User.master_link,
        User.guild_membership,
        User.duolar,
        User.created_at
    ]
    
    column_labels = {
        User.full_name: "To'liq ism",
        User.phone: "Telefon raqami",
        User.hashed_password: "Parol (Hashed)",
        User.role: "Rol (Vazifa)",
        User.bio: "O'zi haqida (Bio)",
        User.avatar_url: "Rasm URL",
        User.lat: "Kenglik (Xaritada)",
        User.lng: "Uzunlik (Xaritada)",
        User.shop_address: "Do'kon manzili",
        User.baraka_count: "Baraka (Ball)",
        User.halol_rating: "Halol reyting",
        User.bagrikenglik_requests: "Bag'rikenglik",
        User.created_at: "Ro'yxatdan o'tgan sana"
    }

class GuildAdmin(ModelView, model=Guild):
    name = "Uyushma (Kasaba)"
    name_plural = "Uyushmalar"
    column_list = [Guild.id, Guild.name, Guild.created_at]
    icon = "fa-solid fa-users"

class GuildMembershipAdmin(ModelView, model=GuildMembership):
    name = "Uyushma A'zosi"
    name_plural = "Uyushma A'zolari"
    column_list = [GuildMembership.id, GuildMembership.user_id, GuildMembership.guild_id, GuildMembership.rank, GuildMembership.nufuz]
    icon = "fa-solid fa-id-badge"

class ApprenticeshipAdmin(ModelView, model=Apprenticeship):
    name = "Ustoz-Shogirdlik"
    name_plural = "Ustoz-Shogirdlik"
    column_list = [Apprenticeship.id, Apprenticeship.master_id, Apprenticeship.apprentice_id, Apprenticeship.started_at]
    icon = "fa-solid fa-handshake"

class DuoAdmin(ModelView, model=Duo):
    name = "Duo (Sharh)"
    name_plural = "Duolar"
    column_list = [Duo.id, Duo.author_id, Duo.target_user_id, Duo.text, Duo.created_at]
    icon = "fa-solid fa-comment"

class OrderAdmin(ModelView, model=Order):
    name = "Buyurtma"
    name_plural = "Buyurtmalar"
    column_list = [Order.id, Order.client_id, Order.master_id, Order.title, Order.status, Order.price]
    icon = "fa-solid fa-cart-shopping"

class GalleryItemAdmin(ModelView, model=GalleryItem):
    name = "Galereya Rasmi"
    name_plural = "Galereya"
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
