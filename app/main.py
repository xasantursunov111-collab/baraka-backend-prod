from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from fastapi.responses import HTMLResponse
from sqladmin import Admin
from app.admin import AdminAuth, setup_admin
from app.core.config import settings
from app.core.database import engine, Base
from app.api.routers import users, transactions, uploads, auth, ustoz_shogird, academy, chat, market, sadaqa, supplier, features

# --------- Barcha jadvallarni yaratish ---------
from app.models.user import User
from app.models.guild import Guild, GuildMembership, Apprenticeship, Duo
from app.models.transaction import Order
from app.models.gallery import GalleryItem
from app.models.academy import Course, Lesson
from app.models.chat import ChatMessage
from app.models.market import Material, MaterialRequest, MaterialRequestItem
from app.models.supplier import SupplierProduct, SupplierReview
from app.models.extras import Notification, Certificate, ScheduleSlot
from app.models.transaction import Order
from app.models.gallery import GalleryItem

Base.metadata.create_all(bind=engine)

# --------- FastAPI ilovasi ---------
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "BARAKA — Ustoz va Shogird munosabatlarini bog'lovchi, "
        "Rizolik va Hunarmandchilik qadriyatlariga asoslangan raqamli ekotizim API'si."
    ),
    version="1.0.0",
)

# --------- Admin Panel ---------
authentication_backend = AdminAuth(secret_key=os.getenv("SECRET_KEY", "my-super-secret-key-123!"))
admin = Admin(app, engine, authentication_backend=authentication_backend)
setup_admin(admin)

# --------- Routerlarni ulash ---------
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(transactions.router, prefix="/api/v1")
app.include_router(uploads.router, prefix="/api/v1")
app.include_router(ustoz_shogird.router, prefix="/api/v1")
app.include_router(academy.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(market.router, prefix="/api/v1")
app.include_router(sadaqa.router, prefix="/api/v1")
app.include_router(supplier.router, prefix="/api/v1")
app.include_router(features.router, prefix="/api/v1")

# --------- Statik fayllar ---------
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

if os.environ.get("VERCEL"):
    UPLOADS_DIR = Path("/tmp/uploads")
else:
    UPLOADS_DIR = BASE_DIR / "uploads"

UPLOADS_DIR.mkdir(exist_ok=True, parents=True)

app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


# --------- HTML sahifalarni qaytarish ---------
def _html(filename: str):
    file_path = FRONTEND_DIR / filename
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    return HTMLResponse(file_path.read_text(encoding="utf-8"), headers=headers)

@app.get("/", response_class=HTMLResponse, tags=["Sahifalar"])
def home_page():
    return _html("index.html")


@app.get("/masters", response_class=HTMLResponse, tags=["Sahifalar"])
def masters_page():
    return _html("masters.html")


@app.get("/profile", response_class=HTMLResponse, tags=["Sahifalar"])
def profile_page():
    return _html("profile.html")


@app.get("/orders", response_class=HTMLResponse, tags=["Sahifalar"])
def orders_page():
    return _html("orders.html")


@app.get("/login", response_class=HTMLResponse, tags=["Sahifalar"])
def login_page():
    return _html("login.html")


@app.get("/guilds", response_class=HTMLResponse, tags=["Sahifalar"])
def guilds_page():
    return _html("guilds.html")


@app.get("/shogird", response_class=HTMLResponse, tags=["Sahifalar"])
def shogird_page():
    return _html("shogird.html")


@app.get("/duolar", response_class=HTMLResponse, tags=["Sahifalar"])
def duolar_page():
    return _html("duolar.html")


@app.get("/academy", response_class=HTMLResponse, tags=["Sahifalar"])
def academy_page():
    return _html("academy.html")


@app.get("/market", response_class=HTMLResponse, tags=["Sahifalar"])
def market_page():
    return _html("market.html")


@app.get("/suppliers", response_class=HTMLResponse, tags=["Sahifalar"])
def suppliers_page():
    return _html("suppliers.html")


@app.get("/dashboard", response_class=HTMLResponse, tags=["Sahifalar"])
def dashboard_page():
    return _html("dashboard.html")
